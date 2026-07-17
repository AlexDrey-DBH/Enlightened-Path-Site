#!/usr/bin/env python3
"""Build the Healer Next Door archive from the preserved migration manifest."""

from __future__ import annotations

import html as html_module
import json
import math
import posixpath
import re
from datetime import datetime
from pathlib import Path

from lxml import etree, html


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "migration" / "blog-content-manifest.json"
LIVE_ORIGIN = "https://www.enlightenedpathhealing.com"
PAGE_SIZE = 12

TOPICS = (
    ("healing-spiritual-growth", "Healing & Spiritual Growth"),
    ("reiki-energy-healing", "Reiki & Energy Healing"),
    ("akashic-records-intuition", "Akashic Records & Intuition"),
    ("meditation-mindfulness", "Meditation & Mindfulness"),
    ("work-burnout-everyday-life", "Work, Burnout & Everyday Life"),
    ("astrology-guest-posts", "Astrology & Guest Posts"),
)


def repair_mojibake(value: str) -> str:
    """Repair UTF-8 text that was previously decoded as Windows-1252."""
    if not any(marker in value for marker in ("â", "Ã", "Â")):
        return value
    try:
        candidate = value.encode("cp1252").decode("utf-8")
        if sum(candidate.count(marker) for marker in ("â", "Ã", "Â")) < sum(value.count(marker) for marker in ("â", "Ã", "Â")):
            return candidate
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    replacements = {
        "â€™": "’", "â€˜": "‘", "â€œ": "“", "â€": "”",
        "â€“": "–", "â€”": "—", "â€¦": "…", "â€¢": "•",
        "Â·": "·", "Â ": " ", "Â": "",
    }
    for broken, repaired in replacements.items():
        value = value.replace(broken, repaired)
    return value


def repair_record(value):
    if isinstance(value, str):
        return repair_mojibake(value)
    if isinstance(value, list):
        return [repair_record(item) for item in value]
    if isinstance(value, dict):
        return {key: repair_record(item) for key, item in value.items()}
    return value


def slug_for(record: dict) -> str:
    return record["canonical_url"].rstrip("/").rsplit("/", 1)[-1]


def plain_text(fragment_html: str) -> list[str]:
    wrapper = html.fragment_fromstring(fragment_html, create_parent="div")
    return [re.sub(r"\s+", " ", value).strip() for value in wrapper.xpath(".//p//text()") if value.strip()]


def paragraphs(fragment_html: str) -> list[str]:
    wrapper = html.fragment_fromstring(fragment_html, create_parent="div")
    values = []
    for node in wrapper.xpath(".//p"):
        value = re.sub(r"\s+", " ", " ".join(node.itertext())).strip()
        if value:
            values.append(value)
    return values


def actual_author(record: dict) -> str:
    for paragraph in paragraphs(record.get("body_html", ""))[:3]:
        match = re.match(r"^By\s+([A-Z][A-Za-z.'-]+\s+[A-Z][A-Za-z.'-]+)\b", paragraph)
        if match:
            return match.group(1).strip()
    return record.get("author") or "Lisa Batitto"


def first_sentence(record: dict) -> str:
    values = paragraphs(record.get("body_html", ""))
    for value in values:
        byline = re.match(r"^By\s+[A-Z][A-Za-z.'-]+\s+[A-Z][A-Za-z.'-]+\b\s*", value)
        if byline:
            value = value[byline.end():].strip()
            if not value:
                continue
        match = re.search(r"^(.+?[.!?][\"']?)(?=\s+[A-Z\"']|$)", value)
        return (match.group(1) if match else value).strip()
    return record.get("description", "").strip()


def normalized_topic(record: dict) -> tuple[str, str]:
    values = [record.get("title", ""), *record.get("categories", []), *record.get("tags", [])]
    haystack = " ".join(values).lower()
    title = record.get("title", "").lower()

    rules = (
        ("astrology-guest-posts", ("guest column", "astrolog", "zodiac", "full moon", "horoscope", "equinox", "solstice", "supermoon")),
        ("reiki-energy-healing", ("reiki", "energy healing", "chakra", "crystal", "aura", "cord cutting", "vibration")),
        ("akashic-records-intuition", ("akashic", "intuition", "intuitive", "psychic", "spirit guide", "angel guide", "spiritual download")),
        ("meditation-mindfulness", ("meditat", "mindful", "mantra", "breathwork", "grounding")),
        ("work-burnout-everyday-life", ("work", "burnout", "office", "corporate", "career", "professional", "stress", "toxic workplace")),
    )
    if title.startswith("guest column"):
        key = "astrology-guest-posts"
    else:
        key = next((candidate for candidate, terms in rules if any(term in haystack for term in terms)), "healing-spiritual-growth")
    return next(topic for topic in TOPICS if topic[0] == key)


def display_date(value: str) -> str:
    if not value:
        return ""
    return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%B %d, %Y").replace(" 0", " ")


def local_image(slug: str) -> Path | None:
    directory = ROOT / "assets" / "blog" / slug
    candidates = sorted(directory.glob("hero.*")) if directory.exists() else []
    return candidates[0] if candidates else None


def relative(from_file: Path, target: Path) -> str:
    return posixpath.relpath(target.as_posix(), from_file.parent.as_posix())


def card(record: dict, output_file: Path) -> str:
    slug = slug_for(record)
    title = html_module.escape(record["title"])
    author = html_module.escape(actual_author(record))
    excerpt = html_module.escape(first_sentence(record))
    key, label = normalized_topic(record)
    post_href = relative(output_file.relative_to(ROOT), Path("healernextdoor") / slug / "index.html")
    image = local_image(slug)
    image_markup = ""
    if image:
        image_href = relative(output_file.relative_to(ROOT), image.relative_to(ROOT))
        image_markup = f'<a class="blog-card-image" href="{post_href}"><img src="{image_href}" alt="{title}" loading="lazy"></a>'
    published = record.get("published", "")
    date_markup = ""
    if published:
        date_markup = f'<time datetime="{html_module.escape(published[:10])}">{html_module.escape(display_date(published))}</time> &middot; '
    return (
        f'<article class="blog-card">{image_markup}<span class="chip">{html_module.escape(label)}</span>'
        f'<h3><a href="{post_href}">{title}</a></h3>'
        f'<p class="blog-card-meta">{date_markup}{author}</p><p>{excerpt}</p>'
        f'<a class="text-link" href="{post_href}">Read Blog</a></article>'
    )


def topic_nav(output_file: Path, current: str | None = None) -> str:
    root_href = relative(output_file.relative_to(ROOT), Path("healernextdoor.html"))
    links = [f'<a href="{root_href}"{(" aria-current=\"page\"" if current is None else "")}>All Blogs</a>']
    for key, label in TOPICS:
        href = relative(output_file.relative_to(ROOT), Path("healernextdoor") / "topic" / key / "index.html")
        current_markup = ' aria-current="page"' if current == key else ""
        links.append(f'<a href="{href}"{current_markup}>{html_module.escape(label)}</a>')
    return '<nav class="blog-topic-nav" aria-label="Blog topics">' + "".join(links) + "</nav>"


def pagination(output_file: Path, page: int, pages: int, topic: str | None) -> str:
    if pages <= 1:
        return ""

    def target(number: int) -> Path:
        if topic:
            base = Path("healernextdoor") / "topic" / topic
        else:
            base = Path("healernextdoor")
        return (base / "index.html") if number == 1 and topic else (Path("healernextdoor.html") if number == 1 else base / "page" / str(number) / "index.html")

    links = []
    if page > 1:
        links.append(f'<a class="button secondary" href="{relative(output_file.relative_to(ROOT), target(page - 1))}">Newer Blogs</a>')
    if page < pages:
        links.append(f'<a class="button secondary" href="{relative(output_file.relative_to(ROOT), target(page + 1))}">Older Blogs</a>')
    return '<nav class="blog-pagination" aria-label="Blog pagination">' + "".join(links) + "</nav>"


def shell(output_file: Path, records: list[dict], page: int, pages: int, topic: tuple[str, str] | None) -> str:
    rel_file = output_file.relative_to(ROOT)
    home = relative(rel_file, Path("index.html"))
    about = relative(rel_file, Path("about-lisa.html"))
    services = relative(rel_file, Path("services.html"))
    testimonials = relative(rel_file, Path("testimonials.html"))
    resources = relative(rel_file, Path("resources.html"))
    contact = relative(rel_file, Path("contact.html"))
    schedule = relative(rel_file, Path("get-started") / "index.html")
    newsletter = relative(rel_file, Path("newsletter") / "index.html")
    events = relative(rel_file, Path("events") / "index.html")
    css = relative(rel_file, Path("styles.css"))
    script = relative(rel_file, Path("site.js"))
    logo = relative(rel_file, Path("assets") / "enlightened-path-healing-logo.png")
    instagram_icon = relative(rel_file, Path("assets") / "icons" / "social" / "instagram.svg")
    tiktok_icon = relative(rel_file, Path("assets") / "icons" / "social" / "tiktok.svg")
    youtube_icon = relative(rel_file, Path("assets") / "icons" / "social" / "youtube.svg")

    topic_key = topic[0] if topic else None
    topic_label = topic[1] if topic else None
    if topic:
        canonical_path = f"/healernextdoor/topic/{topic_key}" + (f"/page/{page}" if page > 1 else "")
        eyebrow = "Blog topic"
        heading = topic_label
        intro = "Browse the latest Healer Next Door blogs in this topic."
    else:
        canonical_path = "/healernextdoor" + (f"/page/{page}" if page > 1 else "")
        eyebrow = "Blog"
        heading = "Healer Next Door Blog" if page == 1 else f"Healer Next Door Blog: Page {page}"
        intro = "Thoughts on healing, spiritual life, work, and being human, written by Lisa Batitto with occasional guest contributions."

    cards = "\n      ".join(card(record, output_file) for record in records)
    archive_title = "Latest Blogs" if page == 1 else f"Blogs: Page {page}"
    canonical = f"{LIVE_ORIGIN}{canonical_path}"

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_module.escape(heading)} | Enlightened Path Healing</title>
  <meta name="description" content="{html_module.escape(intro, quote=True)}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="{css}">
</head>
<body>
  <header class="site-header"><nav class="nav" aria-label="Primary navigation"><a href="{home}"><img class="logo" src="{logo}" alt="Enlightened Path Healing"></a><button class="nav-toggle" type="button" aria-label="Open navigation menu" aria-expanded="false"><span></span><span></span><span></span></button><div class="nav-links"><a href="{home}">Home</a><a href="{about}">About Lisa</a><a href="{services}">Services</a><a href="{testimonials}">Testimonials</a><a href="{resources}" aria-current="page">Resources</a><a href="{contact}">Contact</a><a class="button" href="{schedule}">Schedule a Session</a></div></nav></header>
  <main>
    <section class="page-hero blog-hero"><div class="container"><p class="eyebrow">{eyebrow}</p><h1>{html_module.escape(heading)}</h1><p>{html_module.escape(intro)}</p><div class="hero-actions"><a class="button" href="#latest">Read Latest Blogs</a><a class="button secondary" href="{newsletter}">Join the Newsletter</a></div></div></section>
    <section class="page-section blog-browse"><div class="container"><p class="eyebrow">Browse</p><h2>Explore by topic</h2>{topic_nav(output_file, topic_key)}</div></section>
    <section class="page-section sage-soft" id="latest"><div class="container"><div class="section-head"><p class="eyebrow">Blog</p><h2>{archive_title}</h2></div><div class="blog-grid">{cards}</div>{pagination(output_file, page, pages, topic_key)}</div></section>
    <section class="page-section"><div class="container narrow-copy"><p class="eyebrow">Services</p><h2>Want to explore working with Lisa?</h2><p>Learn about Reiki, Akashic Records, meditation, Work Trauma Coaching, and Corporate Wellness.</p><a class="button secondary" href="{services}">View Services</a></div></section>
    <section class="page-section newsletter-section"><div class="container newsletter-card"><div class="newsletter-copy"><p class="eyebrow">Newsletter</p><h2>Get new blogs in your inbox.</h2><p>Join the monthly Enlightened Path Healing newsletter for new blogs, resources, events, and practice updates.</p></div><div><a class="button" href="{newsletter}">Join the Newsletter</a></div></div></section>
  </main>
  <footer class="site-footer"><div class="container footer-sitemap-grid"><div class="footer-brand"><img class="logo" src="{logo}" alt="Enlightened Path Healing"><p>Montclair, NJ and online</p><div class="social-buttons footer-social" aria-label="Social links"><a class="social-button" href="https://www.instagram.com/enlightenedpathhealing/" target="_blank" rel="noopener"><img src="{instagram_icon}" alt="">Instagram</a><a class="social-button" href="https://www.tiktok.com/@enlightenedpathhealing" target="_blank" rel="noopener"><img src="{tiktok_icon}" alt="">TikTok</a><a class="social-button" href="https://www.youtube.com/channel/UC6KWXhYQzhJz953m7GaRYKA" target="_blank" rel="noopener"><img src="{youtube_icon}" alt="">YouTube</a></div></div><nav class="footer-group" aria-label="Practice links"><h2>Practice</h2><a href="{home}">Home</a><a href="{about}">About Lisa</a><a href="{services}">Services</a><a href="{testimonials}">Testimonials</a><a href="{contact}">Contact</a></nav><nav class="footer-group" aria-label="Service links"><h2>Services</h2><a href="{relative(rel_file, Path('reiki-energy-healing.html'))}">Reiki and Energy Healing</a><a href="{relative(rel_file, Path('akashic-records.html'))}">Akashic Records</a><a href="{relative(rel_file, Path('meditation.html'))}">Meditation</a><a href="{relative(rel_file, Path('work-trauma-coaching.html'))}">Work Trauma Coaching</a><a href="{relative(rel_file, Path('corporate-wellness.html'))}">Corporate Wellness</a></nav><nav class="footer-group" aria-label="Learning links"><h2>Learn</h2><a href="{resources}">Resources</a><a href="{relative(rel_file, Path('healernextdoor.html'))}">Blog</a><a href="{relative(rel_file, Path('faq') / 'index.html')}">FAQ</a><a href="{events}">Events</a><a href="{newsletter}">Newsletter</a></nav></div></footer>
  <script src="{script}"></script>
</body>
</html>
'''


def output_for(page: int, topic: str | None) -> Path:
    if topic:
        base = ROOT / "healernextdoor" / "topic" / topic
        return base / "index.html" if page == 1 else base / "page" / str(page) / "index.html"
    return ROOT / "healernextdoor.html" if page == 1 else ROOT / "healernextdoor" / "page" / str(page) / "index.html"


def write_archive(records: list[dict], topic: tuple[str, str] | None = None) -> list[Path]:
    pages = max(1, math.ceil(len(records) / PAGE_SIZE))
    outputs = []
    for page in range(1, pages + 1):
        output = output_for(page, topic[0] if topic else None)
        output.parent.mkdir(parents=True, exist_ok=True)
        subset = records[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
        output.write_text(shell(output, subset, page, pages, topic), encoding="utf-8", newline="\n")
        outputs.append(output)
    return outputs


def update_sitemap(outputs: list[Path]) -> None:
    sitemap = ROOT / "sitemap.xml"
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    document = etree.parse(str(sitemap))
    root = document.getroot()

    for node in list(root):
        loc = node.find(f"{{{namespace}}}loc")
        value = loc.text.strip() if loc is not None and loc.text else ""
        if "/healernextdoor/page/" in value or "/healernextdoor/topic/" in value:
            root.remove(node)

    urls = []
    for output in outputs:
        rel = output.relative_to(ROOT).as_posix()
        if rel == "healernextdoor.html":
            path = "/healernextdoor"
        else:
            path = "/" + rel.removesuffix("/index.html")
        urls.append(f"{LIVE_ORIGIN}{path}")

    existing = {node.text.strip() for node in root.xpath("s:url/s:loc", namespaces={"s": namespace}) if node.text}
    for value in urls:
        if value in existing:
            continue
        url_node = etree.SubElement(root, f"{{{namespace}}}url")
        loc_node = etree.SubElement(url_node, f"{{{namespace}}}loc")
        loc_node.text = value
    document.write(str(sitemap), encoding="utf-8", xml_declaration=True, pretty_print=True)


def article_footer() -> str:
    return '''  <footer class="site-footer"><div class="container footer-sitemap-grid"><div class="footer-brand"><img class="logo" src="../../assets/enlightened-path-healing-logo.png" alt="Enlightened Path Healing"><p>Montclair, NJ and online</p><div class="social-buttons footer-social" aria-label="Social links"><a class="social-button" href="https://www.instagram.com/enlightenedpathhealing/" target="_blank" rel="noopener"><img src="../../assets/icons/social/instagram.svg" alt="">Instagram</a><a class="social-button" href="https://www.tiktok.com/@enlightenedpathhealing" target="_blank" rel="noopener"><img src="../../assets/icons/social/tiktok.svg" alt="">TikTok</a><a class="social-button" href="https://www.youtube.com/channel/UC6KWXhYQzhJz953m7GaRYKA" target="_blank" rel="noopener"><img src="../../assets/icons/social/youtube.svg" alt="">YouTube</a></div></div><nav class="footer-group" aria-label="Practice links"><h2>Practice</h2><a href="../../index.html">Home</a><a href="../../about-lisa.html">About Lisa</a><a href="../../services.html">Services</a><a href="../../testimonials.html">Testimonials</a><a href="../../contact.html">Contact</a></nav><nav class="footer-group" aria-label="Service links"><h2>Services</h2><a href="../../reiki-energy-healing.html">Reiki and Energy Healing</a><a href="../../akashic-records.html">Akashic Records</a><a href="../../meditation.html">Meditation</a><a href="../../work-trauma-coaching.html">Work Trauma Coaching</a><a href="../../corporate-wellness.html">Corporate Wellness</a></nav><nav class="footer-group" aria-label="Learning links"><h2>Learn</h2><a href="../../resources.html">Resources</a><a href="../../healernextdoor.html">Blog</a><a href="../../faq/index.html">FAQ</a><a href="../../events/index.html">Events</a><a href="../../newsletter/index.html">Newsletter</a></nav></div></footer>
'''


def refresh_article_shells(records: list[dict]) -> None:
    aside = '<aside class="legacy-article-aside"><p class="eyebrow">Services</p><h2>Want to explore working with Lisa?</h2><p>Learn about Reiki, Akashic Records, meditation, Work Trauma Coaching, and Corporate Wellness.</p><a class="button" href="../../services.html">View Services</a></aside>'
    for record in records:
        path = ROOT / "healernextdoor" / slug_for(record) / "index.html"
        if not path.exists():
            continue
        markup = repair_mojibake(path.read_text(encoding="utf-8"))
        markup = markup.replace("A<em>nd in our lifetimes", "<em>And in our lifetimes")
        markup = markup.replace('<a href="../../healernextdoor.html">Resources</a>', '<a href="../../resources.html">Resources</a>')
        markup = markup.replace('<a class="button" href="../../contact.html">Book a Discovery Call</a>', '<a class="button" href="../../get-started/index.html">Schedule a Session</a>')
        markup = markup.replace('<a class="eyebrow" href="../../healernextdoor.html">Healer Next Door</a>', '<a class="eyebrow" href="../../healernextdoor.html">Back to the Blog</a>')
        markup = re.sub(
            r'(<div class="legacy-article-heading"><a class="eyebrow".*?</a><h1>.*?</h1>)<p>.*?</p>(<div class="legacy-article-meta">)',
            r"\1\2",
            markup,
            flags=re.DOTALL,
        )
        markup = re.sub(r'<aside class="legacy-article-aside">.*?</aside>', aside, markup, flags=re.DOTALL)
        markup = re.sub(r'\s*<section class="final-cta">.*?</section>\s*(?=</main>)', "\n", markup, flags=re.DOTALL)
        author = html_module.escape(actual_author(record))
        markup = re.sub(r'(<div class="legacy-article-meta">.*?<span>By )[^<]+(</span>)', rf"\1{author}\2", markup, count=1, flags=re.DOTALL)
        markup = re.sub(
            r'("author":\s*\{"@type":\s*"Person",\s*"name":\s*")[^"]+("\})',
            rf"\1{author}\2",
            markup,
            count=1,
        )
        footer_markup = article_footer().rstrip()
        if '<footer class="site-footer">' in markup:
            markup = re.sub(r'<footer class="site-footer">.*?</footer>', footer_markup, markup, count=1, flags=re.DOTALL)
        else:
            markup = markup.replace('  <script src="../../site.js"></script>', footer_markup + '\n  <script src="../../site.js"></script>')
        path.write_text(markup, encoding="utf-8", newline="\n")


def main() -> None:
    records = repair_record(json.loads(MANIFEST.read_text(encoding="utf-8")))
    records.sort(key=lambda record: record.get("published", ""), reverse=True)
    outputs = write_archive(records)

    for topic in TOPICS:
        subset = [record for record in records if normalized_topic(record)[0] == topic[0]]
        if subset:
            outputs.extend(write_archive(subset, topic))

    # Keep the folder-index form usable for static hosts while canonicalizing to /healernextdoor.
    clean_hub = ROOT / "healernextdoor" / "index.html"
    clean_hub.write_text(shell(clean_hub, records[:PAGE_SIZE], 1, math.ceil(len(records) / PAGE_SIZE), None), encoding="utf-8", newline="\n")
    refresh_article_shells(records)
    update_sitemap(outputs)
    print(f"Generated {len(outputs)} archive pages from {len(records)} posts.")


if __name__ == "__main__":
    main()
