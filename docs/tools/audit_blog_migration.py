#!/usr/bin/env python3
"""Audit the static Healer Next Door migration before deployment."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from lxml import html


ORIGIN = "https://enlightenedpathhealing.com"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_DOCS = PROJECT_ROOT / "docs" / "migration"


def local_target(output_root: Path, href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or href.startswith(("mailto:", "tel:", "#")):
        return None
    path = unquote(parsed.path)
    if not path.startswith("/"):
        return None
    if path == "/":
        return output_root / "index.html"
    candidate = output_root / path.lstrip("/")
    if candidate.suffix:
        return candidate
    if (candidate / "index.html").exists():
        return candidate / "index.html"
    if candidate.with_suffix(".html").exists():
        return candidate.with_suffix(".html")
    return candidate / "index.html"


def audit(output_root: Path, report_path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    with report_path.open(newline="", encoding="utf-8-sig") as handle:
        report = list(csv.DictReader(handle))

    post_rows = [row for row in report if row["content_type"] == "post"]
    taxonomy_rows = [row for row in report if row["content_type"] in {"category", "tag"}]
    if len(post_rows) != 253:
        errors.append(f"Expected 253 post rows, found {len(post_rows)}")
    if len(taxonomy_rows) != 335:
        errors.append(f"Expected 335 taxonomy rows, found {len(taxonomy_rows)}")
    failed = [row for row in report if row["status"] == "failed"]
    if failed:
        errors.append(f"Migration report contains {len(failed)} failed rows")

    article_pages: list[Path] = []
    blog_root = output_root / "healernextdoor"
    for directory in blog_root.iterdir():
        if directory.is_dir() and directory.name not in {"category", "tag"}:
            page = directory / "index.html"
            if page.exists():
                article_pages.append(page)

    if len(article_pages) != 253:
        errors.append(f"Expected 253 article files, found {len(article_pages)}")

    broken_links: set[str] = set()
    remote_images: set[str] = set()
    for page in article_pages:
        markup = page.read_text(encoding="utf-8")
        document = html.fromstring(markup)
        slug = page.parent.name
        expected = f"{ORIGIN}/healernextdoor/{slug}"
        canonical = document.xpath('string(//link[@rel="canonical"]/@href)')
        if canonical != expected:
            errors.append(f"Canonical mismatch: {page} -> {canonical}")
        if "This page has been kept for continuity" in markup or "Preserved archive" in markup:
            errors.append(f"Placeholder remains: {page}")
        if not document.xpath('//script[@type="application/ld+json"]'):
            errors.append(f"Missing Article schema: {page}")
        body = document.xpath('//article[contains(@class,"legacy-article-body")]')
        if not body or len(re.sub(r"\s+", " ", body[0].text_content()).split()) < 20:
            errors.append(f"Missing or short article body: {page}")
        description = document.xpath('string(//meta[@name="description"]/@content)')
        if len(description.strip()) < 20:
            errors.append(f"Missing meta description: {page}")

        for image in document.xpath('//img[@src]'):
            src = image.get("src", "")
            if "squarespace" in src:
                remote_images.add(f"{page}: {src}")
            if src.startswith("../../assets/blog/"):
                target = (page.parent / src).resolve()
                if not target.exists():
                    errors.append(f"Missing image: {page} -> {src}")

        for link in document.xpath('//article[contains(@class,"legacy-article-body")]//a[@href]'):
            href = link.get("href", "")
            target = local_target(output_root, href)
            if target is not None and not target.exists():
                broken_links.add(f"{page}: {href}")

    if remote_images:
        warnings.append(f"Found {len(remote_images)} Squarespace-hosted article images")
    if broken_links:
        warnings.append(f"Found {len(broken_links)} internal article links without local targets")

    taxonomy_pages = list((blog_root / "category").rglob("index.html")) + list(
        (blog_root / "tag").rglob("index.html")
    )
    if len(taxonomy_pages) != 333:
        errors.append(f"Expected 333 physical taxonomy pages after case collisions, found {len(taxonomy_pages)}")
    for page in taxonomy_pages:
        markup = page.read_text(encoding="utf-8")
        if 'name="robots" content="noindex,follow"' not in markup:
            errors.append(f"Taxonomy page is indexable: {page}")
        if f'<link rel="canonical" href="{ORIGIN}/healernextdoor">' not in markup:
            errors.append(f"Taxonomy canonical mismatch: {page}")

    hub = blog_root / "index.html"
    if not hub.exists() or "Preserved archive" in hub.read_text(encoding="utf-8"):
        errors.append("The clean /healernextdoor hub is missing or still a placeholder")

    sitemap = (output_root / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_posts = set(re.findall(rf"{re.escape(ORIGIN)}/healernextdoor/[^<]+", sitemap))
    sitemap_posts = {url for url in sitemap_posts if "/category/" not in url and "/tag/" not in url}
    # The migration report records the legacy hostname; compare paths against
    # the current production hostname configured for this deployment.
    expected_posts = {
        row["source_url"].replace("https://www.enlightenedpathhealing.com", ORIGIN)
        for row in post_rows
    }
    missing_from_sitemap = expected_posts - sitemap_posts
    if missing_from_sitemap:
        errors.append(f"Sitemap is missing {len(missing_from_sitemap)} migrated posts")
    if re.search(r"/healernextdoor/(category|tag)/", sitemap):
        errors.append("Noindex taxonomy URLs remain in the sitemap")

    return {
        "passed": not errors,
        "article_pages": len(article_pages),
        "taxonomy_report_rows": len(taxonomy_rows),
        "taxonomy_physical_pages": len(taxonomy_pages),
        "remote_article_images": len(remote_images),
        "broken_internal_article_links": len(broken_links),
        "errors": errors,
        "warnings": warnings,
        "broken_link_samples": sorted(broken_links)[:25],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--migration-report", type=Path, default=MIGRATION_DOCS / "blog-migration-report.csv")
    parser.add_argument("--report", type=Path, default=MIGRATION_DOCS / "blog-migration-audit.json")
    args = parser.parse_args()
    result = audit(args.output_root, args.migration_report)
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
