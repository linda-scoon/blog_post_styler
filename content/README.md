# content/

Blog posts fetched from the live izebuy WordPress site land here. This folder is
populated by `scripts/fetch_posts.py` (run directly or via the **Fetch blog
posts from WordPress** GitHub Action).

- `raw/<id>-<slug>.json` — selected fields for each post, including the **raw**
  (unprocessed) post content.
- `raw/<id>-<slug>.html` — just the raw content HTML, for easy reading/diffing.
- `index.json` / `index.md` — a summary of everything fetched, with flags for
  posts that look empty or Elementor-built.

Nothing here is written by hand — re-run the fetch to refresh it.
