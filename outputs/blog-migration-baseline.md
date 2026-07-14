# Healer Next Door Migration Baseline

Baseline date: July 11, 2026

This file records the migration decisions that must be checked before future blog content, SEO, taxonomy, or platform instructions are implemented.

## Current Baseline

- `/healernextdoor` is the canonical editorial hub.
- 253 article URLs retain their exact live paths.
- Every article contains the original live body copy and publication metadata.
- Every article is indexable and self-canonical.
- Every article includes a meta description, Open Graph metadata, and BlogPosting schema.
- Article hero assets are repository-owned rather than dependent on Squarespace.
- 335 legacy category/tag rows are retained for continuity but are `noindex,follow` and canonicalized to the hub.
- Taxonomy URLs are excluded from the sitemap.
- Two case-variant taxonomy collisions are handled by explicit redirects.
- The migration audit passes with zero failures, missing assets, canonical mismatches, or broken article links.

## Comparison Rule for Future Direction

Before changing the blog based on new information:

1. Identify which existing URLs, posts, tags, metadata, or internal links would change.
2. Compare the instruction with the analytics-led hierarchy: Reiki first, Akashic Records emerging, Meditation underused, Work Trauma and Corporate Wellness as growth areas.
3. Preserve established article URLs unless a documented redirect is approved.
4. Do not re-index thin or duplicate taxonomy pages without evidence of demand or backlinks.
5. Do not replace full migrated articles with summaries, archive notices, or generic redirects.
6. Record the reason and expected SEO effect of any change in the migration report or a dated addendum.

## Verification Sources

- `blog-migration-report.csv`: URL-level status and content hashes.
- `blog-content-manifest.json`: structured copy and metadata baseline.
- `blog-migration-audit.json`: current integrity results.
- `blog-migration-map.csv`: original route-preservation map.
- `sitemap.xml`: current indexable URL set.
