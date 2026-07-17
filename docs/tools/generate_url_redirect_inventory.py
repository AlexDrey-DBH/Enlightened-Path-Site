from __future__ import annotations

import csv
from pathlib import Path


DOMAIN = "https://www.enlightenedpathhealing.com"

CANONICAL_DESTINATIONS = {
    "/index.html": "/",
    "/about-lisa.html": "/about",
    "/contact.html": "/contact",
    "/corporate-wellness.html": "/corporate-wellness",
    "/services.html": "/services",
    "/success-stories.html": "/testimonials",
    "/testimonials.html": "/testimonials",
    "/reiki-energy-healing.html": "/reiki-energy-healing",
    "/akashic-records.html": "/akashic-records",
    "/meditation.html": "/meditation",
    "/work-trauma-coaching.html": "/work-trauma",
    "/resources.html": "/resources",
    "/healernextdoor.html": "/healernextdoor",
}

PRESERVE_OVERRIDES = {
    "/about": "/about",
    "/contact": "/contact",
    "/corporate-wellness": "/corporate-wellness",
    "/events": "/events",
    "/get-started": "/get-started",
    "/healernextdoor": "/healernextdoor",
    "/newsletter": "/newsletter",
    "/services": "/services",
    "/testimonials": "/testimonials",
}

EXPLICIT_REDIRECTS = {
    "/home": "/",
    "/links": "/healernextdoor",
    "/love": "/testimonials",
    "/newcomers": "/services",
    "/reflections": "/testimonials",
    "/success-stories": "/testimonials",
    "/success-stories.html": "/testimonials",
}

CURRENT_ROUTES = {
    "/": "index.html",
    "/about": "about-lisa.html",
    "/akashic-records": "akashic-records.html",
    "/contact": "contact.html",
    "/corporate-wellness": "corporate-wellness.html",
    "/events": "events/index.html",
    "/get-started": "get-started/index.html",
    "/healernextdoor": "healernextdoor.html",
    "/meditation": "meditation.html",
    "/newsletter": "newsletter/index.html",
    "/reiki-energy-healing": "reiki-energy-healing.html",
    "/resources": "resources.html",
    "/services": "services.html",
    "/testimonials": "testimonials.html",
    "/work-trauma": "work-trauma-coaching.html",
}


def clean_destination(value: str) -> str:
    value = (value or "").strip()
    if value.startswith(DOMAIN):
        value = value[len(DOMAIN) :] or "/"
    return CANONICAL_DESTINATIONS.get(value, value or "/")


def clean_local_file(value: str) -> str:
    value = (value or "").strip().replace("\\", "/")
    if value.startswith("outputs/"):
        value = value[len("outputs/") :]
    return value


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    source = root / "docs" / "migration" / "legacy-seo-inventory.csv"
    destination = root / "docs" / "migration" / "old-to-new-url-and-redirect-list.csv"
    rows: dict[str, dict[str, str]] = {}

    with source.open(newline="", encoding="utf-8-sig") as handle:
        for item in csv.DictReader(handle):
            old_path = (item.get("path") or "/").strip() or "/"
            proposed = clean_destination(item.get("recommended_destination") or old_path)
            new_path = PRESERVE_OVERRIDES.get(old_path, proposed)
            if old_path in EXPLICIT_REDIRECTS:
                new_path = EXPLICIT_REDIRECTS[old_path]

            status = "200" if old_path == new_path else "301"
            treatment = "preserve" if status == "200" else "redirect"
            local_file = clean_local_file(item.get("local_file") or "")
            if old_path in CURRENT_ROUTES:
                local_file = CURRENT_ROUTES[old_path]

            rows[old_path] = {
                "old_url": item.get("legacy_url") or f"{DOMAIN}{old_path}",
                "old_path": old_path,
                "new_url": f"{DOMAIN}{new_path}" if new_path != "/" else f"{DOMAIN}/",
                "new_path": new_path,
                "status_code": status,
                "treatment": treatment,
                "content_type": item.get("category") or "legacy-page",
                "local_file": local_file,
                "notes": item.get("recommended_action") or "",
            }

    for path, local_file in CURRENT_ROUTES.items():
        rows.setdefault(
            path,
            {
                "old_url": f"{DOMAIN}{path}" if path != "/" else f"{DOMAIN}/",
                "old_path": path,
                "new_url": f"{DOMAIN}{path}" if path != "/" else f"{DOMAIN}/",
                "new_path": path,
                "status_code": "200",
                "treatment": "preserve",
                "content_type": "core-page",
                "local_file": local_file,
                "notes": "Canonical production route",
            },
        )

    for old_path, new_path in EXPLICIT_REDIRECTS.items():
        rows[old_path] = {
            "old_url": f"{DOMAIN}{old_path}",
            "old_path": old_path,
            "new_url": f"{DOMAIN}{new_path}" if new_path != "/" else f"{DOMAIN}/",
            "new_path": new_path,
            "status_code": "301",
            "treatment": "redirect",
            "content_type": "legacy-route",
            "local_file": CURRENT_ROUTES.get(new_path, ""),
            "notes": "Explicit permanent redirect",
        }

    fields = (
        "old_url",
        "old_path",
        "new_url",
        "new_path",
        "status_code",
        "treatment",
        "content_type",
        "local_file",
        "notes",
    )
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows[path] for path in sorted(rows, key=lambda value: (value.count("/"), value)))

    print(f"Wrote {len(rows)} URL mappings to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
