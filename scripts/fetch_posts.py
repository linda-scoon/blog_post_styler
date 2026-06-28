#!/usr/bin/env python3
"""
Fetch blog posts from the izebuy WordPress site via the REST API and save them
into the repo so they can be read and reformatted offline.

Runs anywhere with network access to the site: a GitHub Action, your own
machine, or a server. It does NOT run from the restricted Claude web sandbox
(that environment is network-blocked) — that's the whole point of fetching the
posts INTO the repo.

Required environment variables
------------------------------
  WP_BASE_URL       e.g. https://development.izebuy.com   (no trailing slash needed)
  WP_USERNAME       a WordPress user login with editor/admin rights
  WP_APP_PASSWORD   an Application Password for that user
                    (WP admin -> Users -> Profile -> Application Passwords)

Optional
--------
  WP_STATUS         comma-separated statuses to fetch (default: "publish,draft")

Output (written under content/)
-------------------------------
  content/raw/<id>-<slug>.json   selected fields incl. the RAW post content
  content/raw/<id>-<slug>.html   just the raw content HTML, for easy reading
  content/index.json             machine-readable summary of everything fetched
  content/index.md               human-readable summary, with flags for posts
                                 that look empty or Elementor-built

No third-party dependencies — standard library only.
"""

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")
RAW_DIR = os.path.join(CONTENT_DIR, "raw")


def env(name, required=True, default=None):
    val = os.environ.get(name, default)
    if required and not val:
        sys.exit(f"ERROR: environment variable {name} is not set.")
    return val.strip() if isinstance(val, str) else val


def slugify(text, fallback="post"):
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return text[:60] or fallback


def looks_like_elementor(html):
    if not html or not html.strip():
        return True  # empty post_content is the classic Elementor symptom
    return bool(re.search(r"elementor|\[/?vc_|data-elementor", html, re.I))


def request_json(url, auth_header):
    req = urllib.request.Request(url, headers={
        "Authorization": auth_header,
        "Accept": "application/json",
        "User-Agent": "izebuy-blog-styler/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body), dict(resp.headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:500]
        if e.code == 401:
            sys.exit("ERROR 401 Unauthorized: check WP_USERNAME / WP_APP_PASSWORD "
                     "and that the user has editor/admin rights.\n" + detail)
        sys.exit(f"ERROR {e.code} from {url}\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: could not reach {url} ({e.reason}). "
                 "Is WP_BASE_URL correct and reachable from where this is running?")


def main():
    base = env("WP_BASE_URL").rstrip("/")
    user = env("WP_USERNAME")
    app_pw = env("WP_APP_PASSWORD")
    status = env("WP_STATUS", required=False, default="publish,draft")

    token = base64.b64encode(f"{user}:{app_pw}".encode()).decode()
    auth_header = f"Basic {token}"

    os.makedirs(RAW_DIR, exist_ok=True)

    # context=edit returns the RAW, unprocessed content (so we see shortcodes /
    # whatever Elementor left behind) and requires authentication. _embed pulls
    # the Featured Image URL (the post's cover image) along with each post.
    per_page = 100
    page = 1
    index = []

    print(f"Fetching posts from {base} (status={status}) ...")
    while True:
        query = urllib.parse.urlencode({
            "context": "edit",
            "status": status,
            "per_page": per_page,
            "page": page,
            "_embed": "wp:featuredmedia",
            "orderby": "date",
            "order": "asc",
        })
        url = f"{base}/wp-json/wp/v2/posts?{query}"
        posts, headers = request_json(url, auth_header)
        if not posts:
            break

        total_pages = int(headers.get("X-WP-TotalPages", page))
        for p in posts:
            pid = p.get("id")
            slug = p.get("slug") or slugify((p.get("title") or {}).get("raw"))
            title_raw = (p.get("title") or {}).get("raw", "")
            content_raw = (p.get("content") or {}).get("raw", "")

            # cover image = the post's Featured Image (from the _embed payload)
            cover_image = ""
            try:
                media = (p.get("_embedded") or {}).get("wp:featuredmedia") or []
                if media and isinstance(media[0], dict):
                    cover_image = media[0].get("source_url", "") or ""
            except Exception:
                cover_image = ""

            record = {
                "id": pid,
                "slug": slug,
                "link": p.get("link"),
                "status": p.get("status"),
                "date": p.get("date"),
                "modified": p.get("modified"),
                "title": title_raw,
                "content_raw": content_raw,
                "excerpt_raw": (p.get("excerpt") or {}).get("raw", ""),
                "categories": p.get("categories", []),
                "tags": p.get("tags", []),
                "featured_media": p.get("featured_media"),
                "cover_image": cover_image,
                "author": p.get("author"),
            }

            base_name = f"{pid}-{slug}"
            json_path = os.path.join(RAW_DIR, base_name + ".json")

            if os.path.exists(json_path):
                # NEVER overwrite an existing original. Re-fetching a post we have
                # already published would pull OUR OWN output back and corrupt the
                # writer's source (a feedback loop). Delete the file to force a re-pull.
                flags = ["preserved-original"]
            else:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(record, f, indent=2, ensure_ascii=False)
                with open(os.path.join(RAW_DIR, base_name + ".html"), "w", encoding="utf-8") as f:
                    f.write(content_raw or "")
                flags = []
                if not (content_raw or "").strip():
                    flags.append("EMPTY-content")
                if looks_like_elementor(content_raw):
                    flags.append("looks-elementor")

            index.append({
                "id": pid, "slug": slug, "title": title_raw, "status": p.get("status"),
                "link": p.get("link"), "chars": len(content_raw or ""), "flags": flags,
            })
            print(f"  [{pid}] {title_raw[:60]!r:62} {p.get('status'):8} "
                  f"{len(content_raw or ''):6d} chars  {' '.join(flags)}")

        if page >= total_pages:
            break
        page += 1

    index.sort(key=lambda r: r["id"])
    with open(os.path.join(CONTENT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # Human-readable summary
    lines = ["# Fetched blog posts", "",
             f"Total: **{len(index)}** posts from `{base}`.", "",
             "| ID | Title | Status | Chars | Flags |",
             "| --- | --- | --- | --- | --- |"]
    for r in index:
        lines.append(f"| {r['id']} | {r['title'][:50]} | {r['status']} | "
                     f"{r['chars']} | {' '.join(r['flags']) or '-'} |")
    elementor = [r for r in index if "looks-elementor" in r["flags"] or "EMPTY-content" in r["flags"]]
    if elementor:
        lines += ["", "## ⚠️ Needs attention",
                  "These posts have empty or Elementor-style content — their real "
                  "text may be locked in `_elementor_data` and need a different "
                  "extraction step before reformatting:", ""]
        lines += [f"- [{r['id']}] {r['title']}" for r in elementor]
    with open(os.path.join(CONTENT_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nDone. {len(index)} posts saved under content/. "
          f"{len(elementor)} flagged for attention. See content/index.md")


if __name__ == "__main__":
    main()
