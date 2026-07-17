# Editorial Handoff Reconciliation

## Scope

This implementation reconciles the seven unique client editorial handoffs delivered in July 2026:

- Homepage
- About Lisa
- Services
- Resources and Blog
- Contact
- Testimonials
- Scheduling

The second About Lisa attachment was byte-for-byte identical to the first and was not stored twice. The canonical source files are retained in `docs/editorial-handoffs/` and excluded from Vercel deployment.

## Implemented

### Core pages

- Updated the Homepage, About Lisa, Services, Resources, Contact, Testimonials, and Scheduling copy and section order to match the handoffs.
- Kept the approved visual identity and existing responsive component system.
- Standardized primary navigation as Home, About Lisa, Services, Testimonials, Resources, Contact, and Schedule a Session.
- Standardized production footers, social links, service links, and learning links.
- Replaced the former Reflections and Success Stories labels with Testimonials on client-facing navigation and testimonial surfaces.

### Testimonials

- Homepage: Shakila M., Ashley T., Jacqueline J., and Chane G.
- Testimonials page: Jeremy B., Matthew D, Victoria G., Rosi R., Marissa M., and Clare C.
- Removed the testimonial carousel from the dedicated page and restored a static responsive grid.

### Contact and scheduling

- Preserved `/get-started` as the canonical scheduling route.
- Embedded the existing Acuity scheduler without changing its owner or configuration.
- Consolidated contact inquiries into one form with required first name, email, and inquiry type; an optional general note; an unchecked newsletter checkbox; a honeypot; and accessible status messaging.
- Removed the public email address and mailto fallback.
- Routed booking and scheduling buttons to `/get-started`.

### Resources and Blog

- Rebuilt Resources as the doorway to the Blog, Services, and newsletter.
- Preserved all 253 legacy article URLs and full article bodies.
- Generated 47 chronological and topic archive pages with working pagination.
- Standardized article breadcrumbs, author/date metadata, local images, one services call to action, and the production footer.
- Consolidated legacy category and tag routes into the canonical Blog archive through permanent redirects.
- Corrected known legacy encoding and copy artifacts without rewriting article bodies.

### SEO and deployment

- Updated page titles, descriptions, canonical URLs, internal links, XML sitemap entries, Vercel routes, and redirect files.
- Generated a complete URL migration inventory at `docs/migration/old-to-new-url-and-redirect-list.csv`.
- Excluded documentation, samples, and temporary material from Vercel deployment with `.vercelignore`.
- Automated audits cover core pages, all deployable HTML, local references, sitemap URLs, and the full Blog migration.

## Pending external setup

### HubSpot newsletter

The website is ready for HubSpot, but implementation requires the client-owned HubSpot portal, General Newsletter form, Event Updates form, subscription types, and hosted fallback URLs. Follow `docs/integrations/hubspot-newsletter-implementation-plan.md`. Do not replace HubSpot with a temporary newsletter database or endpoint.

### Contact-form delivery

The discovery-call form requires the approved private submission endpoint and notification destination before launch. The public interface, validation, consent behavior, success message, and error message are implemented; delivery must be tested after the production endpoint is supplied.

### Acuity

Lisa will add Meditation as a bookable Acuity service. Recheck the existing `/get-started` embed after that Acuity-side change. Do not alter the scheduler configuration from the website.

### Live verification

After the Vercel preview is available, complete a final browser pass at desktop, tablet, and mobile widths and test HubSpot routing, contact-form delivery, Acuity loading, and every third-party fallback link against the deployed domain.
