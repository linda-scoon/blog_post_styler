# izebuy Markets blog generator — session design log

A record of what we decided in this session, the documents produced, and what happens
next. Self-contained, so it can be read on its own or pasted into a new session.

---

## The goal
Replace the slow, tedious WordPress + Elementor/OrbitFox blogging process with a
**static HTML generator** living in a **separate git repo**. A writer hands in a plain
Word `.docx`; a script turns it into clean, fast, newspaper-style HTML (plus scoped CSS)
that gets pasted into WordPress. No page builder, no JavaScript in the output. The blog's
theme is mapping the markets of Malawi.

Was dropping Elementor + OrbitFox a good call? Yes — page builders add heavy DOM/CSS and
are a common cause of slow WordPress. Static HTML will be much faster. (Other speed
factors still matter: image sizes, caching, hosting.)

---

## Design decisions (locked)

**Page layout (newspaper style), all CSS scoped under `.izebuy-post`:**
- `H1` = centred masthead with a **double underline**. Placed from the post title; any
  H1 in the body is ignored.
- Hero row under H1: the `[toc]` shortcode on the left, the **featured image** on the right.
- `H2` = uppercase section header with a single rule; each H2 is a contents entry.
- `H3` = small-caps sub-heading with a left rule (used for the walk's zones).
- **Images render LARGE (they are the content), never thumbnails.** Text-heavy section →
  image floats and text wraps; little-text-per-image (shops/products) → large image cards
  with caption underneath, in a **fixed-column grid, two across**.
- **Never stretch a lone image full-width** — fixed columns; a leftover image keeps its
  column and sits on the left.
- Bullet lists → one consistent styled list.
- **About the Author** = the last heading + everything under it, lifted into its own foot
  box with the author's photo. There is **no offer/CTA block** (that was a dictation slip
  — "offer" meant "author").
- **CSS is structure only — NO colour declarations.** All colour comes from the site's
  design tokens.

**Input & images:**
- Input is a **plain `.docx`** (writers aren't technical). Section levels come from Word's
  **Heading styles**.
- Image filename = the item/heading it belongs to (e.g. `lsm-general-dealers.jpg`); the
  generator places each image with the text it describes.
- Photo positions are marked in the docx with a line: `Photo — <filename> · "<caption>"`
  (reliable, because python-docx discards original image filenames).
- Real photos are uploaded to WordPress media separately; the HTML uses placeholder/`--media-base`
  URLs. The **cover image** (named after the market) is the WP Featured Image, not in the body.

**Shortcodes (whitelist — strip everything else, plus all raw tags/scripts/styles):**
- Allowed: `[toc]`, `[izebuy_socials]`, `[izebuy_email]`, `[izebuy_phone]`,
  `[izebuy_address]`, `[affiliate_disclosure]`.
- Convert old `[lwptoc]` → `[toc]`. Strip `[pricings]`, `[ads]`, and anything unknown.
- (Whitelist taken from the registered shortcodes in the `izebuy-classifieds` theme/plugins.)

---

## The content model (the writer's brief)

Fixed article skeleton (the H2s every writer uses, in order):
1. *Opening* (no heading) — what & where, 2–3 lines
2. Getting to [Market] from [nearest **big town** — never the capital]
3. The feel of the place (weather, atmosphere — observable)
4. What's around the market (true, **witnessable** features: a stream, schools, the main
   road — replaces any invented "fun fact"; local history only if attributed)
5. What [Market] is famous for
6. **Walking the market** — the centrepiece (see mapping method)
7. Shops, services & opening hours
8. Practical tips
9. Our honest take (described value/cleanliness/safety — **no star ratings**; never accuse
   a named shop)
10. About the Author (last)

Tone: this is a **paid commission**, so the brief is **instructions, not advice** — no
"this will make your blog more visible," no "your article." SEO is folded in only as plain
writing instructions (use the market name + town naturally; answer real questions; spell
names right). ~2,000 words, from observed detail, not padding. No invented facts.

---

## The mapping method (researched)

Synthesised from: Google's "Ground Truth" process, Kevin Lynch's *Image of the City*
(paths / edges / districts / nodes / landmarks), wayfinding cognitive science (landmarks
at decision points beat left/right & compass — the one fully-verified research claim), and
Global-South informal mapping (Map Kibera; HOT Field Papers; pacing & timing; sketch maps).

Rule that falls out: **anchor to structure, not stock** — the mill, the tree, the painted
shop, never the traders or goods.

Writer procedure, in three parts (now in the brief):
1. **Map on the ground:** cover shot → walk the edge → find gates → name zones by trade →
   pick one *permanent* landmark per zone (never moves / visible / unique) → trace paths &
   note bends → pace + time each leg → photograph systematically.
2. **Write a map description (we draw the map; they don't):** describe from ONE viewpoint
   (entrance, looking in); use edges as the compass ("toward the road/stream") not left/right;
   state any bend; pin each landmark; give each time. Cover: shape & edges, entrances, zones,
   landmarks, paths, times.
3. **Write the guided walk:** first person, entrance → zone → zone, landmark-to-landmark,
   real timed legs, a golden nugget per zone, Heading 3 per zone.

**Maps are drawn by AI (Claude) as labelled SVG/vector diagrams** from the writer's
description — more accurate and legible than image generators for a schematic map. Proven
in-session with the Mbayani map.

---

## Documents produced this session
- `01-example-article-mbayani.docx` — gold-standard ~1,800-word example **and** the
  generator's test fixture.
- `01-example-article-mbayani.html` — the example rendered (colourless preview of the
  generator's output).
- `02-writers-brief.docx` — instructions for hired writers (with the mapping procedure and
  the worked map example embedded).
- `03-generator-build-prompt.md` — paste into the new repo's session to build the script.
- `market-mapping-method.md` — the research synthesis + 10-step field procedure (your
  reference; not for writers).
- `mbayani-map.svg` / `mbayani-map.png` — the AI-drawn example market map.

---

## Next steps
1. Create the new (separate) repo for the generator.
2. Start a new Claude Code session targeting that repo.
3. First message: paste `03-generator-build-prompt.md`; attach `01-example-article-mbayani.docx`.
4. The new session builds: the generator script, `izebuy-post.css` (colourless, scoped),
   a README, and the example fixture + expected output.

**Open items to decide:** where the map-drawing step lives (chat vs. part of the flow);
whether to require the `Photo —` marker line (recommended) vs. infer image placement;
whether to pad the example to a full 2,000 words.

---
*Note: nothing in this session was committed to the `izebuy-classifieds` repo — it was all
design work and handoff documents.*
