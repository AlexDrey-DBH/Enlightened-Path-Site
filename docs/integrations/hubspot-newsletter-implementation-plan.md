# HubSpot Newsletter Implementation Plan

## Decision

HubSpot will be the only newsletter platform and subscriber system. The website will not create or maintain a separate subscriber database.

Implementation begins after the HubSpot account, subscription types, and forms exist. Until then, the current newsletter integration must be treated as a launch blocker rather than replaced with another temporary endpoint.

## HubSpot Structure

Create two distinct email subscription types:

1. **General Newsletter** - the default audience for the homepage newsletter form, the `/newsletter` form, and an explicitly checked newsletter opt-in on another website form.
2. **Event Updates** - used only by the signup form on `/events`.

Use separate HubSpot forms for the two subscription types:

- **General Newsletter Signup**: embedded on the homepage and `/newsletter`.
- **Event Updates Signup**: embedded only on `/events`.

The event form should also set a stable source value such as `website_events_page` so reporting can distinguish the page and form source in addition to the subscription type.

## Consent Rules

- Newsletter checkboxes remain unchecked by default.
- Submitting a discovery-call or service inquiry form does not imply newsletter consent.
- Only an explicitly checked newsletter checkbox may subscribe that person to the General Newsletter.
- A General Newsletter subscription must not automatically subscribe someone to Event Updates.
- An Event Updates subscription must not automatically subscribe someone to the General Newsletter.
- Existing unsubscribed contacts must remain unsubscribed.
- Do not send an opt-in or confirmation request to anyone whose existing status is unsubscribed.
- Preserve available consent source, consent date, form source, and subscription status during migration.

HubSpot subscription types represent the legal basis for email communication and maintain separate subscribed, unsubscribed, and not-specified states. See [HubSpot: Set up email subscription types](https://knowledge.hubspot.com/marketing-email/set-up-email-subscription-types).

## Existing Subscriber Migration

1. Export the existing subscriber list with email address, subscription status, signup source, signup date, and any available consent evidence.
2. Split the export into active subscribers, unsubscribed contacts, and records with unknown or unverified consent.
3. Import the unsubscribed addresses first using HubSpot's dedicated opt-out import. This prevents those addresses from being treated as eligible recipients. See [HubSpot: Import opted-out contacts](https://knowledge.hubspot.com/marketing-email/import-an-opt-out-list).
4. Import active subscribers only when their consent can be tied to Enlightened Path Healing. Map the original source and signup date where available.
5. Keep unknown or unverified records as not specified. Do not mark them subscribed merely because they were present in an old export.
6. Compare the imported totals and sample records against the source export before sending any campaign.
7. Keep the original export in a restricted administrative archive, not in the public website repository.

HubSpot requires verifiable permission for marketing email and states that lack of an opt-out is not equivalent to consent. See [HubSpot: Understand opt-in consent for email](https://knowledge.hubspot.com/marketing-email/understand-opt-in-consent-for-email).

## Website Integration

Use HubSpot's embedded forms rather than submitting directly through the Forms API. This allows HubSpot's native form validation, spam detection, and CAPTCHA configuration to remain available.

For each form:

- Add the website domain to HubSpot's tracked site domains.
- Enable HubSpot CAPTCHA in the form editor.
- Keep the email field required.
- Configure a clear in-place success message.
- Configure a clear validation or submission error message.
- Preserve keyboard access, visible labels, status announcements, and focus behavior.
- Keep a non-JavaScript fallback link to the corresponding HubSpot-hosted form if available.
- Test successful submission, invalid email, blocked/spam submission, duplicate subscriber behavior, and the fallback link.

HubSpot forms include automatic spam detection and can use invisible reCAPTCHA v2. HubSpot notes that CAPTCHA-enabled forms should not be submitted through the Forms API or another form integration. See [HubSpot: Prevent and filter spam in form submissions](https://knowledge.hubspot.com/forms/prevent-spam-form-submissions).

## Routing Acceptance Tests

- Homepage general signup appears in the General Newsletter audience only.
- `/newsletter` signup appears in the General Newsletter audience only.
- `/events` signup appears in Event Updates only and records the events-page source.
- An unchecked newsletter box creates no newsletter subscription.
- A checked newsletter box on another form creates only a General Newsletter subscription.
- A previously unsubscribed address remains unsubscribed after every form and import test.
- Each form displays the approved success and error states.
- CAPTCHA and HubSpot spam filtering are active.
- No Squarespace newsletter endpoint, Google Sheets newsletter endpoint, temporary endpoint, or developer setup message remains before launch.

## Values Required From the HubSpot Account

- HubSpot portal ID
- General Newsletter form ID
- Event Updates form ID
- General Newsletter subscription type ID
- Event Updates subscription type ID
- Hosted fallback URL for each form, if enabled
- Approved success and error copy
- Confirmation of whether double opt-in is enabled

After these values are supplied, replace the existing newsletter forms, test routing in HubSpot, and remove the former Squarespace form-submission code from `site.js` before launch.
