#!/usr/bin/env python3
"""Sync every blog-card preview to the first sentence of its article."""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
BLOG_ROOT = ROOT / "healernextdoor"
CARD_PATTERN = re.compile(
    r'<article\b(?=[^>]*\bclass=["\'][^"\']*\bblog-card\b[^"\']*["\'])[^>]*>.*?</article>',
    re.IGNORECASE | re.DOTALL,
)
HREF_PATTERN = re.compile(
    r'<h3\b[^>]*>.*?<a\b[^>]*\bhref=["\']([^"\']+)["\']',
    re.IGNORECASE | re.DOTALL,
)
EXCERPT_PATTERN = re.compile(
    r'(<p\s+class=["\']blog-card-meta["\'][^>]*>.*?</p>\s*)<p(?:\s[^>]*)?>.*?</p>',
    re.IGNORECASE | re.DOTALL,
)


def clean_text(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", value)).split())


def article_excerpt(article: Path) -> str:
    markup = article.read_text(encoding="utf-8")
    body_match = re.search(
        r'<article\s+class=["\'][^"\']*legacy-article-body[^"\']*["\'][^>]*>(.*?)</article>',
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not body_match:
        return ""
    for paragraph in re.findall(r'<p\b[^>]*>(.*?)</p>', body_match.group(1), flags=re.IGNORECASE | re.DOTALL):
        text = clean_text(paragraph)
        text = re.sub(r'^By\s+[A-Z][A-Za-z.\'-]+\s+[A-Z][A-Za-z.\'-]+\.?\s*', "", text)
        if not text:
            continue
        sentence = re.search(r'^(.+?[.!?]["\']?)(?=\s+[A-Z"\']|$)', text)
        return (sentence.group(1) if sentence else text).strip()
    return ""


def target_article(page: Path, href: str) -> Path | None:
    parts = urlsplit(html.unescape(href))
    if parts.scheme or parts.netloc or not parts.path:
        return None
    if parts.path.startswith("/"):
        target = ROOT / unquote(parts.path.lstrip("/"))
    else:
        target = page.parent / unquote(parts.path)
    if target.is_dir():
        target /= "index.html"
    target = target.resolve()
    try:
        target.relative_to(BLOG_ROOT.resolve())
    except ValueError:
        return None
    return target if target.name == "index.html" and target.is_file() else None


def sync_page(page: Path) -> int:
    markup = page.read_text(encoding="utf-8")
    updated_cards = 0

    def replace_card(match: re.Match[str]) -> str:
        nonlocal updated_cards
        card = match.group(0)
        href_match = HREF_PATTERN.search(card)
        if not href_match:
            return card
        article = target_article(page, href_match.group(1))
        if not article:
            return card
        excerpt = article_excerpt(article)
        if not excerpt or not EXCERPT_PATTERN.search(card):
            return card
        updated_cards += 1
        return EXCERPT_PATTERN.sub(
            lambda excerpt_match: excerpt_match.group(1) + f"<p>{html.escape(excerpt)}</p>",
            card,
            count=1,
        )

    updated = CARD_PATTERN.sub(replace_card, markup)
    if updated != markup:
        page.write_text(updated, encoding="utf-8", newline="\n")
    return updated_cards


def main() -> None:
    pages = [
        page for page in ROOT.rglob("*.html")
        if "tmp" not in page.relative_to(ROOT).parts and page.is_file()
    ]
    cards = sum(sync_page(page) for page in pages)
    print(f"Synchronized {cards} blog card excerpts across {len(pages)} HTML pages.")


if __name__ == "__main__":
    main()
