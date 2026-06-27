# Build prompt — izebuy Markets blog HTML generator

> Paste this as the first message in a new Claude Code session, **inside the new,
> empty repository** you've created for this generator. Attach the file
> `01-example-article-mbayani.docx` to that session — it is the test fixture.

---

## What I want you to build

A small command-line tool that turns a **plain Microsoft Word `.docx`** market
write-up into a **single block of clean, static HTML** (plus one scoped stylesheet)
that I can paste straight into the WordPress post editor. No WordPress, no database,
no JavaScript in the output — just HTML and CSS. The point is to skip page builders
(we removed Elementor and OrbitFox for being heavy) and produce fast, consistent,
newspaper-style posts from a Word file.

This repository is standalone. Do **not** assume any WordPress code is present.

## The pipeline, end to end

1. **Input:** a `.docx` written to our writer's brief. Section structure comes from
   Word **Heading styles** (Heading 1 = title, Heading 2 = section, Heading 3 = zone
   inside the walk-through). Body text is normal paragraphs.
2. **Images:** in the `.docx`, each image position is marked by a paragraph that
   begins `Photo — <filename> · "<caption>"` (see the fixture). Treat that marker as
   the source of truth for **where** an image goes, its **filename**, and its
   **caption** — do not rely on the embedded image binary or its internal name.
   The real photo files are uploaded separately to the WordPress media library; in
   the output, emit `<img>` tags whose `src` is a **placeholder URL** built from the
   filename (e.g. `{{MEDIA_URL}}/lsm-general-dealers.jpg`) that I can find-and-replace,
   OR accept a `--media-base` argument to set the base URL. The **cover** image
   (filename = the market name) is NOT placed in the body — it is the WordPress
   Featured Image, so output its URL separately (e.g. printed to stdout / a sidecar
   file), not inside the HTML.
3. **Sanitise** (this is critical — there is no human moderation):
   - Strip **all** raw HTML tags, `<script>`, `<style>`, inline styles, tables, text
     boxes, and any formatting that isn't plain text, headings, paragraphs, bold, or
     links.
   - **Shortcodes:** allow ONLY this whitelist, and strip every other shortcode
     entirely (including `[pricings]`, `[ads]`, and anything unknown):
     - `[toc]`, `[izebuy_socials]`, `[izebuy_email]`, `[izebuy_phone]`,
       `[izebuy_address]`, `[affiliate_disclosure]`
   - **Convert** the old `[lwptoc]` shortcode to `[toc]`.
   - Make the whitelist a single, clearly-commented constant at the top so I can add
     to it later when we install a new plugin.
4. **Assemble** the HTML to the layout rules below.
5. **Output:** write an `.html` file (the body fragment, wrapped in
   `<article class="izebuy-post">…</article>`) and a separate `izebuy-post.css`.
   Print the Featured Image URL and a list of every media filename the post expects,
   so I know what to upload.

## Layout rules (the design is already agreed — match it exactly)

Everything is scoped under `.izebuy-post`. **CSS must be structure only — layout,
spacing, borders/rules, image sizing. NO colour declarations of any kind** (no
`color`, `background`, coloured borders): the live site supplies all colour through
design tokens. Use borders/rules for the newspaper feel but leave their colour to
inherit.

- **H1** → centred masthead, uppercase, with a **double underline** (e.g.
  `border-bottom: 8px double`). It is placed from the title; ignore any H1 in the body.
- **Hero row** directly under H1: the **`[toc]`** shortcode on the left, the
  **featured image** on the right. Stacks on mobile.
- **H2** → uppercase section header with a single rule under it. Each H2 is a TOC entry.
- **H3** → small-caps sub-heading with a left rule bar (used for walk-through zones).
- **Images are the content — render them LARGE, never thumbnails.**
  - In a **text-heavy** section (lots of text, one image), the image **floats** and
    the text **wraps** around it (newspaper style), ~420px wide.
  - In a section that is **a little text per image** (shops, products), render each
    image as a **large card (~500px wide)** with its name/caption **below** it, laid
    out in a **fixed-column grid, two across**.
  - **Never stretch a lone image full-width.** Use a fixed-column grid so a leftover
    third image keeps its column width and sits on the left — it does not stretch
    end to end. A very image-heavy section may use three fixed columns.
  - An image must stay welded to the text that describes it (matched by the
    `Photo —` marker's position and its filename vs. the nearest heading / bold label).
- **Bullet lists** → one consistent styled list (used for services, tips, etc.).
- **About the Author** = the **last heading and everything beneath it**: lift it into
  its own box at the foot, author photo beside the bio. (There is **no** offer/CTA
  block — ignore any notion of one.)
- **Mobile:** everything stacks in document order and reads as a plain post.

## Tech notes

- Python is fine; `python-docx` reads heading styles and paragraph text well. Note
  that `python-docx` does **not** preserve original image filenames, which is exactly
  why we use the `Photo — <filename>` marker convention instead.
- Keep it a single, well-documented script with the whitelist and the layout
  dimensions as constants at the top, so I can re-skin later by editing one file.
- Add a `--media-base` flag (default `{{MEDIA_URL}}`).

## Acceptance test

Run the tool on the attached `01-example-article-mbayani.docx` and confirm:
- The title becomes the masthead; the cover image is reported as the Featured Image
  and is **not** in the body.
- The `[toc]` sits beside the featured image; every H2 is a contents entry.
- The "walk through" H3 zones render with large images welded to their captions.
- The shops render as large two-across cards with name + hours under each photo, and
  **no image is stretched full-width**.
- `[pricings]` / `[ads]` and any stray tags are gone; the whitelisted shortcodes
  remain; `[lwptoc]` (if present) became `[toc]`.
- The author section is lifted into its own foot box.
- The emitted CSS contains **no colour declarations**.
- Open the HTML in a browser (with the CSS) and eyeball it against the agreed
  newspaper design.

## Deliverables in that repo

1. The generator script.
2. `izebuy-post.css` (colourless, token-friendly, scoped to `.izebuy-post`).
3. A short `README.md`: how to run it, the naming conventions, how to add a shortcode
   to the whitelist, and the find-and-replace / `--media-base` step for image URLs.
4. The example `.docx` checked in as a test fixture, with the generated HTML/CSS
   committed beside it so I can see the expected output.
