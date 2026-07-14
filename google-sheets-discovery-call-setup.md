# Discovery Call Form to Google Sheets

The contact page form is already wired for a Google Apps Script endpoint. It posts email, newsletter opt-in, source, page URL, page title, and user agent.

## Setup

1. Create a Google Sheet for Enlightened Path Healing leads.
2. Open `Extensions > Apps Script`.
3. Paste the contents of `google-sheets-discovery-call-apps-script.js` into `Code.gs`.
4. Save the project.
5. Deploy with `Deploy > New deployment > Web app`.
6. Set `Execute as` to `Me`.
7. Set `Who has access` to `Anyone`.
8. Copy the Web App URL.
9. In `outputs/contact.html`, paste that URL into the contact form:

```html
data-sheet-endpoint="PASTE_WEB_APP_URL_HERE"
```

10. Submit a test email from the contact page and confirm rows appear in:

- `Discovery Calls`
- `Newsletter Opt Ins`, only when the opt-in checkbox is selected

## Notes

- Until the endpoint is added, the form falls back to a prefilled email to `lisa@enlightenedpathhealing.com`.
- The checkbox records newsletter consent separately so the client can import opt-ins into their email platform.
- The form uses `no-cors` so it can post from a static site without adding server-side code.
