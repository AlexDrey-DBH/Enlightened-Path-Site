#!/usr/bin/env python3
"""Refresh the homepage's latest-blog cards from published article pages."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
ARTICLES = ROOT / "healernextdoor"
HOMEPAGE = ROOT / "index.html"
EXCLUDED_DIRECTORIES = {"category", "tag", "topic", "page"}
START_MARKER = "<!-- LATEST_BLOGS:START -->"
END_MARKER = "<!-- LATEST_BLOGS:END -->"


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    description: str
    excerpt: str
    author: str
    published: date
    topic: str
    image: str | None


def clean_text(value: object) -> str:
    text = re.sub(r"<br\s*/?>", " ", str(value or ""), flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(html.unescape(text).split())


def blog_post_from(value: object) -> dict | None:
    if isinstance(value, dict):
        kind = value.get("@type", "")
        kinds = kind if isinstance(kind, list) else [kind]
        if "BlogPosting" in kinds:
            return value
        for child in value.values():
            match = blog_post_from(child)
            if match:
                return match
    if isinstance(value, list):
        for child in value:
            match = blog_post_from(child)
            if match:
                return match
    return None


def structured_post(markup: str) -> dict | None:
    scripts = re.findall(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for script in scripts:
        try:
            match = blog_post_from(json.loads(script.strip()))
        except json.JSONDecodeError:
            continue
        if match:
            return match
    return None


def image_path(value: object) -> str | None:
    if isinstance(value, dict):
        value = value.get("url")
    if isinstance(value, list):
        value = value[0] if value else None
    if not isinstance(value, str) or not value.strip():
        return None
    parts = urlsplit(value)
    path = (parts.path if parts.scheme or parts.netloc else value).lstrip("/")
    return path if (ROOT / path).is_file() else None


def first_article_sentence(markup: str) -> str:
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


def read_post(page: Path) -> Post | None:
    markup = page.read_text(encoding="utf-8")
    data = structured_post(markup)
    if not data:
        return None
    try:
        published = date.fromisoformat(str(data.get("datePublished", ""))[:10])
    except ValueError:
        return None

    author = data.get("author", "Lisa Batitto")
    if isinstance(author, dict):
        author = author.get("name", "Lisa Batitto")
    topic_match = re.search(
        r'<div\s+class=["\']legacy-article-meta["\']>\s*<span>(.*?)</span>',
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return Post(
        slug=page.parent.name,
        title=clean_text(data.get("headline")),
        description=clean_text(data.get("description")),
        excerpt=first_article_sentence(markup) or clean_text(data.get("description")),
        author=clean_text(author) or "Lisa Batitto",
        published=published,
        topic=clean_text(topic_match.group(1)) if topic_match else "Blog",
        image=image_path(data.get("image")),
    )


def all_posts() -> list[Post]:
    posts = []
    for directory in ARTICLES.iterdir():
        if not directory.is_dir() or directory.name in EXCLUDED_DIRECTORIES:
            continue
        post = read_post(directory / "index.html") if (directory / "index.html").is_file() else None
        if post and post.title and post.description:
            posts.append(post)
    return sorted(posts, key=lambda post: (post.published, post.slug), reverse=True)


def render_card(post: Post) -> str:
    href = f"healernextdoor/{post.slug}/index.html"
    image = ""
    if post.image:
        image = (
            f'<a class="blog-card-image" href="{href}"><img src="{html.escape(post.image, quote=True)}" '
            f'alt="{html.escape(post.title, quote=True)}" loading="lazy"></a>'
        )
    return (
        f'<article class="blog-card">{image}<span class="chip">{html.escape(post.topic)}</span>'
        f'<h3><a href="{href}">{html.escape(post.title)}</a></h3>'
        f'<p class="blog-card-meta"><time datetime="{post.published.isoformat()}">'
        f'{post.published.strftime("%B").replace(" 0", " ")} {post.published.day}, {post.published.year}'
        f'</time> &middot; {html.escape(post.author)}</p>'
        f'<p>{html.escape(post.excerpt)}</p><a class="text-link" href="{href}">Read Blog</a></article>'
    )


def render_section(posts: list[Post]) -> str:
    cards = "\n          ".join(render_card(post) for post in posts[:3])
    return f'''{START_MARKER}
    <section class="section latest-blog-section" aria-labelledby="latest-blog-heading">
      <div class="container">
        <div class="section-head">
          <p class="eyebrow">Blog</p>
          <h2 id="latest-blog-heading">Latest from the Blog</h2>
          <p>Thoughtful reflections on healing, intuition, work, and being human.</p>
        </div>
        <div class="blog-grid">
          {cards}
        </div>
        <div class="cta-row"><a class="button secondary" href="healernextdoor.html">Read the Blog</a></div>
      </div>
    </section>
    {END_MARKER}'''


def main() -> None:
    posts = all_posts()
    if not posts:
        raise SystemExit("No published blog posts with BlogPosting metadata were found.")
    markup = HOMEPAGE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if pattern.search(markup):
        updated = pattern.sub(render_section(posts), markup, count=1)
    else:
        anchor = '    <section class="section soft">'
        if anchor not in markup:
            raise SystemExit("Could not find the homepage insertion point for the latest-blog section.")
        updated = markup.replace(anchor, render_section(posts) + "\n\n" + anchor, 1)
    HOMEPAGE.write_text(updated, encoding="utf-8", newline="\n")
    print(f"Updated homepage latest-blog section with {min(3, len(posts))} of {len(posts)} published posts.")


if __name__ == "__main__":
    main()
