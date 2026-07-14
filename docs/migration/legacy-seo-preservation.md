# Legacy SEO Preservation

The live Squarespace sitemap was refreshed on June 26, 2026. The Healer Next Door archive was fully migrated from the live site on July 11, 2026.

## Integrity Check

- Healer Next Door articles migrated with full body content: 253.
- Article migrations failed: 0.
- Article pages with missing local images: 0.
- Article pages with missing canonicals, descriptions, or Article schema: 0.
- Legacy taxonomy rows consolidated: 335.
- Physical taxonomy pages after Windows case collisions: 333.
- Broken internal links in migrated article bodies: 0.

## What Was Preserved

- All 253 Healer Next Door posts now include the original article body, title, author, publication and modified dates, description, canonical URL, Open Graph metadata, and BlogPosting schema.
- Article hero images were downloaded into the repository so the archive does not depend on the retired Squarespace site.
- The clean `/healernextdoor` hub now serves the refreshed resources experience rather than a continuity placeholder.
- 34 category rows and 301 tag rows were retained for inbound-link continuity, marked `noindex,follow`, and canonicalized to `/healernextdoor`.
- Case-variant taxonomy URLs that collide on Windows have explicit redirects to their lowercase equivalents.
- Taxonomy URLs were removed from the XML sitemap because they are intentionally non-indexable.
- 30 event paths, 5 booking/get-started paths, and 21 additional legacy page paths remain preserved pending their own content audits.

## Key Files

- `outputs/blog-migration-map.csv`
  - Original URL-preservation map for the blog, categories, and tags.

- `outputs/blog-migration-report.csv`
  - Per-URL migration status, word count, dates, asset count, hashes, and notes.

- `outputs/blog-content-manifest.json`
  - Structured source-of-truth copy of all 253 migrated posts for future CMS import or comparison.

- `outputs/blog-migration-audit.json`
  - Repeatable deployment audit covering content, canonicals, schema, assets, internal links, taxonomies, hub, and sitemap.

- `outputs/_redirects`
  - Deployable 301 rules for legacy URLs that have clear redesigned equivalents and case collisions.

- `outputs/.htaccess-legacy-redirects.txt`
  - Apache-style redirect reference.

- `outputs/sitemap.xml`
  - Sitemap containing indexable legacy articles and refreshed site pages; noindex taxonomy pages are excluded.

- `outputs/robots.txt`
  - Points crawlers to the generated sitemap.

## Deployment Notes

Do not delete the generated legacy folders unless the deployment platform has equivalent server-side redirects or imported CMS content for those exact URLs.

For pages with redesigned equivalents, use `outputs/_redirects` or equivalent hosting rules.

For blog posts, keep the full migrated article at its exact legacy path. Do not replace a full article with a continuity placeholder or redirect it to the homepage.

For categories and tags, preserve the current consolidation policy unless analytics show that a specific taxonomy URL has meaningful search traffic or backlinks. If one does, promote that URL into a useful curated topic page rather than making every old tag indexable again.

Before acting on new blog information or direction, compare it against `outputs/blog-migration-report.csv`, `outputs/blog-content-manifest.json`, and `outputs/blog-migration-baseline.md`. Record intentional changes instead of silently replacing this baseline.
