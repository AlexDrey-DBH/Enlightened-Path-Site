#!/usr/bin/env python3
"""Migrate live Squarespace blog posts into the static site archive."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import html as html_module
import json
import mimetypes
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, unquote_plus, urljoin, urlparse
from urllib.request import Request, urlopen

from lxml import etree, html


USER_AGENT = "Mozilla/5.0 (compatible; EnlightenedPathHealingMigration/1.0)"
LIVE_ORIGIN = "https://www.enlightenedpathhealing.com"
BLOG_PREFIX = "/healernextdoor/"


@dataclass
class Article:
    source_url: str
    canonical_url: str
    title: str
    description: str
    author: str
    published: str
    modified: str
    image_url: str
    categories: list[str]
    tags: list[str]
    body_html: str
    body_words: int


@dataclass
class MigrationResult:
    source_url: str
    destination: str
    content_type: str
    status: str
    title: str = ""
    body_words: int = 0
    published: str = ""
    modified: str = ""
    image_count: int = 0
    source_sha256: str = ""
    output_sha256: str = ""
    note: str = ""


def fetch(url: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def first(document: html.HtmlElement, expressions: Iterable[str]) -> html.HtmlElement | None:
    for expression in expressions:
        matches = document.xpath(expression)
        if matches:
            candidate = matches[0]
            if isinstance(candidate, html.HtmlElement):
                return candidate
    return None


def meta(document: html.HtmlElement, *, name: str | None = None, prop: str | None = None,
         itemprop: str | None = None) -> str:
    if name:
        values = document.xpath(f'//meta[@name="{name}"]/@content')
    elif prop:
        values = document.xpath(f'//meta[@property="{prop}"]/@content')
    elif itemprop:
        values = document.xpath(f'//meta[@itemprop="{itemprop}"]/@content')
    else:
        values = []
    return values[0].strip() if values else ""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html_module.unescape(value or "")).strip()


def text_content(node: html.HtmlElement | None) -> str:
    return clean_text(node.text_content()) if node is not None else ""


def discover_body(document: html.HtmlElement) -> html.HtmlElement | None:
    return first(
        document,
        (
            '//*[@itemprop="articleBody"]',
            '//*[contains(concat(" ", normalize-space(@class), " "), " blog-item-content ")]'
            '//*[contains(concat(" ", normalize-space(@class), " "), " sqs-layout ")]',
            '//article[contains(concat(" ", normalize-space(@class), " "), " blog-item ")]'
            '//*[contains(concat(" ", normalize-space(@class), " "), " entry-content ")]',
            '//article[contains(concat(" ", normalize-space(@class), " "), " blog-item ")]'
            '//*[contains(concat(" ", normalize-space(@class), " "), " sqs-layout ")]',
            '//article[@itemtype="http://schema.org/BlogPosting"]',
        ),
    )


def class_text(document: html.HtmlElement, class_name: str) -> list[str]:
    nodes = document.xpath(
        f'//*[contains(concat(" ", normalize-space(@class), " "), " {class_name} ")]'
    )
    return [text_content(node) for node in nodes if text_content(node)]


def description_for(document: html.HtmlElement, body: html.HtmlElement) -> str:
    description = meta(document, prop="og:description") or meta(document, name="description")
    if not description:
        description = " ".join(text_content(body).split()[:38])
    description = clean_text(description)
    if len(description) <= 160:
        return description
    shortened = description[:157].rsplit(" ", 1)[0]
    return f"{shortened}..."


def article_from_document(url: str, raw: bytes) -> Article:
    document = html.fromstring(raw)
    body = discover_body(document)
    if body is None:
        raise ValueError("Article body container not found")

    title = meta(document, itemprop="headline") or clean_text(document.xpath("string(//h1)"))
    if not title:
        raise ValueError("Article title not found")

    canonical = document.xpath('//link[@rel="canonical"]/@href')
    canonical_url = canonical[0].strip() if canonical else url
    author = meta(document, itemprop="author") or "Lisa Batitto"
    published = meta(document, itemprop="datePublished")
    modified = meta(document, itemprop="dateModified") or published
    image_url = meta(document, prop="og:image") or meta(document, itemprop="image")
    categories = class_text(document, "blog-item-category")
    tags = class_text(document, "blog-item-tag")

    body_copy = copy.deepcopy(body)
    has_embedded_media = bool(body_copy.xpath('.//*[@data-html]|.//iframe|.//video|.//audio'))
    for node in body_copy.xpath('.//style|.//script|.//noscript|.//form|.//button'):
        node.drop_tree()
    words = len(text_content(body_copy).split())
    minimum_words = 20 if has_embedded_media else 40
    if words < minimum_words:
        raise ValueError(f"Article body is unexpectedly short ({words} words)")

    return Article(
        source_url=url,
        canonical_url=canonical_url,
        title=title,
        description=description_for(document, body_copy),
        author=author,
        published=published,
        modified=modified,
        image_url=image_url,
        categories=categories,
        tags=tags,
        body_html=etree.tostring(body_copy, encoding="unicode", method="html"),
        body_words=words,
    )


def normalize_asset_url(value: str, base_url: str) -> str:
    value = (value or "").strip()
    if value.startswith("//"):
        return f"https:{value}"
    return urljoin(base_url, value)


def extension_for(content_type: str, url: str) -> str:
    content_type = content_type.split(";", 1)[0].strip().lower()
    overrides = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
    if content_type in overrides:
        return overrides[content_type]
    extension = Path(urlparse(url).path).suffix.lower()
    if extension in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if extension == ".jpeg" else extension
    return mimetypes.guess_extension(content_type) or ".jpg"


def download_asset(url: str, destination_stem: Path) -> Path:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "image/jpeg")
    if len(data) > 20_000_000:
        raise ValueError(f"Asset is too large ({len(data)} bytes)")
    destination = destination_stem.with_suffix(extension_for(content_type, url))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def rewrite_internal_link(href: str, source_url: str) -> str:
    decoded = unquote(href).strip()
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", decoded, re.IGNORECASE)
    if email_match and not decoded.lower().startswith("mailto:"):
        return f"mailto:{email_match.group(0)}"
    absolute = urljoin(source_url, href)
    parsed = urlparse(absolute)
    if parsed.netloc in {"www.enlightenedpathhealing.com", "enlightenedpathhealing.com"}:
        path = parsed.path or "/"
        if path == "/home":
            path = "/"
        elif path == "/about":
            path = "/about-lisa.html"
        elif path == "/get-started":
            path = "/contact.html"
        elif path == "/love":
            path = "/success-stories.html"
        return path + (f"?{parsed.query}" if parsed.query else "") + (f"#{parsed.fragment}" if parsed.fragment else "")
    return absolute if parsed.scheme else href


def prepare_body(
    article: Article,
    output_root: Path,
    slug: str,
    download_assets: bool,
) -> tuple[str, str, int, list[str]]:
    fragment = html.fragment_fromstring(article.body_html, create_parent="div")
    warnings: list[str] = []
    image_count = 0
    assets_dir = output_root / "assets" / "blog" / slug
    asset_cache: dict[str, str] = {}

    for node in fragment.xpath('.//style|.//script|.//noscript|.//form|.//button'):
        node.drop_tree()

    for wrapper in fragment.xpath('.//*[@data-html]'):
        encoded = wrapper.get("data-html", "")
        try:
            embedded = html.fragment_fromstring(html_module.unescape(encoded))
        except (etree.ParserError, ValueError):
            continue
        if embedded.tag != "iframe":
            frames = embedded.xpath('.//iframe')
            if not frames:
                continue
            embedded = frames[0]
        source = normalize_asset_url(embedded.get("src", ""), article.source_url)
        if "cdn.embedly.com" in source:
            embedded_source = parse_qs(urlparse(source).query).get("src", [""])[0]
            if embedded_source:
                source = embedded_source
        if source.startswith("http://"):
            source = f"https://{source.removeprefix('http://')}"
        embedded.set("src", source)
        embedded.set("title", embedded.get("title") or f"Video for {article.title}")
        embedded.set("loading", "lazy")
        embedded.set("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture")
        embedded.set("allowfullscreen", "")
        wrapper.clear()
        wrapper.append(embedded)
        if "youtube.com/embed/" in source:
            video_id = urlparse(source).path.rstrip("/").rsplit("/", 1)[-1]
            fallback = etree.Element("p", {"class": "legacy-video-fallback"})
            fallback_link = etree.SubElement(
                fallback,
                "a",
                {
                    "href": f"https://www.youtube.com/watch?v={video_id}",
                    "target": "_blank",
                    "rel": "noopener",
                },
            )
            fallback_link.text = "Watch this video on YouTube"
            wrapper.append(fallback)

    for link in fragment.xpath('.//a[@href]'):
        link.set("href", rewrite_internal_link(link.get("href", ""), article.source_url))
        parsed = urlparse(link.get("href", ""))
        if parsed.scheme in {"http", "https"} and parsed.netloc not in {
            "www.enlightenedpathhealing.com",
            "enlightenedpathhealing.com",
        }:
            link.set("target", "_blank")
            link.set("rel", "noopener")

    for source in fragment.xpath('.//source'):
        source.drop_tree()

    for image in fragment.xpath('.//img'):
        source_url = image.get("data-src") or image.get("src") or ""
        source_url = normalize_asset_url(source_url, article.source_url)
        if not source_url or source_url.startswith("data:"):
            continue
        image_count += 1
        local_src = source_url
        if download_assets:
            if source_url in asset_cache:
                local_src = asset_cache[source_url]
            else:
                try:
                    destination = download_asset(source_url, assets_dir / f"image-{image_count:02d}")
                    local_src = f"../../assets/blog/{slug}/{destination.name}"
                    asset_cache[source_url] = local_src
                except Exception as error:  # Keep the live asset as a visual fallback.
                    warnings.append(f"inline image {image_count}: {error}")
        image.set("src", local_src)
        image.set("loading", "lazy")
        image.set("decoding", "async")
        image.attrib.pop("srcset", None)
        image.attrib.pop("data-src", None)
        image.attrib.pop("data-srcset", None)
        if not image.get("alt"):
            image.set("alt", "")

    for node in reversed(fragment.xpath('.//div|.//section')):
        has_media = bool(node.xpath('.//img|.//iframe|.//video|.//audio'))
        if not text_content(node) and not has_media:
            node.drop_tree()

    hero_src = article.image_url
    if hero_src and download_assets:
        normalized_hero = normalize_asset_url(hero_src, article.source_url)
        try:
            if normalized_hero in asset_cache:
                hero_src = asset_cache[normalized_hero]
            else:
                destination = download_asset(normalized_hero, assets_dir / "hero")
                hero_src = f"../../assets/blog/{slug}/{destination.name}"
        except Exception as error:
            warnings.append(f"hero image: {error}")

    for node in fragment.iterdescendants():
        for attribute in list(node.attrib):
            if attribute == "style" or attribute.startswith("data-") or attribute in {"id", "contenteditable"}:
                node.attrib.pop(attribute, None)

    body_html = "".join(
        etree.tostring(child, encoding="unicode", method="html") for child in fragment
    )
    return body_html, hero_src, image_count, warnings


def display_date(value: str) -> str:
    if not value:
        return ""
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not match:
        return value
    year, month, day = (int(part) for part in match.groups())
    return date(year, month, day).strftime("%B %d, %Y").replace(" 0", " ")


def render_article(article: Article, body_html: str, hero_src: str, slug: str) -> str:
    title = html_module.escape(article.title)
    description = html_module.escape(article.description, quote=True)
    canonical = html_module.escape(article.canonical_url, quote=True)
    author = html_module.escape(article.author)
    published_label = display_date(article.published)
    category = html_module.escape(article.categories[0]) if article.categories else "Reflection"
    image_absolute = ""
    if hero_src:
        if hero_src.startswith("../../"):
            image_absolute = f"{LIVE_ORIGIN}/{hero_src.removeprefix('../../')}"
        else:
            image_absolute = hero_src

    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article.title,
        "description": article.description,
        "url": article.canonical_url,
        "mainEntityOfPage": article.canonical_url,
        "author": {"@type": "Person", "name": article.author},
        "publisher": {"@type": "Organization", "name": "Enlightened Path Healing"},
    }
    if article.published:
        schema["datePublished"] = article.published
    if article.modified:
        schema["dateModified"] = article.modified
    if image_absolute:
        schema["image"] = image_absolute

    image_meta = ""
    hero_markup = ""
    if image_absolute:
        escaped_image = html_module.escape(image_absolute, quote=True)
        image_meta = f'\n  <meta property="og:image" content="{escaped_image}">'
    if hero_src:
        escaped_src = html_module.escape(hero_src, quote=True)
        hero_markup = (
            f'<figure class="legacy-article-hero-media"><img src="{escaped_src}" alt="{title}" '
            'fetchpriority="high"></figure>'
        )

    time_markup = ""
    if published_label:
        time_markup = (
            f'<time datetime="{html_module.escape(article.published, quote=True)}">'
            f'{html_module.escape(published_label)}</time>'
        )

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Enlightened Path Healing</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">{image_meta}
  <link rel="stylesheet" href="../../styles.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=True)}</script>
</head>
<body class="legacy-seo-page legacy-article-page">
  <header class="site-header"><nav class="nav" aria-label="Primary navigation"><a href="../../index.html"><img class="logo" src="../../assets/enlightened-path-healing-logo.png" alt="Enlightened Path Healing"></a><button class="nav-toggle" type="button" aria-label="Open navigation menu" aria-expanded="false"><span></span><span></span><span></span></button><div class="nav-links"><a href="../../index.html">Home</a><a href="../../about-lisa.html">About Lisa</a><a href="../../services.html">Services</a><a href="../../success-stories.html">Reflections</a><a href="../../healernextdoor.html">Resources</a><a href="../../contact.html">Contact</a><a class="button" href="../../contact.html">Book a Discovery Call</a></div></nav></header>
  <main>
    <section class="legacy-article-hero"><div class="container legacy-article-hero-inner"><div class="legacy-article-heading"><a class="eyebrow" href="../../healernextdoor.html">Healer Next Door</a><h1>{title}</h1><p>{description}</p><div class="legacy-article-meta"><span>{category}</span>{time_markup}<span>By {author}</span></div></div>{hero_markup}</div></section>
    <section class="page-section legacy-article-section"><div class="container legacy-article-layout"><article class="legacy-article-body">{body_html}</article><aside class="legacy-article-aside"><p class="eyebrow">Grounded spiritual support</p><h2>Curious about what this could mean for you?</h2><p>Explore Reiki, Akashic Records, mindfulness, and supportive coaching with Lisa Batitto in Montclair, NJ and online.</p><a class="button" href="../../services.html">Explore Services</a><a class="text-link" href="../../contact.html">Start with a discovery call</a></aside></div></section>
    <section class="final-cta"><div class="container"><p class="eyebrow">A place to begin</p><h2>You do not have to have it all figured out.</h2><p>Bring your questions, your skepticism, or simply the sense that something needs to change.</p><div class="cta-row"><a class="button" href="../../contact.html">Book a Discovery Call</a><a class="button secondary" href="../../healernextdoor.html">More Reflections</a></div></div></section>
  </main>
  <script src="../../site.js"></script>
</body>
</html>
'''


def render_taxonomy(source_url: str, label: str, kind: str) -> str:
    escaped_label = html_module.escape(label)
    canonical = f"{LIVE_ORIGIN}/healernextdoor"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_label} {kind.title()} Archive | Enlightened Path Healing</title>
  <meta name="description" content="Browse current Healer Next Door reflections on Reiki, mindfulness, intuitive guidance, work stress, and life transitions.">
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="../../../styles.css">
</head>
<body class="legacy-seo-page">
  <header class="site-header"><nav class="nav" aria-label="Primary navigation"><a href="../../../index.html"><img class="logo" src="../../../assets/enlightened-path-healing-logo.png" alt="Enlightened Path Healing"></a><button class="nav-toggle" type="button" aria-label="Open navigation menu" aria-expanded="false"><span></span><span></span><span></span></button><div class="nav-links"><a href="../../../index.html">Home</a><a href="../../../about-lisa.html">About Lisa</a><a href="../../../services.html">Services</a><a href="../../../success-stories.html">Reflections</a><a href="../../../healernextdoor.html">Resources</a><a href="../../../contact.html">Contact</a><a class="button" href="../../../contact.html">Book a Discovery Call</a></div></nav></header>
  <main>
    <section class="page-hero legacy-hero"><div class="container"><p class="eyebrow">Healer Next Door archive</p><h1>{escaped_label}</h1><p>This older {kind} label has been consolidated so the most useful reflections are easier to find.</p><div class="hero-actions"><a class="button" href="../../../healernextdoor.html">Browse Current Topics</a><a class="button secondary" href="../../../services.html">Explore Services</a></div></div></section>
  </main>
  <script src="../../../site.js"></script>
</body>
</html>
'''


def destination_for(output_root: Path, source_url: str) -> Path:
    relative = urlparse(source_url).path.strip("/")
    return output_root / relative / "index.html"


def is_post_url(source_url: str) -> bool:
    path = urlparse(source_url).path
    return path.startswith(BLOG_PREFIX) and "/category/" not in path and "/tag/" not in path


def taxonomy_kind(source_url: str) -> str | None:
    path = urlparse(source_url).path
    if "/category/" in path:
        return "category"
    if "/tag/" in path:
        return "tag"
    return None


def taxonomy_label(source_url: str) -> str:
    value = unquote_plus(urlparse(source_url).path.rstrip("/").rsplit("/", 1)[-1])
    return re.sub(r"\s+", " ", value.replace("-", " ")).strip().title()


def write_report(results: list[MigrationResult], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(MigrationResult.__dataclass_fields__)
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def upsert_report(result: MigrationResult, report_path: Path) -> None:
    fields = list(MigrationResult.__dataclass_fields__)
    rows: list[dict[str, str | int]] = []
    if report_path.exists():
        with report_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    replacement = asdict(result)
    updated = False
    for index, row in enumerate(rows):
        if row.get("source_url") == result.source_url:
            rows[index] = replacement
            updated = True
            break
    if not updated:
        rows.append(replacement)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(articles: list[Article], manifest_path: Path) -> None:
    manifest_path.write_text(
        json.dumps([asdict(article) for article in articles], indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def upsert_manifest(article: Article, manifest_path: Path) -> None:
    records: list[dict] = []
    if manifest_path.exists():
        records = json.loads(manifest_path.read_text(encoding="utf-8"))
    replacement = asdict(article)
    for index, record in enumerate(records):
        if record.get("source_url") == article.source_url:
            records[index] = replacement
            break
    else:
        records.append(replacement)
    manifest_path.write_text(json.dumps(records, indent=2, ensure_ascii=True), encoding="utf-8")


def migrate_post(
    source_url: str,
    output_root: Path,
    download_assets: bool,
    force: bool,
) -> tuple[MigrationResult, Article | None]:
    destination = destination_for(output_root, source_url)
    relative_destination = destination.relative_to(output_root).as_posix()
    if destination.exists() and not force:
        existing = destination.read_text(encoding="utf-8", errors="replace")
        if "This page has been kept for continuity" not in existing and "Preserved archive" not in existing:
            return (
                MigrationResult(
                    source_url=source_url,
                    destination=relative_destination,
                    content_type="post",
                    status="skipped-existing",
                    output_sha256=hashlib.sha256(existing.encode("utf-8")).hexdigest(),
                    note="Existing non-placeholder page preserved; use --force to replace.",
                ),
                None,
            )

    raw = fetch(source_url)
    source_hash = hashlib.sha256(raw).hexdigest()
    article = article_from_document(source_url, raw)
    slug = urlparse(source_url).path.rstrip("/").rsplit("/", 1)[-1]
    body_html, hero_src, image_count, warnings = prepare_body(
        article, output_root, slug, download_assets
    )
    rendered = render_article(article, body_html, hero_src, slug)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8", newline="\n")
    return (
        MigrationResult(
            source_url=source_url,
            destination=relative_destination,
            content_type="post",
            status="migrated" if not warnings else "migrated-with-warnings",
            title=article.title,
            body_words=article.body_words,
            published=article.published,
            modified=article.modified,
            image_count=image_count + (1 if hero_src else 0),
            source_sha256=source_hash,
            output_sha256=hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
            note="; ".join(warnings),
        ),
        article,
    )


def migrate_taxonomy(source_url: str, output_root: Path) -> MigrationResult:
    kind = taxonomy_kind(source_url)
    if not kind:
        raise ValueError("Not a taxonomy URL")
    destination = destination_for(output_root, source_url)
    rendered = render_taxonomy(source_url, taxonomy_label(source_url), kind)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8", newline="\n")
    return MigrationResult(
        source_url=source_url,
        destination=destination.relative_to(output_root).as_posix(),
        content_type=kind,
        status="consolidated-noindex",
        title=taxonomy_label(source_url),
        output_sha256=hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        note="Canonicalized to /healernextdoor and retained for link continuity.",
    )


def load_urls(map_path: Path) -> list[str]:
    with map_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return [row["legacy_url"].strip() for row in rows if row.get("legacy_url")]


def update_blog_sitemap(output_root: Path, successful_posts: list[str]) -> None:
    sitemap_path = output_root / "sitemap.xml"
    if not sitemap_path.exists():
        return
    document = etree.parse(str(sitemap_path))
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = document.getroot()
    for url_node in list(root):
        loc = url_node.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        value = loc.text.strip() if loc is not None and loc.text else ""
        if "/healernextdoor/category/" in value or "/healernextdoor/tag/" in value:
            root.remove(url_node)
        elif value.startswith(f"{LIVE_ORIGIN}{BLOG_PREFIX}") and value not in successful_posts:
            root.remove(url_node)
    existing = {
        node.text.strip()
        for node in root.xpath("s:url/s:loc", namespaces=namespace)
        if node.text
    }
    for url in successful_posts:
        if url in existing:
            continue
        url_node = etree.SubElement(root, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        loc_node = etree.SubElement(url_node, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        loc_node.text = url
    document.write(str(sitemap_path), encoding="utf-8", xml_declaration=True, pretty_print=True)


def write_clean_blog_hub(output_root: Path) -> None:
    source = output_root / "healernextdoor.html"
    if not source.exists():
        return
    markup = source.read_text(encoding="utf-8")
    replacements = (
        ('href="styles.css"', 'href="../styles.css"'),
        ('src="site.js"', 'src="../site.js"'),
        ('src="assets/', 'src="../assets/'),
        ('href="healernextdoor.html"', 'href="/healernextdoor"'),
        ('href="index.html"', 'href="../index.html"'),
        ('href="about-lisa.html"', 'href="../about-lisa.html"'),
        ('href="services.html"', 'href="../services.html"'),
        ('href="success-stories.html"', 'href="../success-stories.html"'),
        ('href="contact.html"', 'href="../contact.html"'),
        ('href="reiki-energy-healing.html"', 'href="../reiki-energy-healing.html"'),
        ('href="akashic-records.html"', 'href="../akashic-records.html"'),
        ('href="work-trauma-coaching.html"', 'href="../work-trauma-coaching.html"'),
    )
    for old, new in replacements:
        markup = markup.replace(old, new)
    destination = output_root / "healernextdoor" / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markup, encoding="utf-8", newline="\n")


def inspect_url(url: str) -> int:
    document = html.fromstring(fetch(url))
    print(f"title: {clean_text(document.xpath('string(//title)'))}")
    print(f"h1: {clean_text(document.xpath('string(//h1)'))}")
    print(f"articles: {len(document.xpath('//article'))}")
    print(f"articleBody nodes: {len(document.xpath('//*[@itemprop=\"articleBody\"]'))}")
    for index, node in enumerate(document.xpath('//article')):
        print(
            f"article[{index}]: id={node.get('id')!r} class={node.get('class')!r} "
            f"itemprop={node.get('itemprop')!r} words={len(text_content(node).split())}"
        )
    for index, node in enumerate(
        document.xpath(
            '(//article)[2]//*[contains(@class,"sqs-layout") or contains(@class,"sqs-html-content") '
            'or contains(@class,"blog-item") or contains(@class,"entry-content") or contains(@class,"blog-content")]'
        )
    ):
        print(
            f"candidate[{index}]: tag={node.tag} id={node.get('id')!r} class={node.get('class')!r} "
            f"words={len(text_content(node).split())}"
        )
    second_article = document.xpath('(//article)[2]')
    if second_article:
        for index, node in enumerate(second_article[0].iterdescendants()):
            if index >= 80:
                break
            if node.get("class") or node.get("id") or node.tag in {"header", "main", "section"}:
                print(
                    f"node[{index}]: tag={node.tag} id={node.get('id')!r} class={node.get('class')!r} "
                    f"words={len(text_content(node).split())}"
                )
    body = discover_body(document)
    if body is None:
        print("body: NOT FOUND")
        return 1
    print(
        f"body: tag={body.tag} id={body.get('id')!r} class={body.get('class')!r} "
        f"words={len(text_content(body).split())}"
    )
    print(etree.tostring(body, encoding="unicode", method="html")[:4000])
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", metavar="URL", help="Inspect live markup without writing files")
    parser.add_argument("--url", help="Migrate one live article URL")
    parser.add_argument("--all", action="store_true", help="Migrate all mapped posts and consolidate taxonomies")
    parser.add_argument("--limit", type=int, help="Limit post migrations for a staged run")
    project_root = Path(__file__).resolve().parents[2]
    migration_docs = project_root / "docs" / "migration"
    parser.add_argument("--map", type=Path, default=migration_docs / "blog-migration-map.csv")
    parser.add_argument("--output-root", type=Path, default=project_root)
    parser.add_argument("--report", type=Path, default=migration_docs / "blog-migration-report.csv")
    parser.add_argument("--manifest", type=Path, default=migration_docs / "blog-content-manifest.json")
    parser.add_argument("--no-assets", action="store_true", help="Keep live image URLs instead of downloading")
    parser.add_argument("--force", action="store_true", help="Replace previously migrated non-placeholder pages")
    parser.add_argument("--delay", type=float, default=0.15, help="Pause between live requests")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.inspect:
        return inspect_url(args.inspect)
    if args.url:
        result, article = migrate_post(
            args.url,
            args.output_root,
            download_assets=not args.no_assets,
            force=args.force,
        )
        upsert_report(result, args.report)
        if article:
            upsert_manifest(article, args.manifest)
        print(json.dumps(asdict(result), indent=2))
        return 0 if result.status.startswith("migrated") else 1
    if not args.all:
        print("No action selected. Use --inspect URL, --url URL, or --all.", file=sys.stderr)
        return 2

    urls = load_urls(args.map)
    post_urls = [url for url in urls if is_post_url(url)]
    taxonomy_urls = [url for url in urls if taxonomy_kind(url)]
    if args.limit is not None:
        post_urls = post_urls[: args.limit]

    results: list[MigrationResult] = []
    articles: list[Article] = []
    for index, source_url in enumerate(post_urls, start=1):
        try:
            result, article = migrate_post(
                source_url,
                args.output_root,
                download_assets=not args.no_assets,
                force=args.force,
            )
            results.append(result)
            if article:
                articles.append(article)
            print(f"[{index}/{len(post_urls)}] {result.status}: {source_url}", flush=True)
        except Exception as error:
            results.append(
                MigrationResult(
                    source_url=source_url,
                    destination=destination_for(args.output_root, source_url).relative_to(args.output_root).as_posix(),
                    content_type="post",
                    status="failed",
                    note=str(error),
                )
            )
            print(f"[{index}/{len(post_urls)}] failed: {source_url}: {error}", flush=True)
        write_report(results, args.report)
        if articles:
            write_manifest(articles, args.manifest)
        if args.delay:
            time.sleep(args.delay)

    if args.limit is None:
        for source_url in taxonomy_urls:
            try:
                results.append(migrate_taxonomy(source_url, args.output_root))
            except Exception as error:
                results.append(
                    MigrationResult(
                        source_url=source_url,
                        destination=destination_for(args.output_root, source_url).relative_to(args.output_root).as_posix(),
                        content_type=taxonomy_kind(source_url) or "taxonomy",
                        status="failed",
                        note=str(error),
                    )
                )
        write_report(results, args.report)

    successful_posts = [
        result.source_url
        for result in results
        if result.content_type == "post" and result.status in {"migrated", "migrated-with-warnings", "skipped-existing"}
    ]
    if args.limit is None:
        update_blog_sitemap(args.output_root, successful_posts)
        write_clean_blog_hub(args.output_root)

    failures = sum(result.status == "failed" for result in results)
    print(
        json.dumps(
            {
                "posts_requested": len(post_urls),
                "taxonomies_consolidated": sum(result.status == "consolidated-noindex" for result in results),
                "failures": failures,
                "report": str(args.report),
                "manifest": str(args.manifest),
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
