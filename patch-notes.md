# Patch Notes

Updated September 21, 2026. All history entries are retained; later entries may supersede earlier implementations.

Patch notes preference: keep this client-readable Markdown document as the primary project history. Preserve prior entries when adding new work.

## September 2026

- Blog: published "What Life Has Taught Me: The Ego's Greatest Trick" with its supplied image; refreshed the homepage, blog archives, topic archive, metadata, structured data, and sitemap through the managed blog build.
- Blog: published "Maybe You Don't Need to Climb the Mountain." The article is dated September 1 and was deployed September 3.
- Blog publisher: retained the free workflow in which the client prepares a post and selects **Publish Now** at or after the planned date and time.

## August 2026

- Blog publisher: added a private Cloudflare Worker dashboard for entering a title, article copy, image, topic, and planned publication time.
- Blog automation: connected new posts to the article page, SEO metadata, canonical URL, Open Graph data, `BlogPosting` schema, XML sitemap, main blog archive, topic archive, homepage feed, and card excerpt.
- Blog previews: made cards use the article's opening sentence automatically.
- Homepage: made the latest-blog section update from the managed blog source.
- Blog: published "What Life Has Taught Me: The Trouble With Pedestals" with its supplied image.
- Blog: published "Why We Have Such a Hard Time Trusting Ourselves" and added its supplied hero image.

## July 2026

- Deployment: configured GitHub Pages to publish from `main` through GitHub Actions.
- Routes: added clean production routes while preserving legacy blog and search URLs.
- Editorial handoff: reconciled final page copy, navigation, footer labels, testimonials, scheduling, metadata, sitemap, and redirects.
- HubSpot: embedded the General Newsletter and Event Updates forms with separate subscriber routing.
- HubSpot: connected the Resources newsletter signup to the General Newsletter form.
- Analytics: installed Google Analytics and HubSpot tracking sitewide.
- Search branding: changed the search/favicon image to the mark-only logo.
- Scheduling: preserved `/get-started` for the embedded Acuity scheduler and removed the redundant page-level booking button.
- Scheduler research: added an unlisted `/newscheduler` staging page without replacing Acuity.
- Homepage: connected "Help Me Choose" to the five-ways-to-work-together section and added discovery-call guidance.
- Contact: removed the redundant alternate contact-options section.
- About Lisa: linked the Montclair Girl award badge.
- Testimonials: aligned card content and corrected responsive hero line wrapping.
- Responsive QA: refined key headings, location labels, booking details, pathway controls, and social icons across phone and tablet breakpoints.

## Active Maintenance

1. **Blog publisher:** confirm the Cloudflare Worker is deployed, its GitHub token and publisher password are current, and the client can complete a test draft and publication.
2. **Blog publishing:** verify each new post appears on the article page, homepage, main blog archive, matching topic archive, and XML sitemap after GitHub Pages finishes deploying.
3. **Newsletter:** retain separate General Newsletter and Event Updates routing, unchecked consent controls, double opt-in, and existing unsubscribe status.
4. **Scheduling:** keep Acuity unchanged on `/get-started`; recheck the embed whenever services are changed inside Acuity.
5. **Launch QA:** periodically test forms, buttons, redirects, canonical URLs, metadata, analytics, accessibility, and desktop/tablet/mobile layouts.

## Implementation Notes

- The production site is a static repository deployed from `main` by `.github/workflows/deploy-pages.yml`.
- The deployment excludes `docs/`, `samples/`, and `tmp/` from the public website.
- The free blog publisher does not publish unattended at a scheduled time. The client must sign in and choose **Publish Now** at or after the planned time.
- Publisher images are limited to 1 MB for the Cloudflare Workers Free workflow.
- Publisher secrets must remain in Cloudflare and must never be committed or sent by email.
- HubSpot is the subscriber system of record. Do not create a separate newsletter database or re-subscribe previously unsubscribed contacts.
- Acuity remains the live scheduling system unless a replacement is separately approved and completed.

## Reference

- [Project README](README.md)
- [Blog publisher setup](docs/publisher-worker/README.md)
- [Managed blog records](docs/publisher-content/posts.json)
- [GitHub Pages workflow](.github/workflows/deploy-pages.yml)
- [XML sitemap](sitemap.xml)
