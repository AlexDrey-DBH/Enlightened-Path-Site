# Free Blog Publisher

This Cloudflare Worker provides the private client dashboard that creates blog source records and featured images in GitHub. GitHub Pages then builds the article and every discovery surface.

## What Publishing Updates

- Full article page
- SEO title and description
- Canonical URL
- Open Graph article and image metadata
- `BlogPosting` structured data
- XML sitemap
- Main Blog archive
- Matching topic archive
- Homepage latest-blog section
- Card excerpt from the article's opening sentence

## Free-Plan Behavior

The client can prepare drafts with a planned date and time. At that time, the client signs in and chooses **Publish Now**. Exact unattended scheduling is intentionally not part of the free workflow.

Images are limited to 1 MB to keep the GitHub upload within the Cloudflare Workers Free CPU allowance.

## One-Time Deployment

From this directory:

```powershell
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put PUBLISHER_PASSWORD
npx wrangler deploy
```

`GITHUB_TOKEN` must be a fine-grained GitHub token scoped only to `AlexDrey-DBH/Enlightened-Path-Site`, with repository **Contents: Read and write** permission. Never place either secret in this repository or send it by email.

After deployment, use the `workers.dev` URL shown by Wrangler. Changing the publisher password or GitHub token is done by running the matching `wrangler secret put` command again.
