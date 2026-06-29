# Prompt: implement the single-blog-post CSS / theme

Hand this to a future session to build the styling for izebuy single blog posts.

---

Implement the CSS and WordPress theme integration for izebuy **single blog posts**, matching the agreed "gold standard" design. Work in this repo (`linda-scoon/blog_post_styler`).

**What already exists (use it, don't reinvent):**
- The canonical stylesheet: `styles/izebuy-post.css`. Refine from this base.
- The design rules: `Docs/design-spec.md`.
- Rendered examples of the post HTML: `content/styled/*.html`.
- Posts are published as clean semantic HTML wrapped in `<article class="izebuy-post">`, using: `h1` (masthead title), `<nav class="izebuy-toc">[toc]</nav>` (contents box, filled by the site's TOC shortcode), `h2` (section headers, each a TOC entry), `h3` (sub-headings), `p`, `figure`/`img`, `figure.izebuy-map` (full-width map), `.izebuy-figR`/`.izebuy-figL` (floated images), `.izebuy-items` (two-column grid) of `.izebuy-item` cards (`.it-name`, `.it-text`, `.it-hours`), `ul.izebuy-bullets`, and `.izebuy-author`.

**Hard constraint:** the CSS must be **loaded by the theme (enqueued site-wide), NOT inlined in posts.** WordPress strips inline `<style>` from post content via KSES over the REST API, so inline styling does not survive. The post body carries only HTML + classes.

**Design rules:**
- Everything scoped under `.izebuy-post`.
- Structure only, **no colour**, with ONE exception: the about-author box has a light neutral background. Borders and text inherit colour from the theme.
- `h1` = centred masthead: uppercase, letter-spaced, double bottom border.
- `.izebuy-toc` (the `[toc]` contents) = a bordered box.
- `h2` = uppercase with a single underline rule; `h3` = small-caps with a left rule.
- Images large (full content width, thin border). `.izebuy-items` is a two-column grid of cards; card name on its own line, description beneath (no leading colon), hours italic.
- **`.izebuy-author` = a SMALL box (max ~560px), aligned LEFT (not centered), light neutral background, rounded border, round avatar.**
- Responsive: single column on mobile; `.izebuy-items` collapses to one column; floats clear.

**The cover image:**
- The post body has **no** cover image. The cover is the **WordPress Featured Image**, rendered by the theme.
- Desired behaviour: on **desktop** the featured image sits to the **right of the contents box**; on **mobile** the featured image appears **above** the contents. Implement this at the template level (the featured image comes from the theme, not the post body) — or advise if it's cleaner to inject the featured image into the `.izebuy-post` hero.

**Theme integration:**
- Build as a **child theme** (or a small enqueue plugin) so all posts, existing and future, get the design with no per-post CSS. Ask me for the active (parent) theme name — you need it for the child theme header.
- Provide: the enqueued stylesheet (from `styles/izebuy-post.css`), a single-post template if needed (`single.php` or block template/part) that wraps `the_content` in `.izebuy-post` and places the featured image + `[toc]` per the rule above, and **step-by-step install instructions I can follow**. (I can verify the steps but cannot test the live Malawi side, so the steps must be exact.)
- **Watch for duplication:** the theme already outputs the post title — make sure the masthead `h1` and the theme's title don't both show. Decide how to handle it and tell me.

**Deliverables:** the theme files in the repo, install steps, and a short note on how you handled the title and the featured-image placement. Test against the already-published market posts (e.g. Mbayani).
