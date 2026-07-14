# Enlightened Path Healing

The production website lives directly in this repository root. It is a static site designed for GitHub source control and direct deployment through Vercel.

## Production structure

- `index.html` and root HTML files: primary pages
- `assets/`: production images, fonts, and licensed social icons
- route folders such as `about/`, `healernextdoor/`, and `events/`: legacy and SEO-preserved URLs
- `styles.css` and `site.js`: shared site styling and behavior
- `sitemap.xml`, `robots.txt`, `_redirects`, and `vercel.json`: search and deployment configuration
- `docs/`: non-production strategy, migration, QA, integration, and maintenance material

## Local preview

```powershell
py -m http.server 8000
```

Open `http://localhost:8000/`.

## Vercel deployment

Import this repository in Vercel and use these settings:

- Framework Preset: `Other`
- Build Command: leave blank
- Output Directory: leave blank

Vercel serves `index.html` from the repository root. `vercel.json` preserves the clean canonical routes and redirects used by the prior site.

## SEO preservation

The full Healer Next Door archive remains in `healernextdoor/`, including legacy taxonomy routes and local image assets. Migration records and audits are retained under `docs/migration/` for reference, but are not published as website files.

## Asset note

The social icons in `assets/icons/social/` are derived from a client-supplied, licensed Adobe Stock EPS. Do not redistribute the original stock source independently of its license.
