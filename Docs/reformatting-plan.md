# Reformatting existing blog posts — plan & status

Goal: bring the **existing** blog posts on the izebuy WordPress site into the
house style (`Docs/design-spec.md`), so they match the new Word-doc pipeline.

## Workflow (proposed — not built yet)

One post at a time:

1. **Fetch** only blog *posts* (not pages) via `GET /wp-json/wp/v2/posts`
   (request `context=edit` to get raw `content`). Pages, the how-it-works
   page, etc. are left untouched.
2. **Clean** — strip shortcodes not on the keep-list (keep `[toc]`), remove
   leftover page-builder markup.
3. **Restructure** — most old posts won't have proper `H1/H2/H3` structure.
   An LLM pass reads each post and adds the correct semantic headings and
   components per the design spec, producing clean markup.
4. **Style** — wrap in `.izebuy-post`; the scoped stylesheet does the rest.
5. **Write back** via `POST /wp-json/wp/v2/posts/<id>` **as a draft first**, so
   it can be reviewed before going live.

## Safety

- Never blind-overwrite a published post. Save the original `content` to a
  backup file, write the reformatted version as a **draft/revision**, review,
  then publish.
- WordPress keeps post revisions, so there is an undo path on the site too.
- About-the-author block only when the original already has author info.
- No colour is ever added (see design spec).

## ⚠️ Blocker: site not reachable from the Claude web environment

This environment's **network policy** denies outbound HTTPS to the site — the
proxy returns `403 Forbidden` on CONNECT for both `izebuy.com` and
`development.izebuy.com`. The WordPress API itself is fine; it just can't be
reached from *here*.

Ways forward (pick one):

1. **Loosen the network policy** for this web environment to allow the izebuy
   domains, then everything runs from here.
   See https://code.claude.com/docs/en/claude-code-on-the-web
2. **Run the tool on a machine that can reach the site** (local/server) using a
   WordPress **Application Password** (Users → Profile → Application Passwords).
3. **Provide one real post's content** to develop and prove the conversion
   offline while access is sorted.

## ⚠️ Open question: where does the old content live?

The site previously used Elementor (now removed). Elementor-built posts often
store their real content in hidden post-meta (`_elementor_data`) as JSON,
leaving `post_content` empty or just a shortcode. **We must inspect one real
post** to know whether `post_content` is usable or needs a different extraction
step. Cannot be answered until the site is reachable or a sample is provided.
