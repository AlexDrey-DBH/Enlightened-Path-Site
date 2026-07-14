from __future__ import annotations

import html
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote


CORE_ORDER = (
    "index.html",
    "about-lisa.html",
    "services.html",
    "reiki-energy-healing.html",
    "akashic-records.html",
    "meditation.html",
    "work-trauma-coaching.html",
    "corporate-wellness.html",
    "success-stories.html",
    "resources.html",
    "healernextdoor.html",
    "contact.html",
)


@dataclass
class PageInfo:
    path: str
    title: str
    h1: str
    canonical: str
    actions: list[str]


class PageInfoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.capture: str | None = None
        self.buffer: list[str] = []
        self.title = ""
        self.h1 = ""
        self.canonical = ""
        self.actions: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title" and not self.title:
            self.capture = "title"
            self.buffer = []
        elif tag == "h1" and not self.h1:
            self.capture = "h1"
            self.buffer = []
        elif tag == "link" and values.get("rel", "").lower() == "canonical":
            self.canonical = (values.get("href") or "").strip()

        action = (values.get("data-action-item") or "").strip()
        if action and action not in self.actions:
            self.actions.append(action)

    def handle_endtag(self, tag: str) -> None:
        if self.capture == tag:
            value = " ".join("".join(self.buffer).split())
            if tag == "title":
                self.title = value
            elif tag == "h1":
                self.h1 = value
            self.capture = None
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.buffer.append(data)

    def handle_comment(self, data: str) -> None:
        marker = data.strip()
        if marker.upper().startswith("ACTION:"):
            action = marker.split(":", 1)[1].strip()
            if action and action not in self.actions:
                self.actions.append(action)


def group_for(path: str) -> str:
    if path in CORE_ORDER:
        return "Core experience"
    if path.startswith(("healernextdoor/category/", "healernextdoor/tag/")):
        return "Legacy taxonomy"
    if path.startswith("healernextdoor/") and path.endswith("/index.html"):
        return "Healer Next Door articles"
    if path.startswith("events/"):
        return "Events"
    return "Preserved utility and legacy pages"


def page_sort_key(page: PageInfo) -> tuple[int, str]:
    if page.path in CORE_ORDER:
        return CORE_ORDER.index(page.path), page.path
    return 999, page.title.lower() or page.path.lower()


def collect_pages(output_root: Path) -> list[PageInfo]:
    pages: list[PageInfo] = []
    for page in sorted(output_root.rglob("*.html")):
        relative = page.relative_to(output_root).as_posix()
        if relative == "local-sitemap.html":
            continue
        parser = PageInfoParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        pages.append(
            PageInfo(
                path=relative,
                title=parser.title or relative,
                h1=parser.h1,
                canonical=parser.canonical,
                actions=parser.actions,
            )
        )
    return pages


def page_card(page: PageInfo) -> str:
    search = " ".join((page.path, page.title, page.h1, *page.actions)).lower()
    href = "../outputs/" + quote(page.path, safe="/")
    actions = "".join(
        f'<li><span>Action</span>{html.escape(action)}</li>' for action in page.actions
    )
    action_block = f'<ul class="page-actions">{actions}</ul>' if actions else ""
    status = '<span class="status action">Action needed</span>' if actions else '<span class="status ready">No actions</span>'
    canonical = (
        f'<p class="canonical">{html.escape(page.canonical)}</p>' if page.canonical else ""
    )
    return f"""
      <article class="page-card{' has-action' if page.actions else ''}" data-page data-search="{html.escape(search, quote=True)}">
        <div class="page-card-top">{status}<code>{html.escape(page.path)}</code></div>
        <h3><a href="{href}">{html.escape(page.h1 or page.title)}</a></h3>
        <p>{html.escape(page.title)}</p>
        {canonical}
        {action_block}
      </article>"""


def build_local_sitemap(output_root: Path, destination: Path) -> tuple[int, int]:
    pages = collect_pages(output_root)
    groups: dict[str, list[PageInfo]] = defaultdict(list)
    for page in pages:
        groups[group_for(page.path)].append(page)

    action_pages = [page for page in pages if page.actions]
    actions = sum(len(page.actions) for page in action_pages)
    order = (
        "Core experience",
        "Healer Next Door articles",
        "Events",
        "Preserved utility and legacy pages",
        "Legacy taxonomy",
    )
    sections: list[str] = []
    for group in order:
        group_pages = sorted(groups.get(group, []), key=page_sort_key)
        if not group_pages:
            continue
        open_attr = " open" if group == "Core experience" else ""
        cards = "".join(page_card(page) for page in group_pages)
        sections.append(
            f'<details class="page-group"{open_attr}><summary><span>{html.escape(group)}</span><strong>{len(group_pages)}</strong></summary><div class="page-grid">{cards}</div></details>'
        )

    action_cards = "".join(page_card(page) for page in action_pages)
    generated = datetime.now().astimezone().strftime("%B %d, %Y at %I:%M %p %Z")
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <title>Local Site Map | Enlightened Path Healing QA</title>
  <style>
    :root {{ --plum:#6f5665; --sage:#8b9677; --olive:#606049; --gold:#efb31a; --pink:#ff2f92; --ink:#2d2a2a; --muted:#6f6869; --line:#e9e2e7; --wash:#fbfaf8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--wash); font:15px/1.55 Inter,"Segoe UI",Arial,sans-serif; }}
    a {{ color:inherit; }}
    .wrap {{ width:min(1260px,calc(100% - 36px)); margin:auto; }}
    header {{ padding:50px 0 34px; background:linear-gradient(135deg,#fff,#f7f1f6 58%,#f1f5ed); border-bottom:3px solid var(--pink); }}
    .eyebrow {{ margin:0 0 8px; color:var(--pink); font-size:.75rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }}
    h1 {{ margin:0; color:var(--plum); font-size:clamp(2.2rem,5vw,4.3rem); line-height:1.02; }}
    header p {{ max-width:760px; color:var(--muted); }}
    .stats {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:24px; }}
    .stat {{ padding:8px 12px; border:1px solid var(--line); border-radius:8px; background:#fff; font-weight:750; }}
    .stat.action {{ border-color:var(--pink); color:var(--pink); }}
    main {{ padding:30px 0 70px; }}
    .toolbar {{ position:sticky; top:0; z-index:4; padding:14px 0; background:rgba(251,250,248,.94); backdrop-filter:blur(12px); }}
    input {{ width:100%; min-height:48px; padding:0 16px; border:1px solid var(--line); border-radius:8px; background:#fff; font:inherit; }}
    .action-register {{ margin:20px 0 28px; padding:24px; border:2px solid var(--pink); border-radius:8px; background:#fff2f8; }}
    .action-register h2 {{ margin:0 0 6px; color:var(--pink); }}
    .page-group {{ margin:14px 0; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .page-group > summary {{ display:flex; justify-content:space-between; gap:20px; padding:18px 20px; color:var(--olive); font-weight:800; cursor:pointer; }}
    .page-group > summary strong {{ color:var(--plum); }}
    .page-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; padding:0 18px 18px; }}
    .page-card {{ min-width:0; padding:18px; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .page-card.has-action {{ border:2px solid var(--pink); background:#fff5fa; box-shadow:0 10px 26px rgba(255,47,146,.1); }}
    .page-card-top {{ display:flex; align-items:start; justify-content:space-between; gap:10px; }}
    code {{ color:var(--muted); font-size:.72rem; overflow-wrap:anywhere; }}
    .status {{ flex:0 0 auto; padding:4px 7px; border-radius:999px; font-size:.66rem; font-weight:850; text-transform:uppercase; }}
    .status.ready {{ background:#f1f5ed; color:var(--olive); }}
    .status.action {{ background:var(--pink); color:#fff; }}
    .page-card h3 {{ margin:16px 0 5px; color:var(--plum); font-size:1.08rem; line-height:1.25; }}
    .page-card p {{ margin:0; color:var(--muted); font-size:.84rem; }}
    .canonical {{ margin-top:8px!important; font-size:.7rem!important; overflow-wrap:anywhere; }}
    .page-actions {{ margin:14px 0 0; padding:0; list-style:none; }}
    .page-actions li {{ padding:10px; border-radius:6px; background:var(--pink); color:#fff; font-weight:750; }}
    .page-actions span {{ display:block; font-size:.64rem; text-transform:uppercase; opacity:.82; }}
    [hidden] {{ display:none!important; }}
    @media(max-width:900px) {{ .page-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media(max-width:620px) {{ .page-grid {{ grid-template-columns:1fr; }} .wrap {{ width:min(100% - 24px,1260px); }} }}
  </style>
</head>
<body>
  <header><div class="wrap"><p class="eyebrow">Local QA only</p><h1>Site map and action register</h1><p>Generated from every HTML file in <code>outputs</code>. This page is ignored by Git and excluded from the committed website.</p><div class="stats"><span class="stat">{len(pages)} pages</span><span class="stat">{len(action_pages)} pages with actions</span><span class="stat action">{actions} open actions</span><span class="stat">Updated {html.escape(generated)}</span></div></div></header>
  <main class="wrap">
    <div class="toolbar"><label><span class="eyebrow">Filter pages</span><input id="page-filter" type="search" placeholder="Search by page, title, heading, or action"></label></div>
    <section class="action-register"><h2>Open action items</h2>{action_cards or '<p>No open action items.</p>'}</section>
    {''.join(sections)}
  </main>
  <script>
    const filter = document.querySelector('#page-filter');
    const cards = [...document.querySelectorAll('[data-page]')];
    filter.addEventListener('input', () => {{
      const query = filter.value.trim().toLowerCase();
      cards.forEach(card => card.hidden = query && !card.dataset.search.includes(query));
    }});
  </script>
</body>
</html>"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    return len(pages), actions


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    pages, actions = build_local_sitemap(
        project_root / "outputs", project_root / ".local" / "site-map.html"
    )
    print(f"Generated local sitemap with {pages} pages and {actions} action items")


if __name__ == "__main__":
    main()
