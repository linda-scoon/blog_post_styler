# izebuy Blog Post — Design Spec (the single source of truth)

**This is the one and only instructions document for how a blog post must look.**
(It replaces the old `sessionexport.md` and `03generatorbuildprompt.md`, which
were consolidated here.) Locked to the **"gold standard"** design
(`examples/01examplearticlembayani.html`); the canonical stylesheet is
`styles/izebuy-post.css`.

## Hard rules

- **No colour**, with ONE deliberate exception: the About-the-author box has a
  light neutral background so it reads as a proper card. Everything else inherits
  black text/borders; the live theme supplies colour through its design tokens.
- **Everything scoped to `.izebuy-post`** so it can't affect the rest of the site.
- **Images render large** — they are the content, never thumbnails.
- **Market posts: the writer's words are never changed.** When restyling an
  existing market post we only strip junk shortcodes and apply styling — no
  rewriting, no inventing sections.
- **About-the-author block is conditional** — included **only if the post already
  has author info**. Never invent one.

## Structure model

| Element | Role | Style |
| --- | --- | --- |
| `H1` | Post title → centred masthead | uppercase, letter-spaced, **double underline**. From the title; any body H1 is ignored. |
| **Hero row** | Contents + cover image | `.izebuy-hero` > `nav.izebuy-toc` ( `[toc]` ) + `figure.izebuy-featured` (cover). See below. |
| `H2` | Main section header | uppercase, single rule. **Each H2 is a contents entry.** |
| `H3` | Sub-heading / zone | small-caps, left rule. |
| `p` | Body text | normal paragraphs |

### The hero row (cover image + contents)

- **Desktop:** the **contents box is on the LEFT**, the **cover image on the
  RIGHT**.
- **Mobile:** they stack, and the **cover image comes ABOVE the contents**.
- The **cover image is the post's WordPress Featured Image** (filename = the
  market name). The generator places it in the hero; if its URL isn't known yet
  it leaves a marked placeholder.

## Components

- **Item grid** — `.izebuy-items` (two-column grid) of `.izebuy-item` cards for
  shops/products. Each card: `figure > img`, then `.it-cap` with `.it-name` (bold,
  own line) and `.it-text` beneath. **No leading colon** before the description.
- **Bold-lead items** (a labelled item with no photo, e.g. services) → a paragraph
  `<p><b>Name</b> description</p>` — again **no colon** after the name.
- **The map** — `figure.izebuy-map`, full content width, kept where the writer put
  it (existing posts embed a Google map; that's fine).
- **Floated figures** — `.izebuy-figR` / `.izebuy-figL` (420px) for text-heavy
  sections where text wraps the image. Follow with `<div class="clear"></div>`.
- **Bulleted list** — `ul.izebuy-bullets` (custom "›" marker).
- **"Golden nugget"** — an inline tip, `<b>Golden nugget:</b>` leading a paragraph.
- **About-the-author** — `.izebuy-author`: a **small, centred card** (max ~560px,
  not full width) with the author photo (round), a light neutral background, and
  rounded border. Conditional (see hard rules).

## Shortcodes

- **Keep (whitelist):** `[toc]`, `[izebuy_socials]`, `[izebuy_email]`,
  `[izebuy_phone]`, `[izebuy_address]`, `[affiliate_disclosure]`.
- **Convert** `[lwptoc]` → `[toc]`.
- **Strip** `[pricings]`, `[ads]`, and any other unknown shortcode.

## Images (for new posts written from a `.docx`)

Each image's position is marked in the source `.docx` by a paragraph:

```
Photo — <filename> · "<caption>"
```

That marker is the source of truth for **where** the image goes, its **filename**,
and its **caption**. Real photos live in the WordPress media library; the output
`<img>` `src` points there.

## Article skeleton (the writer's content model)

The fixed H2 order every market write-up follows (see the writer's brief,
`izebuymarketwritersbrief.md`, for the full instructions):

1. *Opening* (no heading) — what & where, 2–3 lines
2. Getting to [Market] from [nearest big town]
3. The feel of the place
4. What's around the market
5. What [Market] is famous for
6. **Walking the market** — the centrepiece
7. Shops, services & opening hours
8. Practical tips
9. Our honest take (no star ratings)
10. About the Author (last) — conditional
