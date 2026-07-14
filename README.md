# Enlightened Path Healing

Static website refresh for [Enlightened Path Healing](https://www.enlightenedpathhealing.com/), including the redesigned core experience and the preserved Healer Next Door archive used for SEO migration.

## Project structure

- `outputs/` - deployable website root
- `outputs/assets/` - production images, fonts, and licensed social SVGs
- `outputs/healernextdoor/` - migrated legacy article archive
- `scripts/` - migration, extraction, sitemap, and QA utilities
- `.local/site-map.html` - generated local-only sitemap and action-item view; intentionally ignored by Git
- `LOCAL-QA.md` - local sitemap and hot-pink action-item conventions
- `google-sheets-discovery-call-setup.md` - discovery-call form integration steps

## Local preview

The site can be opened directly from `outputs/index.html`. A local server gives more reliable relative-link behavior:

```powershell
py -m http.server 8000 --directory outputs
```

Then open `http://localhost:8000/`.

## Quality checks

Install the one audit dependency and run both checks before a release:

```powershell
py -m pip install -r requirements-dev.txt
py scripts/audit_core_site.py
py scripts/audit_blog_migration.py
```

The core audit also regenerates `.local/site-map.html`. The current site has two intentionally visible hot-pink launch actions: replace the ancestral-healing placeholder and connect the discovery-call form to its Google Sheets endpoint.

## Deployment

Publish the contents of `outputs/` as the site root. The folder already contains `_redirects` for Netlify-style hosts and `.htaccess-legacy-redirects.txt` for Apache hosts. On Apache, rename that file to `.htaccess` during deployment.

Before pointing the live domain at the new build:

1. Complete every hot-pink action item listed in `.local/site-map.html`.
2. Run both QA scripts and resolve all errors.
3. Confirm the Acuity embed, discovery-call form, and newsletter signup in the production environment.
4. Verify legacy redirects and canonical URLs against `outputs/blog-migration-map.csv` and `outputs/legacy-seo-inventory.csv`.
5. Submit `outputs/sitemap.xml` in Google Search Console after launch.

## GitHub setup

This workspace is initialized as a Git repository. To publish it to a new GitHub repository, create an empty repository on GitHub and run:

```powershell
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

The GitHub Actions workflow in `.github/workflows/site-qa.yml` runs the core-site and blog-migration audits on every push and pull request.

## Asset note

The social icons under `outputs/assets/icons/social/` are derived from a client-supplied, licensed Adobe Stock EPS. The extraction script preserves the purchased vector geometry and applies the Enlightened Path Healing plum. Do not redistribute the original stock source independently of its license.

All site content and brand assets are proprietary to Enlightened Path Healing unless otherwise noted.
