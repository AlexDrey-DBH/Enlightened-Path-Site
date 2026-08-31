#!/usr/bin/env python3
"""Build publisher-managed blog posts and their discovery surfaces."""

from __future__ import annotations

import html
import json
import posixpath
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "publisher-content" / "posts.json"
BLOG_ROOT = ROOT / "healernextdoor"
SITEMAP = ROOT / "sitemap.xml"
SITE_URL = "https://enlightenedpathhealing.com"
EASTERN = ZoneInfo("America/New_York")
CARD_START = "<!-- MANAGED_BLOG_CARDS:START -->"
CARD_END = "<!-- MANAGED_BLOG_CARDS:END -->"
URL_START = "<!-- MANAGED_BLOG_URLS:START -->"
URL_END = "<!-- MANAGED_BLOG_URLS:END -->"

TOPICS = {
    "healing-spiritual-growth": "Healing & Spiritual Growth",
    "reiki-energy-healing": "Reiki & Energy Healing",
    "akashic-records-intuition": "Akashic Records & Intuition",
    "meditation-mindfulness": "Meditation & Mindfulness",
    "work-burnout-everyday-life": "Work, Burnout & Everyday Life",
    "astrology-guest-posts": "Astrology & Guest Posts",
}


def text(value: object) -> str:
    return " ".join(str(value or "").split())


def paragraphs(value: object) -> list[str]:
    normalized = str(value or "").replace("\r\n", "\n").strip()
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n+", normalized) if chunk.strip()]
    if len(chunks) == 1 and "\n" in normalized:
        chunks = [line.strip() for line in normalized.splitlines() if line.strip()]
    return chunks


def first_sentence(value: object) -> str:
    first = text(paragraphs(value)[0]) if paragraphs(value) else ""
    match = re.search(r'^(.+?[.!?]["\']?)(?=\s+[A-Z"\']|$)', first)
    return (match.group(1) if match else first).strip()


def description(value: object) -> str:
    sentence = first_sentence(value)
    if len(sentence) <= 158:
        return sentence
    return sentence[:155].rsplit(" ", 1)[0].rstrip(".,;:") + "..."


def parse_date(value: object) -> datetime:
    raw = str(value or "").replace("Z", "+00:00")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=EASTERN)
    return parsed.astimezone(EASTERN)


def load_posts() -> list[dict]:
    if not SOURCE.is_file():
        return []
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    posts = []
    for item in document.get("posts", []):
        if item.get("status") != "published":
            continue
        required = ("slug", "title", "body", "topic", "publishAt", "imagePath", "imageAlt")
        if not all(text(item.get(field)) for field in required):
            raise SystemExit(f"Managed post is missing required fields: {item!r}")
        if item["topic"] not in TOPICS:
            raise SystemExit(f"Managed post has an unknown topic: {item['topic']}")
        if not (ROOT / item["imagePath"]).is_file():
            raise SystemExit(f"Managed post image is missing: {item['imagePath']}")
        item = dict(item)
        item["date"] = parse_date(item["publishAt"])
        posts.append(item)
    return sorted(posts, key=lambda post: (post["date"], post["slug"]), reverse=True)


def article_markup(post: dict) -> str:
    title = html.escape(text(post["title"]))
    desc = html.escape(description(post["body"]), quote=True)
    slug = post["slug"]
    canonical = f"{SITE_URL}/healernextdoor/{slug}"
    image_url = f"{SITE_URL}/{post['imagePath']}"
    topic = html.escape(TOPICS[post["topic"]])
    published = post["date"]
    display_date = f"{published.strftime('%B')} {published.day}, {published.year}"
    body = "".join(f"<p>{html.escape(chunk)}</p>" for chunk in paragraphs(post["body"]))
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": text(post["title"]),
        "description": description(post["body"]),
        "url": canonical,
        "mainEntityOfPage": canonical,
        "author": {"@type": "Person", "name": "Lisa Batitto"},
        "publisher": {
            "@type": "Organization",
            "name": "Enlightened Path Healing",
            "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/assets/favicon-mark.png"},
        },
        "image": image_url,
        "datePublished": published.isoformat(),
        "dateModified": str(post.get("publishedAt") or post["publishAt"]),
    }
    schema_json = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
    image_alt = html.escape(text(post["imageAlt"]), quote=True)
    return f'''<!doctype html>
<!-- MANAGED_BLOG_POST -->
<html lang="en">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-6Q1QS7YNRZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-6Q1QS7YNRZ');</script>
  <!-- HubSpot tracking code -->
  <script type="text/javascript" id="hs-script-loader" async defer src="https://js-na2.hs-scripts.com/246755669.js"></script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Enlightened Path Healing</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(text(post['title']), quote=True)}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{image_url}">
  <link rel="stylesheet" href="../../styles.css">
  <script type="application/ld+json">{schema_json}</script>
  <link rel="icon" type="image/png" sizes="512x512" href="/assets/favicon-mark.png">
  <link rel="apple-touch-icon" href="/assets/favicon-mark.png">
  <link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#6f5665">
</head>
<body class="legacy-seo-page legacy-article-page">
  <header class="site-header"><nav class="nav" aria-label="Primary navigation"><a href="../../index.html"><img class="logo" src="../../assets/enlightened-path-healing-logo.png" alt="Enlightened Path Healing"></a><button class="nav-toggle" type="button" aria-label="Open navigation menu" aria-expanded="false"><span></span><span></span><span></span></button><div class="nav-links"><a href="../../index.html">Home</a><a href="../../about-lisa.html">About Lisa</a><a href="../../services.html">Services</a><a href="../../testimonials.html">Testimonials</a><a href="../../resources.html">Resources</a><a href="../../contact.html">Contact</a><a class="button" href="../../get-started/index.html">Schedule a Session</a></div></nav></header>
  <main>
    <section class="legacy-article-hero"><div class="container legacy-article-hero-inner"><div class="legacy-article-heading"><a class="eyebrow" href="../../healernextdoor.html">Back to the Blog</a><h1>{title}</h1><div class="legacy-article-meta"><span>{topic}</span><time datetime="{published.date().isoformat()}">{display_date}</time><span>By Lisa Batitto</span></div></div><figure class="legacy-article-hero-media"><img src="../../{html.escape(post['imagePath'], quote=True)}" alt="{image_alt}" fetchpriority="high"></figure></div></section>
    <section class="page-section legacy-article-section"><div class="container legacy-article-layout"><article class="legacy-article-body">{body}</article><aside class="legacy-article-aside"><p class="eyebrow">Explore</p><h2>Want a grounded place to begin?</h2><p>Explore services designed to make room for reflection, questions, and your next step.</p><a class="button" href="../../services.html">Explore Services</a></aside></div></section>
  </main>
  <footer class="site-footer"><div class="container footer-sitemap-grid"><div class="footer-brand"><img class="logo" src="../../assets/enlightened-path-healing-logo.png" alt="Enlightened Path Healing"><p>Montclair, NJ and online</p><div class="social-buttons footer-social" aria-label="Social links"><a class="social-button" href="https://www.instagram.com/enlightenedpathhealing/" target="_blank" rel="noopener"><img src="../../assets/icons/social/instagram.svg" alt="">Instagram</a><a class="social-button" href="https://www.tiktok.com/@enlightenedpathhealing" target="_blank" rel="noopener"><img src="../../assets/icons/social/tiktok.svg" alt="">TikTok</a><a class="social-button" href="https://www.youtube.com/channel/UC6KWXhYQzhJz953m7GaRYKA" target="_blank" rel="noopener"><img src="../../assets/icons/social/youtube.svg" alt="">YouTube</a></div></div><nav class="footer-group" aria-label="Practice links"><h2>Practice</h2><a href="../../index.html">Home</a><a href="../../about-lisa.html">About Lisa</a><a href="../../services.html">Services</a><a href="../../testimonials.html">Testimonials</a><a href="../../contact.html">Contact</a></nav><nav class="footer-group" aria-label="Service links"><h2>Services</h2><a href="../../reiki-energy-healing.html">Reiki and Energy Healing</a><a href="../../akashic-records.html">Akashic Records</a><a href="../../meditation.html">Meditation</a><a href="../../work-trauma-coaching.html">Work Trauma Coaching</a><a href="../../corporate-wellness.html">Corporate Wellness</a></nav><nav class="footer-group" aria-label="Learning links"><h2>Learn</h2><a href="../../resources.html">Resources</a><a href="../../healernextdoor.html">Blog</a><a href="../../faq/index.html">FAQ</a><a href="../../events/index.html">Events</a><a href="../../newsletter/index.html">Newsletter</a></nav></div></footer>
  <script src="../../site.js"></script>
</body>
</html>
'''


def relative_path(page: Path, target: str) -> str:
    page_dir = page.relative_to(ROOT).parent.as_posix() or "."
    return posixpath.relpath(target, page_dir)


def card_markup(post: dict, page: Path) -> str:
    article = f"healernextdoor/{post['slug']}/index.html"
    href = relative_path(page, article)
    image = relative_path(page, post["imagePath"])
    published = post["date"]
    display_date = f"{published.strftime('%B')} {published.day}, {published.year}"
    return (
        f'<article class="blog-card"><a class="blog-card-image" href="{html.escape(href, quote=True)}">'
        f'<img src="{html.escape(image, quote=True)}" alt="{html.escape(text(post["imageAlt"]), quote=True)}" loading="lazy"></a>'
        f'<span class="chip">{html.escape(TOPICS[post["topic"]])}</span>'
        f'<h3><a href="{html.escape(href, quote=True)}">{html.escape(text(post["title"]))}</a></h3>'
        f'<p class="blog-card-meta"><time datetime="{published.date().isoformat()}">{display_date}</time> &middot; Lisa Batitto</p>'
        f'<p>{html.escape(first_sentence(post["body"]))}</p><a class="text-link" href="{html.escape(href, quote=True)}">Read Blog</a></article>'
    )


def update_card_region(page: Path, posts: list[dict]) -> None:
    markup = page.read_text(encoding="utf-8")
    cards = "".join(card_markup(post, page) for post in posts)
    region = f"{CARD_START}{cards}{CARD_END}"
    pattern = re.compile(re.escape(CARD_START) + r".*?" + re.escape(CARD_END), re.DOTALL)
    if pattern.search(markup):
        updated = pattern.sub(region, markup, count=1)
    else:
        anchor = '<div class="blog-grid">'
        if anchor not in markup:
            raise SystemExit(f"Could not find blog grid in {page.relative_to(ROOT)}")
        updated = markup.replace(anchor, anchor + region, 1)
    page.write_text(updated, encoding="utf-8", newline="\n")


def update_sitemap(posts: list[dict]) -> None:
    markup = SITEMAP.read_text(encoding="utf-8")
    entries = "".join(
        f'<url><loc>{SITE_URL}/healernextdoor/{html.escape(post["slug"])}</loc><lastmod>{post["date"].date().isoformat()}</lastmod></url>'
        for post in posts
    )
    region = f"{URL_START}{entries}{URL_END}"
    pattern = re.compile(re.escape(URL_START) + r".*?" + re.escape(URL_END), re.DOTALL)
    if pattern.search(markup):
        updated = pattern.sub(region, markup, count=1)
    else:
        updated = markup.replace("</urlset>", region + "</urlset>", 1)
    SITEMAP.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    posts = load_posts()
    for post in posts:
        destination = BLOG_ROOT / post["slug"] / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(article_markup(post), encoding="utf-8", newline="\n")

    update_card_region(ROOT / "healernextdoor.html", posts)
    update_card_region(BLOG_ROOT / "index.html", posts)
    for topic_slug in TOPICS:
        topic_posts = [post for post in posts if post["topic"] == topic_slug]
        update_card_region(BLOG_ROOT / "topic" / topic_slug / "index.html", topic_posts)
    update_sitemap(posts)
    print(f"Built {len(posts)} publisher-managed blog post(s) and refreshed all discovery surfaces.")


if __name__ == "__main__":
    main()
