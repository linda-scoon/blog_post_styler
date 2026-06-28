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
STRONG_LABEL_RE = re.compile(r"^\s*<strong>\s*(?P<name>.*?)\s*</strong>\s*:?\s*(?P<rest>.*)$",
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


def render_section_body(blocks):
    """Render the blocks inside one section, preserving all text."""
    out, grid = [], []
    pending = None   # a strong-labelled paragraph awaiting an image

    def flush_grid():
        if grid:
            out.append('<div class="izebuy-items">\n' + "\n".join(grid) + "\n</div>")
            grid.clear()

    def flush_pending():
        nonlocal pending
        if pending:
            name, rest = pending
            out.append(f"<p><b>{name}</b>{(' ' + rest) if rest else ''}</p>")
            pending = None

    for kind, val in blocks:
        if kind == "img":
            src, alt = val
            if pending:                       # label + image = an item card
                name, rest = pending
                grid.append(
                    '<div class="izebuy-item"><figure>'
                    f'<img src="{src}" alt="{html.escape(alt)}"></figure>'
                    f'<div class="it-cap"><span class="it-name">{name}</span>'
                    f'<span class="it-text">{rest}</span></div></div>'
                )
                pending = None
            else:
                flush_grid()
                cap = f"<figcaption>{html.escape(alt)}</figcaption>" if alt else ""
                out.append(f'<figure><img src="{src}" alt="{html.escape(alt)}">{cap}</figure>')
            continue

        if kind == "iframe":                  # the Google map, kept in place
            flush_pending(); flush_grid()
            ifr = re.sub(r'\s(?:width|height)="[^"]*"', "", val)
            ifr = ifr.replace("<iframe",
                              '<iframe style="width:100%;height:380px;border:1px solid"', 1)
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
            name = collapse_ws(text_only(lm.group("name"))).rstrip(": ").strip()
            pending = (name, collapse_ws(lm.group("rest")))
            continue

        # genuine non-card block: ends any run of cards
        flush_pending(); flush_grid()
        if kind == "h4":
            out.append(f"<h3>{collapse_ws(text_only(val))}</h3>")
        elif kind in ("ul", "ol"):
            out.append(val.strip())
        elif kind == "p":
            inner = collapse_ws(val)
            if inner.strip().lower() == "[toc]":
                out.append('<nav class="izebuy-toc">[toc]</nav>')
            elif text_only(inner):
                out.append(f"<p>{inner}</p>")
    flush_pending(); flush_grid()
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
                    bio = collapse_ws(v)
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

    # Hero: contents (left) + cover image (right). The cover is the post's
    # WordPress Featured Image; if we don't have its URL yet, leave a marked
    # placeholder so the layout is visible.
    if cover:
        cover_fig = (f'<figure class="izebuy-featured">'
                     f'<img src="{html.escape(cover)}" alt="{html.escape(title)}">'
                     f"<figcaption>{html.escape(title)}</figcaption></figure>")
    else:
        cover_fig = ('<figure class="izebuy-featured">'
                     '<div class="ph" style="min-height:300px">Cover image — the '
                     f'WordPress Featured Image for &ldquo;{html.escape(title)}&rdquo;'
                     "</div></figure>")

    parts = [f"<h1>{title}</h1>",
             '<div class="izebuy-hero">',
             '<nav class="izebuy-toc">[toc]</nav>',
             cover_fig,
             "</div>"]
    if intro:
        parts.append(render_section_body(intro))
    for s in sections:
        parts.append(f'<h2 id="{slugify(s["title"])}">{s["title"]}</h2>')
        parts.append(render_section_body(s["blocks"]))
    return "\n".join(p for p in parts if p)


def convert(json_path):
    with open(json_path, encoding="utf-8") as f:
        post = json.load(f)
    title = collapse_ws(post.get("title") or "")
    content = clean_shortcodes(post.get("content_raw") or "")
    blocks = tokenize(content)
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
