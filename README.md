# blog_post_styler

Tooling and documentation for **izebuy Markets** — turning plain Microsoft Word
market write-ups into clean, fast, newspaper-style HTML that gets published to a
WordPress site, plus the field method and writer guidance behind it.

## What this project is for

1. **Blog post styler.** A writer hands in a plain Word `.docx` (written to our
   brief, using Word Heading styles). A script turns it into a single block of
   static HTML + scoped CSS — no page builder, no JavaScript — ready to paste or
   post into WordPress.
2. **Writer guidance.** How we tell writers to structure their documents so the
   script can do its job.
3. **Market mapping system.** The field method writers follow when they go out to
   map a market in Malawi.

## Folder layout

| Folder | Contents |
| --- | --- |
| `Docs/` | The written specs and guidance (see below). |
| `scripts/` | Tooling: `fetch_posts.py` (pull posts), `style_post.py` (apply the design), `publish_posts.py` (write styled posts back as drafts/updates). |
| `.github/workflows/` | GitHub Actions: `fetch-posts.yml` and `publish-posts.yml` (run from GitHub, which can reach the site even though the Claude sandbox can't). |
| `content/` | `raw/` fetched posts, `styled/` generated previews, `backup/` originals saved before publishing. |
| `styles/` | `izebuy-post.css` — the canonical scoped stylesheet (the locked "gold standard" design, structure only, no colour). |
| `examples/` | The test-fixture article (`.docx`) and its styled HTML output. Used to develop and verify the generator. |
| `mockups/` | Design mockups / prototypes of the styled post layout. |

### `Docs/`
- **`02writersbrief.docx`** — the izebuy Markets Writer's Brief (latest version).
  This is what writers are given.
- **`izebuymarketwritersbrief.md`** — the writer's brief in Markdown. *Note: this
  is an earlier wording ("What we're doing…") than the `.docx` above ("This is a
  commission…"). Kept as the editable Markdown source; reconcile the two when
  convenient.*
- **`design-spec.md`** — **the single source of truth** for how every post must
  look (gold standard, no colour, hero with cover image, shortcode whitelist,
  article skeleton). Consolidated — there is only one design instructions doc.
- **`marketmappingmethod.md`** — how izebuy maps a market (the field method).
- **`reformatting-plan.md`** — plan + status for reformatting the existing live posts into the house style.
- **`setup-credentials.md`** — how to create the WordPress Application Password and add the GitHub secrets the tooling needs.

### `examples/`
- **`01examplearticlembayani.docx`** — the Mbayani example article (test fixture).
- **`01examplearticlembayani.html`** — its styled HTML output.

### `mockups/`
- **`mbayanimockup.html`**, **`mbayanimockupv2.html`**, **`mbayanimockupv3.html`** —
  progressive design mockups (v3 is newest).
- **`howitworkscontent.html`** — "how it works" content page.

## Status

Early scaffolding. The generator script itself is not built yet — see
`Docs/03generatorbuildprompt.md` for the spec and `examples/` for the fixture.
