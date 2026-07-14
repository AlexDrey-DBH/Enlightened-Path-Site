# Local QA Sitemap and Action Items

The development sitemap is generated at `.local/site-map.html`. The `.local` directory is ignored by Git and sits outside the deployable `outputs` directory.

## Updating the Sitemap

Run either command after adding, renaming, or removing pages:

```powershell
python scripts/generate_local_sitemap.py
python scripts/audit_core_site.py
```

The core-site audit regenerates the local sitemap automatically. It inventories every HTML page under `outputs`, groups the legacy archive, and reports open action items.

## Marking Action Items

Any unfinished visual, integration, or content task must remain visibly hot pink until it is resolved:

```html
<div
  class="action-item"
  data-action-item="Replace with the approved photograph"
>
  Image placeholder
</div>
```

The shared stylesheet supplies the hot-pink outline and action label. The local sitemap reads `data-action-item`, lists the page in its action register, and includes the action text. Remove both attributes only when the work is complete.

HTML comments using `<!-- ACTION: description -->` also appear in the local action register, but visible page work should use the hot-pink element treatment above.
