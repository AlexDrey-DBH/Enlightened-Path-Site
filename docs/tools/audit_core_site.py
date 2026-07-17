from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from generate_local_sitemap import build_local_sitemap


CORE_PAGES = (
    "index.html",
    "about-lisa.html",
    "services.html",
    "reiki-energy-healing.html",
    "akashic-records.html",
    "meditation.html",
    "work-trauma-coaching.html",
    "corporate-wellness.html",
    "testimonials.html",
    "resources.html",
    "healernextdoor.html",
    "contact.html",
    "get-started/index.html",
    "newsletter/index.html",
    "events/index.html",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_count = 0
        self.in_title = False
        self.title_text: list[str] = []
        self.h1_count = 0
        self.meta_description = 0
        self.canonical = 0
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title":
            self.title_count += 1
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta" and values.get("name", "").lower() == "description":
            if values.get("content", "").strip():
                self.meta_description += 1
        elif tag == "link" and values.get("rel", "").lower() == "canonical":
            if values.get("href", "").strip():
                self.canonical += 1

        if values.get("id"):
            self.ids.append(values["id"] or "")
        if values.get("href"):
            self.hrefs.append(values["href"] or "")
        if values.get("src"):
            self.sources.append(values["src"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text.append(data)


def local_target(page: Path, raw_url: str) -> tuple[Path | None, str]:
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


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors: list[str] = []
    parsed: dict[Path, PageParser] = {}
    local_map = root / "tmp" / "site-map.html"

    try:
        sitemap_pages, action_items = build_local_sitemap(root, local_map)
    except Exception as exc:  # pragma: no cover - diagnostic output
        sitemap_pages, action_items = 0, 0
        errors.append(f"local sitemap generation failed: {exc}")

    for name in CORE_PAGES:
        page = root / name
        if not page.exists():
            errors.append(f"missing core page: {name}")
            continue
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        parsed[page.resolve()] = parser

        if parser.title_count != 1 or not "".join(parser.title_text).strip():
            errors.append(f"{name}: expected one non-empty title")
        if parser.meta_description != 1:
            errors.append(f"{name}: expected one meta description")
        if parser.canonical != 1:
            errors.append(f"{name}: expected one canonical link")
        if parser.h1_count != 1:
            errors.append(f"{name}: expected one h1, found {parser.h1_count}")
        duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if duplicates:
            errors.append(f"{name}: duplicate ids {', '.join(duplicates)}")
        lowered = text.lower()
        for forbidden in ("tender", "lorem ipsum", "[verify"):
            if forbidden in lowered:
                errors.append(f"{name}: forbidden placeholder/copy token '{forbidden}'")

    for page, parser in list(parsed.items()):
        for raw_url in parser.hrefs + parser.sources:
            target, fragment = local_target(page, raw_url)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{page.name}: missing local target {raw_url}")
                continue
            if fragment and target.suffix.lower() == ".html":
                target_parser = parsed.get(target.resolve())
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    parsed[target.resolve()] = target_parser
                if fragment not in target_parser.ids:
                    errors.append(f"{page.name}: missing anchor target {raw_url}")

    sitemap = root / "sitemap.xml"
    try:
        ElementTree.parse(sitemap)
    except Exception as exc:  # pragma: no cover - diagnostic output
        errors.append(f"sitemap.xml: invalid XML ({exc})")

    css = (root / "styles.css").read_text(encoding="utf-8")
    if css.count("{") != css.count("}"):
        errors.append("styles.css: unbalanced braces")

    print(f"Core pages checked: {len(CORE_PAGES)}")
    print(f"Local references checked: {sum(len(p.hrefs) + len(p.sources) for p in parsed.values())}")
    print(f"Local sitemap: {sitemap_pages} pages, {action_items} open actions")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Errors: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
