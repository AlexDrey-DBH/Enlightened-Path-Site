from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


EXCLUDED_PARTS = {".git", "assets", "docs", "samples", "tmp"}
FORBIDDEN_PUBLIC_TOKENS = (
    "data-action-item",
    "image placeholder",
    "lorem ipsum",
    "before launch",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_count = 0
        self.title_text: list[str] = []
        self.in_title = False
        self.h1_count = 0
        self.meta_descriptions: list[str] = []
        self.canonicals: list[str] = []
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.sources: list[str] = []
        self.images_missing_alt = 0
        self.checked_checkboxes = 0
        self.cites: list[str] = []
        self.in_cite = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title":
            self.title_count += 1
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta" and values.get("name", "").lower() == "description":
            if values.get("content", "").strip():
                self.meta_descriptions.append(values.get("content", "").strip())
        elif tag == "link" and values.get("rel", "").lower() == "canonical":
            if values.get("href", "").strip():
                self.canonicals.append(values.get("href", "").strip())
        elif tag == "img" and "alt" not in values:
            self.images_missing_alt += 1
        elif tag == "input" and values.get("type", "").lower() == "checkbox" and "checked" in values:
            self.checked_checkboxes += 1
        elif tag == "cite":
            self.in_cite = True

        if values.get("id"):
            self.ids.append(values.get("id") or "")
        if values.get("href"):
            self.hrefs.append(values.get("href") or "")
        if values.get("src"):
            self.sources.append(values.get("src") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "cite":
            self.in_cite = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text.append(data)
        if self.in_cite and data.strip():
            self.cites.append(data.strip())


def html_pages(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.html")
        if not EXCLUDED_PARTS.intersection(path.relative_to(root).parts)
    )


def local_target(root: Path, page: Path, raw_url: str) -> tuple[Path | None, str]:
    if not raw_url or raw_url.startswith(("mailto:", "tel:", "data:", "javascript:")):
        return None, ""
    parts = urlsplit(raw_url)
    if parts.scheme or parts.netloc:
        return None, ""
    if not parts.path:
        return page, parts.fragment
    path = unquote(parts.path)
    if path.startswith("/"):
        return None, parts.fragment
    target = (page.parent / path).resolve()
    if target.is_dir():
        target = target / "index.html"
    return target, parts.fragment


def sitemap_urls(root: Path) -> set[str]:
    tree = ElementTree.parse(root / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return {
        (node.text or "").strip()
        for node in tree.findall(".//sm:loc", namespace)
        if (node.text or "").strip()
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    pages = html_pages(root)
    errors: list[str] = []
    parsed: dict[Path, PageParser] = {}

    for page in pages:
        relative = page.relative_to(root).as_posix()
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        parsed[page.resolve()] = parser

        title = "".join(parser.title_text).strip()
        if parser.title_count != 1 or not title:
            errors.append(f"{relative}: expected one non-empty title")
        if len(parser.meta_descriptions) != 1:
            errors.append(f"{relative}: expected one non-empty meta description")
        if len(parser.canonicals) != 1:
            errors.append(f"{relative}: expected one canonical URL")
        if parser.h1_count != 1:
            errors.append(f"{relative}: expected one h1, found {parser.h1_count}")
        duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
        if duplicates:
            errors.append(f"{relative}: duplicate ids {', '.join(duplicates)}")
        if parser.images_missing_alt:
            errors.append(f"{relative}: {parser.images_missing_alt} image(s) missing alt attributes")
        if parser.checked_checkboxes:
            errors.append(f"{relative}: checkbox checked by default")

        lowered = text.lower()
        for token in FORBIDDEN_PUBLIC_TOKENS:
            if token in lowered:
                errors.append(f"{relative}: public development token '{token}'")
        if re.search(r"\bReflections\b", text):
            errors.append(f"{relative}: old client-facing label 'Reflections'")

    for page, parser in parsed.items():
        relative = page.relative_to(root).as_posix()
        for raw_url in parser.hrefs + parser.sources:
            target, fragment = local_target(root, page, raw_url)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{relative}: missing local target {raw_url}")
                continue
            if fragment and target.suffix.lower() == ".html":
                target_parser = parsed.get(target.resolve())
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    parsed[target.resolve()] = target_parser
                if fragment not in target_parser.ids:
                    errors.append(f"{relative}: missing anchor target {raw_url}")

    listed_urls = sitemap_urls(root)
    for page, parser in parsed.items():
        relative = page.relative_to(root).as_posix()
        if len(parser.canonicals) == 1 and parser.canonicals[0] not in listed_urls:
            errors.append(f"{relative}: canonical missing from sitemap.xml ({parser.canonicals[0]})")

    home = parsed.get((root / "index.html").resolve())
    testimonials = parsed.get((root / "testimonials.html").resolve())
    if home and testimonials:
        repeated = sorted(set(home.cites).intersection(testimonials.cites))
        if repeated:
            errors.append(f"homepage testimonials repeat on testimonials page: {', '.join(repeated)}")

    print(f"Production pages checked: {len(pages)}")
    print(f"Internal references checked: {sum(len(page.hrefs) + len(page.sources) for page in parsed.values())}")
    print(f"Sitemap URLs checked: {len(listed_urls)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Errors: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
