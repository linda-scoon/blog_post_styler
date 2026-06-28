# izebuy Blog Post — Design Spec (house style)

The single source of truth for how every blog post must look. Locked to the
**"gold standard"** design (`examples/01examplearticlembayani.html`). The
canonical stylesheet is `styles/izebuy-post.css`.

## Hard rules

- **No colour.** The generator emits structure only — no colour declarations,
  ever. Text and borders inherit black; the live theme supplies any colour
  through its own design tokens.
- **Everything scoped to `.izebuy-post`** so it cannot affect the rest of the site.
- **Images render large** — they are the content, never thumbnails.
- **About-the-author block is conditional** — include it **only if the source
  post already has author information**. Never invent one.

## Structure model

Section structure comes from heading levels:

| Element | Role | Style |
| --- | --- | --- |
| `H1` | Post title → centred masthead | uppercase, letter-spaced, **double underline**. Set from the post title; any H1 in the body is ignored. |
| Hero row | `[toc]` contents (left) + featured image (right) | `.izebuy-hero` > `.izebuy-toc` + `figure.izebuy-featured` |
| `H2` | Main section header | uppercase, single rule. **Each H2 is a contents entry.** |
| `H3` | Zone inside the walk-through | small-caps, left rule. |
| `p` | Body text | normal paragraphs |

## Components

- **Floated figures** — `figure.izebuy-figR` / `.izebuy-figL` (420px) for
  text-heavy sections where the text wraps the image. Follow with `<div class="clear"></div>`.
- **The map** — `figure.izebuy-map`, full content width, the centrepiece of the
  walk-through section.
- **Item grid** — `.izebuy-items` (two-column grid) of `.izebuy-item` cards for
  shops/products. Each card: `figure > img`, then `.it-cap` with
  `.it-name` / `.it-text` / `.it-hours`.
- **Practical-tips list** — `ul.izebuy-bullets` (custom "›" marker).
- **"Golden nugget"** — an inline tip, emphasised with `<b>Golden nugget:</b>`
  at the start of a paragraph. Not a separate box, no colour.
- **About-the-author** — `.izebuy-author` (round avatar + bio). Conditional, see above.

## Images

Image positions come from a marker paragraph in the source `.docx`:

```
Photo — <filename> · "<caption>"
```

That marker is the source of truth for **where** an image goes, its
**filename**, and its **caption**. The real photo files live in the WordPress
media library; output `<img>` `src` points there.

## Shortcodes

- **Keep:** `[toc]` (or the site's TOC shortcode) — renders the contents box.
- **Strip:** everything else — leftover Elementor/page-builder shortcodes and
  any other `[...]` not on the keep-list.
