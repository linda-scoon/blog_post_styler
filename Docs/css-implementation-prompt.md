# Prompt: build the single-blog-post styling (self-contained)

Paste this into a session in the NEW repo. It contains everything needed; it does not depend on any other repository.

---

I need you to build the CSS and WordPress theme integration for styling a **single blog post** on my WordPress site (izebuy, a Malawian buy-and-sell site). The design is already decided. Everything you need is in this prompt.

## How the posts are structured

Each post is published as clean, semantic HTML wrapped in `<article class="izebuy-post">`. The post body contains only HTML and class names (no inline CSS, no `<style>`). It uses the site's table-of-contents shortcode `[toc]` for the contents box. A representative post looks like this:

```html
<article class="izebuy-post">
  <h1>Mbayani Market</h1>
  <nav class="izebuy-toc">[toc]</nav>

  <p>Intro paragraph.</p>

  <h2 id="how-to-get-there">How to get there</h2>
  <p>Body text.</p>
  <figure class="izebuy-map"><iframe src="https://maps.google.com/..."></iframe></figure>

  <h2 id="things-you-can-buy">Things you can buy</h2>
  <div class="izebuy-items">
    <div class="izebuy-item">
      <figure><img src="https://.../photo1.jpg" alt=""></figure>
      <div class="it-cap"><span class="it-name">Tomatoes and Onions</span><span class="it-text">Cheap and good quality.</span></div>
    </div>
    <div class="izebuy-item">
      <figure><img src="https://.../photo2.jpg" alt=""></figure>
      <div class="it-cap"><span class="it-name">Clothes</span><span class="it-text">Second-hand, cheapest in town.</span></div>
    </div>
  </div>

  <h2 id="shops">Shops and services</h2>
  <h3>Services</h3>
  <p><b>Mill</b> There is one maize mill near the entrance.</p>
  <ul class="izebuy-bullets"><li>A practical tip.</li><li>Another tip.</li></ul>

  <h2 id="honest-take">Our honest take</h2>
  <p>Body text.</p>

  <div class="izebuy-author">
    <figure><img src="https://.../author.jpg" alt="Author photo"></figure>
    <div><h2>About the Author</h2><p>Short author bio.</p></div>
  </div>
</article>
```

A text-heavy section may also use a floated image: `<figure class="izebuy-figR">…</figure>` (float right) or `<figure class="izebuy-figL">…</figure>` (float left), followed by `<div class="clear"></div>`.

## Hard constraint

The CSS must be **loaded by the theme (enqueued site-wide), NOT inlined in the post content.** WordPress strips inline `<style>` from post content via its KSES sanitizer over the REST API, so inline styling does not survive. The post body stays HTML + classes only; the theme supplies the styling.

## The design rules

- Everything scoped under `.izebuy-post` so it cannot affect the rest of the site.
- **Structure only, no colour declarations**, with ONE deliberate exception: the about-the-author box has a light neutral background so it reads as a proper "about" card. All other borders and text inherit colour from the theme.
- `h1` = centred masthead: uppercase, letter-spaced, double bottom border.
- `.izebuy-toc` (which contains the `[toc]` shortcode) = a bordered contents box.
- `h2` = uppercase section header with a single underline rule; each is a contents entry. `h3` = small-caps sub-heading with a left rule.
- Images render large (full content width, thin border). `.izebuy-items` is a **two-column grid** of `.izebuy-item` cards; the name (`.it-name`) is on its own line, the description (`.it-text`) beneath it with no leading colon, hours (`.it-hours`) italic.
- `ul.izebuy-bullets` = a custom list with a "›" marker.
- **`.izebuy-author` = a SMALL box (max ~560px), aligned LEFT (not centered and not full width), light neutral background, rounded border, round avatar.**
- Responsive: single column on mobile; `.izebuy-items` collapses to one column; floated figures clear.

## The cover image

- The post body has **no** cover image. The cover is the **WordPress Featured Image**, rendered by the theme.
- Desired behaviour: on **desktop** the featured image sits to the **right of the contents box**; on **mobile** the featured image appears **above** the contents.
- The stylesheet below already includes `.izebuy-hero` and `.izebuy-featured` for exactly this. The cleanest implementation is a single-post template that outputs, near the top of the article: `<div class="izebuy-hero"><nav class="izebuy-toc">[toc]</nav><figure class="izebuy-featured">[the featured image]</figure></div>`. Advise me if you'd do it differently.

## The stylesheet to start from

This is the agreed stylesheet. Refine it if needed, but keep the rules and the scoping.

```css
/* izebuy single blog post — scoped, structure-only stylesheet.
   Scoped under .izebuy-post. No colour except the about-author background. */

.izebuy-post{ max-width:1140px; margin:0 auto; padding:52px 60px 44px;
  font-family:Georgia,'Times New Roman',serif; line-height:1.7; font-size:18px; }

/* H1 = centred masthead with a double underline */
.izebuy-post h1{ text-align:center; text-transform:uppercase; letter-spacing:3px;
  font-size:46px; margin:0 0 28px; padding-bottom:16px; border-bottom:8px double; }

/* Hero: contents (left) + featured/cover image (right) on desktop;
   stacks on mobile with the cover image ABOVE the contents. */
.izebuy-hero{ display:flex; gap:32px; align-items:flex-start; margin-bottom:34px; }
.izebuy-toc{ flex:0 0 280px; border:1px solid; padding:18px 20px; font-size:15px; line-height:2; }
.izebuy-toc .toc-title{ text-transform:uppercase; letter-spacing:1px; font-size:12px;
  font-weight:bold; margin:0 0 10px; border-bottom:1px solid; padding-bottom:7px; }
.izebuy-toc ul{ margin:0; padding-left:18px; }
.izebuy-toc a{ color:inherit; text-decoration:none; }
.izebuy-featured{ flex:1; margin:0; }
.izebuy-featured img{ width:100%; height:auto; display:block; border:1px solid; }
.izebuy-featured figcaption{ font-size:14px; font-style:italic; margin-top:8px; text-align:center; }

/* H2 = uppercase section header with a single rule; H3 = small-caps with a left rule */
.izebuy-post h2{ text-transform:uppercase; letter-spacing:1.5px; font-size:23px;
  margin:48px 0 18px; padding-bottom:9px; border-bottom:2px solid; clear:both; }
.izebuy-post h3{ font-size:18px; font-variant:small-caps; letter-spacing:.5px;
  margin:30px 0 14px; border-left:4px solid; padding-left:12px; }
.izebuy-post p{ margin:0 0 16px; }

/* Images are the content: large, never thumbnails */
.izebuy-post figure{ margin:0; }
.izebuy-post figure img{ width:100%; height:auto; display:block; border:1px solid; }
.izebuy-post figcaption{ font-size:13px; font-style:italic; margin-top:6px; }
.izebuy-post .clear{ clear:both; }

/* Float helpers for text-heavy sections */
.izebuy-figR{ float:right; width:420px; margin:4px 0 14px 28px; }
.izebuy-figL{ float:left;  width:420px; margin:4px 28px 14px 0; }

/* Full-width map figure */
.izebuy-map{ margin:6px 0 24px; }
.izebuy-map figcaption{ text-align:center; }

/* Two-column card grid (shops / products); name on its own line, no leading colon */
.izebuy-items{ display:grid; grid-template-columns:repeat(2,1fr); gap:30px; margin:10px 0 14px; }
.izebuy-item .it-cap{ margin-top:10px; }
.izebuy-item .it-name{ font-weight:bold; font-size:19px; display:block; }
.izebuy-item .it-text{ font-size:16px; }
.izebuy-item .it-hours{ font-size:14px; font-style:italic; }

/* Bulleted list with a "›" marker */
ul.izebuy-bullets{ list-style:none; padding:0; margin:0 0 20px; }
ul.izebuy-bullets li{ position:relative; padding:11px 0 11px 30px; border-bottom:1px dotted; font-size:17px; }
ul.izebuy-bullets li::before{ content:"\203A"; position:absolute; left:8px; top:9px; font-weight:bold; font-size:20px; }

/* About-the-author — small, LEFT-aligned card, light neutral background */
.izebuy-author{ max-width:560px; margin:48px 0 0; display:flex; gap:20px;
  align-items:center; padding:20px 24px; border:1px solid; border-radius:8px;
  background:#f5f5f5; }
.izebuy-author figure{ flex:0 0 84px; margin:0; }
.izebuy-author img{ width:84px; height:84px; object-fit:cover; border-radius:50%; border:1px solid; }
.izebuy-author h2{ border:none; margin:0 0 6px; padding:0; font-size:13px;
  text-transform:uppercase; letter-spacing:1px; }
.izebuy-author p{ margin:0; font-size:15px; line-height:1.55; }

/* Responsive */
@media (max-width:760px){
  .izebuy-post{ padding:28px 20px; }
  .izebuy-hero{ flex-direction:column; }
  .izebuy-featured{ order:-1; }          /* cover image ABOVE contents on mobile */
  .izebuy-toc{ flex-basis:auto; width:100%; box-sizing:border-box; }
  .izebuy-figR,.izebuy-figL{ float:none; width:100%; margin:0 0 16px; }
  .izebuy-items{ grid-template-columns:1fr; }
  .izebuy-author{ flex-direction:column; align-items:flex-start; }
}
```

## What to build

- A **child theme** (or a small enqueue plugin) that loads this stylesheet site-wide, so every post — existing and future — is styled with no per-post CSS.
- A single-post template (`single.php`, or a block template / template part) if needed, that ensures `the_content` is wrapped in `.izebuy-post` and places the featured image + `[toc]` per the cover-image rule above.
- **Step-by-step install instructions I can follow.** I can follow and verify the steps, but I can't fully test on the live site, so the steps must be exact.

## Things to check with me

- **Ask me for the active (parent) theme name** — you need it for the child theme header.
- **Title duplication:** the theme already outputs the post title. Make sure the masthead `h1` in the body and the theme's own title don't both show. Decide how to handle it (hide one) and tell me what you did.

Deliverables: the theme/plugin files, exact install steps, and a short note on how you handled the title and the featured-image placement.
