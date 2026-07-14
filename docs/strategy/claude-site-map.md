# Enlightened Path Healing Sitemap for Claude

Use this sitemap as the structural source of truth when writing website copy. Do not add, remove, merge, rename, or reorganize core pages unless the implementation team explicitly changes this plan.

## Primary Navigation

1. Home
2. About Lisa
3. Services
4. Reflections
5. Resources
6. Contact
7. Persistent CTA: Schedule a Session

## Core Site Hierarchy

```text
Home                                            /
|
+-- About Lisa                                  /about
|
+-- Services                                    /services
|   |
|   +-- Reiki and Energy Healing                /reiki-energy-healing
|   +-- Akashic Records                         /akashic-records
|   +-- Meditation                              /meditation
|   +-- Work Trauma Coaching                    /work-trauma
|   +-- Corporate Wellness                      /corporate-wellness
|
+-- Reflections                                 /testimonials
|
+-- Resources                                   /resources
|   |
|   +-- Healer Next Door                        /healernextdoor
|       |
|       +-- 253 preserved legacy articles       /healernextdoor/{existing-slug}
|
+-- Contact and Schedule                        /contact
    |
    +-- Acuity scheduler                        /contact#book-online
```

## Core Page Map

| Navigation/Page | Canonical route | Current project file | Primary job | Primary conversion |
|---|---|---|---|---|
| Home | `/` | `index.html` | Establish the promise, route visitors by need, and build trust | Schedule a Session |
| About Lisa | `/about` | `about-lisa.html` | Establish founder credibility, fit, credentials, interviews, and accolades | Schedule a Session |
| Services | `/services` | `services.html` | Help visitors choose a service by need | Help Me Choose |
| Reiki and Energy Healing | `/reiki-energy-healing` | `reiki-energy-healing.html` | Primary organic acquisition page for local and virtual Reiki | Schedule a Reiki Session |
| Akashic Records | `/akashic-records` | `akashic-records.html` | Primary growth page for readings and reflective spiritual guidance | Schedule an Akashic Reading |
| Meditation | `/meditation` | New page required | Capture local meditation demand and explain available pathways | Explore Meditation Options |
| Work Trauma Coaching | `/work-trauma` | `work-trauma-coaching.html` | Convert visitors recovering from toxic workplaces, burnout, layoffs, and identity loss | Talk Through What Happened |
| Corporate Wellness | `/corporate-wellness` | `corporate-wellness.html` | Convert HR, leadership, small-business, and wellness-program inquiries | Plan a Workplace Program |
| Reflections | `/testimonials` | `success-stories.html` | Build confidence with preserved client experiences | Help Me Choose |
| Resources | `/resources` | `resources.html` | Route visitors to useful content, services, and newsletter signup | Explore Resources |
| Healer Next Door | `/healernextdoor` | `healernextdoor.html` | Canonical editorial hub and long-tail organic acquisition | Read, subscribe, or explore a related service |
| Contact and Schedule | `/contact` | `contact.html` | Support scheduling, discovery calls, corporate inquiries, and newsletter consent | Schedule a Session |

## Page Relationships

### Home

Home should link directly to:

- About Lisa
- Services
- Reiki and Energy Healing
- Akashic Records
- Meditation
- Work Trauma Coaching
- Corporate Wellness
- Reflections
- Selected Healer Next Door articles
- Contact and Schedule

### Services

Services should link directly to all five service pages:

1. Reiki and Energy Healing
2. Akashic Records
3. Meditation
4. Work Trauma Coaching
5. Corporate Wellness

Services should also link to Contact through the “Help Me Choose” path.

### Consumer Service Pages

Reiki, Akashic Records, Meditation, and Work Trauma Coaching should each link to:

- About Lisa for credentials and founder fit
- Contact and Schedule for conversion
- Reflections for client trust
- Two to four relevant Healer Next Door articles
- One related service only when the relationship is useful to the visitor

Do not create loops of generic “learn more” links between every service.

### Corporate Wellness

Corporate Wellness should link to:

- About Lisa for professional credibility
- Contact for the corporate inquiry route
- Meditation where organizational mindfulness is relevant
- Work Trauma Coaching only when discussing workplace stress or culture repair
- Evidence or resources that directly support the organizational offer

### About Lisa

About Lisa should link to:

- Services
- Lisa's directly relevant service pages
- Verified interviews and external media
- Healer Next Door
- Contact and Schedule

### Reflections

Reflections should link to:

- Help Me Choose on Contact
- Relevant service pages when a testimonial can be accurately associated with a service
- Schedule a Session

Do not alter testimonial meaning to manufacture these associations.

### Resources

Resources should link to:

- Healer Next Door
- Topic-filtered article groups
- Relevant services
- Newsletter signup
- Contact and Schedule

### Healer Next Door

The hub should link to:

- Featured and recent articles
- Topic filters
- Newsletter signup
- Relevant service pages
- About Lisa

Each legacy article may receive a contextual related-service link, but its title, slug, canonical, body, authorship, date, and images must remain preserved.

### Contact and Schedule

Contact should provide four distinct pathways:

1. Schedule a service
2. Request a discovery call
3. Plan a workplace program
4. Join the newsletter

The scheduler should reflect service categories. Virtual delivery should appear as an option within a service, not as a competing service category.

## Service and Search Ownership

| Page | Primary search ownership | Supporting topics |
|---|---|---|
| Reiki and Energy Healing | Reiki Montclair NJ; Reiki near me; Reiki healing; energy healing NJ | Virtual Reiki; complementary support; energy work |
| Akashic Records | Akashic Records reading; Akashic reading; virtual Akashic reading | Intuition; recurring patterns; ancestral healing as reflective spiritual exploration |
| Meditation | Meditation Montclair NJ; meditation classes near me; guided meditation | Mindfulness classes; virtual meditation; meditation and Reiki |
| Work Trauma Coaching | Workplace trauma coaching; toxic workplace recovery; workplace stress coaching | Burnout support; layoffs; professional identity loss |
| Corporate Wellness | Corporate mindfulness workshops; corporate meditation; corporate wellness NJ | Employee well-being; workplace stress support; leadership and team programs |
| Healer Next Door | Long-tail educational and reflective queries | Reiki, meditation, spiritual growth, intuition, energy healing, work and burnout |

Pages should not compete for another page's primary keyword cluster. Supporting references should link to the page that owns the topic.

## Regional SEO Structure

Use one concise regional service-area module on relevant service pages.

Approved behavior:

- Name Montclair, New Jersey naturally.
- Mention in-person and virtual availability only where confirmed.
- Refer broadly to Northern New Jersey without listing many cities.
- Adapt the module to the page's service.
- Keep the module useful to visitors, not written only for search engines.

Not approved:

- Separate city landing pages
- Repetitive location blocks
- Doorway pages
- Lists of nearby towns inserted for keyword coverage

City pages may be reconsidered only after clean Search Console data shows distinct demand and enough unique local content exists.

## Editorial and Legacy SEO Structure

### Canonical editorial hub

`/healernextdoor`

### Preserved article pattern

`/healernextdoor/{existing-slug}`

### Migration requirements

- Preserve all 253 migrated article pages.
- Preserve every established article slug and canonical URL.
- Preserve article body copy, authorship, publication date, and local images.
- Do not move articles under `/resources`.
- Do not create a second blog hub.
- Do not rewrite legacy articles as part of the core website rewrite.
- Compare any future blog edit against `outputs/blog-migration-baseline.md` before implementation.
- Preserve taxonomy pages as consolidated `noindex, follow` routes where currently documented.
- Keep the legacy SEO archive as an internal migration reference, not a public conversion page.

## Supporting and Utility Routes

These routes sit outside the primary navigation. Preserve them for content, legal, event, scheduling, or migration purposes.

```text
/faq
/events
/events/{existing-event-slug}
/newsletter
/cancellationrefund-policy
/covid-policy
/get-started
/get-started/{existing-subroute}
/legacy-seo-archive          Internal/noindex migration reference
```

Do not rewrite, delete, merge, or redirect these routes without an implementation-level URL and content audit.

## Canonical and Filename Notes

Claude should write to canonical public routes, not treat local `.html` filenames as the preferred public URLs.

| Current file or label | Intended canonical route or behavior |
|---|---|
| `index.html` | `/` |
| `about-lisa.html` | `/about` |
| `services.html` | `/services` |
| `reiki-energy-healing.html` | `/reiki-energy-healing` |
| `akashic-records.html` | `/akashic-records` |
| New meditation file | `/meditation` |
| `work-trauma-coaching.html` | `/work-trauma` |
| `corporate-wellness.html` | `/corporate-wellness` |
| `success-stories.html` | Navigation label “Reflections”; canonical `/testimonials` |
| `resources.html` | `/resources` |
| `healernextdoor.html` | `/healernextdoor` |
| `contact.html` | `/contact` |

The implementation team will determine the exact hosting and redirect rules. Claude should identify route differences in a final canonical/redirect note but should not invent a new URL scheme.

## Footer Sitemap

### Practice

- Home
- About Lisa
- Services
- Reflections
- Contact

### Services

- Reiki and Energy Healing
- Akashic Records
- Meditation
- Work Trauma Coaching
- Corporate Wellness

### Learn

- Resources
- Healer Next Door
- FAQ
- Events, if active
- Newsletter

### Policies

- Cancellation and Refund Policy
- COVID Policy, if still active
- Privacy or consent policy, if supplied

### Conversion

- Schedule a Session
- Request a Discovery Call
- Plan a Workplace Program

## Sitemap Rules for Claude

1. Write pages in the core sitemap order.
2. Keep one clear purpose and one primary search intent per page.
3. Use the canonical route shown here in every page header and internal-link recommendation.
4. Use the navigation label “Reflections,” while preserving `/testimonials` as the planned canonical route.
5. Create complete copy for the new Meditation page.
6. Do not create additional service or city pages.
7. Do not rewrite or rename legacy articles.
8. Mark unsupported facts with `[VERIFY]` instead of filling structural gaps with invented information.
9. Keep Contact as the central scheduling and inquiry destination.
10. End the copy deliverable with a canonical and redirect note for the implementation team.
