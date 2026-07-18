# Enlightened Path Healing

The production website lives directly in this repository root. It is a static site deployed to GitHub Pages from the `main` branch.

## Production structure

- `index.html` and root HTML files: primary pages
- `assets/`: production images, fonts, and licensed social icons
- route folders such as `about/`, `healernextdoor/`, and `events/`: legacy and SEO-preserved URLs
- `styles.css` and `site.js`: shared site styling and behavior
- `sitemap.xml`, `robots.txt`, `_redirects`, and `CNAME`: search and deployment configuration
- `docs/`: non-production strategy, migration, QA, integration, and maintenance material

## Local preview

```powershell
py -m http.server 8000
```

Open `http://localhost:8000/`.

## GitHub Pages deployment

The GitHub Actions workflow at `.github/workflows/deploy-pages.yml` deploys each push to `main`. It publishes only the public website files, excludes `docs/`, `samples/`, and `tmp/`, and creates current static copies for the site's clean canonical URLs.

In GitHub, open `Settings` > `Pages`, set the source to `GitHub Actions`, and set the custom domain to `enlightenedpathhealing.com`. Enable HTTPS after GitHub verifies the domain.

The root `CNAME` file contains the public domain. At the DNS provider, point the apex domain and `www` subdomain to GitHub Pages using the values GitHub displays in the Pages settings.

## SEO preservation

The full Healer Next Door archive remains in `healernextdoor/`, including legacy taxonomy routes and local image assets. Migration records and audits are retained under `docs/migration/` for reference, but are not published as website files.

## Asset note

The social icons in `assets/icons/social/` are derived from a client-supplied, licensed Adobe Stock EPS. Do not redistribute the original stock source independently of its license.
