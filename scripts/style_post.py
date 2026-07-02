#!/usr/bin/env python3
"""
Convert a fetched WordPress market post (content/raw/<id>-<slug>.json) into the
gold-standard izebuy layout (see Docs/design-spec.md).

For market posts the WORDS ARE LEFT EXACTLY AS THE WRITER WROTE THEM. The only
things this does are: remove junk shortcodes, convert [lwptoc] -> [toc], and
apply the house styling/structure. It never rewrites or invents text.

  - <h1>                       -> centred masthead (title)
  - [lwptoc] / [toc]           -> kept as the [toc] shortcode (renders on site)
  - Google Maps <iframe>       -> full-width map figure, kept in place
  - <h2>                       -> uppercase section header (a contents entry)
  - <h4>                       -> small-caps sub-heading
  - "<strong>Name</strong>: …" followed by an <img>  -> an item card (2-col grid)
  - "<strong>Name</strong>: …" with no image          -> a bold-lead paragraph
  - "ABOUT THE AUTHOR" + photo + bio  -> the author block (kept only if present)
  - shortcodes: keep the whitelist, strip everything else

Output: content/styled/<id>-<slug>.html — a standalone preview with the
canonical stylesheet inlined so it renders exactly as WordPress will show it.
The publish step later posts just the inner <article> (with [toc] intact).

Usage:  python3 scripts/style_post.py content/raw/4458-mbayani-market.json [...]
        python3 scripts/style_post.py --all          # every market post
Stdlib only.
"""

import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "content", "raw")
OUT = os.path.join(REPO, "content", "styled")
CSS_PATH = os.path.join(REPO, "styles", "izebuy-post.css")

MARKET_IDS = {"4143", "4200", "4364", "4404", "4413", "4458"}

# Whitelisted shortcodes (Docs/design-spec.md, Docs/sessionexport.md). Everything
# else is stripped; [lwptoc] is converted to [toc].
WHITELIST = {"toc", "izebuy_socials", "izebuy_email", "izebuy_phone",
             "izebuy_address", "affiliate_disclosure"}

BLOCK_RE = re.compile(
    r"<h1[^>]*>(?P<h1>.*?)</h1>"
    r"|<h2[^>]*>(?P<h2>.*?)</h2>"
    r"|<h3[^>]*>(?P<h3>.*?)</h3>"
    r"|<h4[^>]*>(?P<h4>.*?)</h4>"
    r"|<p[^>]*>(?P<p>.*?)</p>"
    r"|(?P<ul><ul[^>]*>.*?</ul>)"
    r"|(?P<ol><ol[^>]*>.*?</ol>)"
    r"|(?P<iframe><iframe[^>]*>.*?</iframe>)"
    r"|<img(?P<img>[^>]*?)/?>",
    re.DOTALL | re.IGNORECASE,
)
STRONG_LABEL_RE = re.compile(r"^\s*<strong>\s*(?P<name>.*?)\s*</strong>\s*[:;]?\s*(?P<rest>.*)$",
                             re.DOTALL | re.IGNORECASE)


def text_only(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def collapse_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", text_only(s).lower()).strip("-") or "section"


def clean_shortcodes(content):
    # convert the old TOC plugin shortcode to ours
    content = re.sub(r"\[lwptoc[^\]]*\]", "[toc]", content, flags=re.I)
    # strip junk shortcodes together with any wrapped content
    content = re.sub(r"\[pricings\b[^\]]*\].*?\[/pricings\]", "", content, flags=re.S | re.I)
    content = re.sub(r"\[ads\b[^\]]*\].*?\[/ads\]", "", content, flags=re.S | re.I)
    content = re.sub(r"\[/?(?:pricings|ads)\b[^\]]*\]", "", content, flags=re.I)

    # strip any remaining shortcode that is not on the whitelist
    def keep(m):
        name = re.match(r"\[/?\s*([a-zA-Z0-9_]+)", m.group(0))
        return m.group(0) if name and name.group(1).lower() in WHITELIST else ""
    return re.sub(r"\[/?[a-zA-Z][^\]]*\]", keep, content)


def img_attrs(raw_attr):
    src = re.search(r'src="([^"]+)"', raw_attr)
    alt = re.search(r'alt="([^"]*)"', raw_attr)
    return (src.group(1) if src else ""), (alt.group(1) if alt else "")


def tokenize(content):
    blocks = []
    for m in BLOCK_RE.finditer(content):
        kind = m.lastgroup
        val = m.group(kind)
        if kind == "p":
            # a paragraph that is just an image (e.g. the author photo,
            # stored as <p><img></p>) should be treated as an image block
            only_img = re.fullmatch(r"\s*<img([^>]*?)/?>\s*", val, re.I)
            if only_img:
                src, alt = img_attrs(only_img.group(1))
                if src:
                    blocks.append(("img", (src, alt)))
                    continue
            blocks.append(("p", val))
        elif kind in ("h1", "h2", "h3", "h4"):
            blocks.append((kind, val))
        elif kind == "img":
            src, alt = img_attrs(val)
            if src:
                blocks.append(("img", (src, alt)))
        elif kind == "iframe":
            blocks.append(("iframe", val))
        elif kind in ("ul", "ol"):
            blocks.append((kind, val))
    return blocks


def is_card_label(kind, val):
    """A '<strong>Name: description</strong>' paragraph (a potential card/label),
    excluding the 'About the author' marker."""
    if kind != "p":
        return False
    lm = STRONG_LABEL_RE.match(val.strip())
    return bool(lm) and not text_only(val).lower().startswith("about the author")


def normalize_photo_captions(blocks):
    """Handle writers who put the PHOTO first and the 'Name: description' caption
    directly beneath it (image-above-caption) — the reverse of the usual
    label-then-photo order.

    When a run clearly follows that reversed pattern — IMG,LABEL,IMG,LABEL,...
    with at least two pairs, starting at a heading/paragraph boundary — each
    IMG,LABEL pair is reordered to LABEL,IMG so the normal pairing turns them
    into proper cards (instead of an orphan photo + a photo-less text label, or,
    worse, a label paired with the NEXT shop's photo). Requiring two alternating
    pairs keeps a lone section-intro photo (e.g. IMG then unrelated Q&A labels)
    from being mistaken for a caption pair."""
    def is_lbl(b):
        return is_card_label(*b)
    def is_img(b):
        return b[0] == "img"
    out = list(blocks)
    n = len(out)
    i = 0
    while i < n:
        boundary = (i == 0) or not (is_img(out[i - 1]) or is_lbl(out[i - 1]))
        pairs, j = 0, i
        while j + 1 < n and is_img(out[j]) and is_lbl(out[j + 1]):
            pairs += 1
            j += 2
        if boundary and pairs >= 2:
            for k in range(i, j, 2):
                out[k], out[k + 1] = out[k + 1], out[k]
            i = j
        else:
            i += 1
    return out


def figure_html(src, alt):
    cap = f"<figcaption>{html.escape(alt)}</figcaption>" if alt else ""
    return f'<figure><img src="{src}" alt="{html.escape(alt)}">{cap}</figure>'


def label_html(raw_name):
    """Bold label text for an item/service. raw_name is the inner HTML of
    <strong>...</strong>; the visible text is cleaned & escaped, but if the
    writer wrapped the label in a link we keep the link (don't drop it)."""
    text = collapse_ws(text_only(raw_name)).rstrip(":; ").strip()
    esc = html.escape(text, quote=False)
    href = re.search(r'<a\s[^>]*href="([^"]+)"', raw_name, re.I)
    return f'<a href="{html.escape(href.group(1))}">{esc}</a>' if href else esc


def item_card_html(label, rest, src, alt):
    # label is already safe HTML (see label_html); rest keeps its inline HTML
    # (links/entities) exactly as the writer wrote it.
    return ('<div class="izebuy-item"><figure>'
            f'<img src="{src}" alt="{html.escape(alt)}"></figure>'
            f'<div class="it-cap"><span class="it-name">{label}</span>'
            f'<span class="it-text">{rest}</span></div></div>')


def render_section_body(blocks):
    """Render the blocks inside one section, preserving all text.

    Item cards (a label + its photo) are kept CONTIGUOUS in one grid — an
    unlabelled photo never splits that grid. Loose photos are collected and
    emitted together *after* the grid (one -> a single figure, several -> a
    gallery), so shops/products stay in one clean 2-column grid instead of
    fragmenting around stray images.
    """
    out, grid, gallery = [], [], []
    pending = None   # a strong-labelled paragraph awaiting an image

    def flush_grid():
        if grid:
            out.append('<div class="izebuy-items">\n' + "\n".join(grid) + "\n</div>")
            grid.clear()

    def flush_gallery():
        # One loose photo stays a single large figure; a run of them becomes a
        # balanced gallery so image-heavy posts don't turn into a giant column.
        if len(gallery) == 1:
            out.append(figure_html(*gallery[0]))
        elif gallery:
            cells = "\n".join(figure_html(src, alt) for src, alt in gallery)
            out.append('<div class="izebuy-gallery">\n' + cells + "\n</div>")
        gallery.clear()

    def flush_media():
        # cards first (one contiguous grid), then any loose photos after them
        flush_grid(); flush_gallery()

    def flush_pending():
        nonlocal pending
        if pending:
            flush_media()      # cards/photos before this label are emitted first
            label, rest = pending
            out.append(f"<p><b>{label}</b>{(' ' + rest) if rest else ''}</p>")
            pending = None

    for kind, val in blocks:
        if kind == "img":
            src, alt = val
            if pending:                       # label + image = an item card
                name, rest = pending
                grid.append(item_card_html(name, rest, src, alt))
                pending = None
            else:                             # no label: a loose photo, held so
                gallery.append((src, alt))    # it can't split the item grid
            continue

        if kind == "iframe":                  # the Google map, kept in place
            flush_pending(); flush_media()
            # drop width/height and the leftover sprintf placeholders
            # (title="%3$s" / aria-label="%3$s") which can fatal a PHP plugin on save
            ifr = re.sub(r'\s(?:width|height|title|aria-label)="[^"]*"', "", val)
            ifr = ifr.replace("<iframe",
                              '<iframe title="Location map" loading="lazy" '
                              'style="width:100%;height:380px;border:1px solid"', 1)
            out.append(f'<figure class="izebuy-map">{ifr}</figure>')
            continue

        # a strong-labelled paragraph is a *potential* card — hold it, don't
        # break the grid, until we know whether an image follows.
        is_label = False
        if kind == "p":
            lm = STRONG_LABEL_RE.match(val.strip())
            if lm and not text_only(val).lower().startswith("about the author"):
                is_label = True
        if is_label:
            flush_pending()
            pending = (label_html(lm.group("name")), collapse_ws(lm.group("rest")))
            continue

        # genuine non-card block: ends the run of cards/photos
        flush_pending(); flush_media()
        if kind == "h4":
            out.append(f"<h3>{html.escape(collapse_ws(text_only(val)), quote=False)}</h3>")
        elif kind in ("ul", "ol"):
            out.append(val.strip())
        elif kind == "p":
            inner = collapse_ws(val)
            if inner.strip().lower() == "[toc]":
                out.append('<nav class="izebuy-toc">[toc]</nav>')
            elif text_only(inner):
                out.append(f"<p>{inner}</p>")
    flush_pending(); flush_media()
    return "\n".join(out)


def extract_author(blocks):
    """Pull an 'About the author' photo + bio out of the blocks, if present."""
    for i, (kind, val) in enumerate(blocks):
        if kind == "p" and text_only(val).lower().startswith("about the author"):
            photo, bio, rest = "", "", []
            for k, v in blocks[i + 1:]:
                if k == "img" and not photo:
                    photo = v[0]
                elif k == "p" and not bio and text_only(v):
                    # some posts embed the author photo INSIDE the bio paragraph
                    # (<p><img ...>bio text</p>); pull it out so it becomes the
                    # round avatar figure instead of an inline image in the text.
                    if not photo:
                        mimg = re.search(r"<img[^>]*>", v, re.I)
                        if mimg:
                            src, _ = img_attrs(mimg.group(0))
                            if src:
                                photo = src
                    bio = collapse_ws(re.sub(r"<img[^>]*>", "", v))
                else:
                    rest.append((k, v))
            img = f'<figure><img src="{photo}" alt="Author photo"></figure>' if photo else ""
            author = ('<div class="izebuy-author">' + img +
                      f"<div><h2>About the Author</h2><p>{bio}</p></div></div>")
            return author, blocks[:i] + rest
    return None, blocks


def build_article(title, blocks, cover=None):
    intro, sections, current = [], [], None
    for kind, val in blocks:
        if kind == "h1":
            continue
        if kind == "p" and collapse_ws(val).strip().lower() == "[toc]":
            continue   # the TOC lives in the hero, not the body
        if kind == "h2":
            current = {"title": collapse_ws(text_only(val)), "blocks": []}
            sections.append(current)
        elif current is None:
            intro.append((kind, val))
        else:
            current["blocks"].append((kind, val))

    # NO cover image in the body: the WordPress theme already shows the post's
    # Featured Image at the top, so adding one here just duplicates it. The body
    # opens with the masthead title and the [toc] contents box.
    parts = [f"<h1>{title}</h1>",
             '<nav class="izebuy-toc">[toc]</nav>']
    if intro:
        parts.append(render_section_body(intro))
    for s in sections:
        parts.append(f'<h2 id="{slugify(s["title"])}">{html.escape(s["title"], quote=False)}</h2>')
        parts.append(render_section_body(s["blocks"]))
    return "\n".join(p for p in parts if p)


def convert(json_path):
    with open(json_path, encoding="utf-8") as f:
        post = json.load(f)
    title = collapse_ws(post.get("title") or "")
    content = clean_shortcodes(post.get("content_raw") or "")
    blocks = tokenize(content)
    blocks = normalize_photo_captions(blocks)
    author, blocks = extract_author(blocks)
    article = build_article(title, blocks, post.get("cover_image"))
    if author:
        article += "\n" + author
    return post, f'<article class="izebuy-post">\n{article}\n</article>'


def standalone(post, article):
    """Self-contained preview. [toc] can't run outside WordPress, so for the
    preview only we render a contents list from the H2s; the real post keeps
    the [toc] shortcode untouched."""
    with open(CSS_PATH, encoding="utf-8") as f:
        css = f.read()
    heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', article)
    toc_html = ('<p class="toc-title">Contents</p><ul>'
                + "".join(f'<li><a href="#{i}">{text_only(t).title()}</a></li>'
                          for i, t in heads) + "</ul>")
    preview = article.replace("[toc]", "<!-- [toc] shortcode -->" + toc_html)
    ph_css = (".ph{background:repeating-linear-gradient(45deg,#eee,#eee 14px,"
              "#e3e3e3 14px,#e3e3e3 28px);display:flex;align-items:center;"
              "justify-content:center;font:italic 13px Georgia;text-align:center;"
              "padding:10px;box-sizing:border-box;border:1px solid;min-height:120px;}")
    return (f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{html.escape(post.get('title',''))} — izebuy (styled preview)</title>\n"
            f"<style>\nbody{{margin:0;padding:40px 16px;}}\n{css}\n{ph_css}\n</style>\n</head>\n"
            f"<body>\n{preview}\n</body>\n</html>\n")


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    if argv == ["--all"]:
        argv = [os.path.join(RAW, fn) for fn in sorted(os.listdir(RAW))
                if fn.endswith(".json") and fn.split("-")[0] in MARKET_IDS]
    if not argv:
        sys.exit("Usage: style_post.py <raw/*.json> [...]  |  --all")
    for path in argv:
        post, article = convert(path)
        name = f"{post['id']}-{post['slug']}.html"
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(standalone(post, article))
        print(f"styled  {post['id']}  {post['title'][:46]:48}  -> content/styled/{name}")


if __name__ == "__main__":
    main(sys.argv[1:])
