#!/usr/bin/env python3
"""
Publish the styled market posts back to the izebuy WordPress site via the REST
API. Generates the gold-standard HTML for each post with style_post.convert()
and writes it back.

SAFE BY DEFAULT:
  - **Dry run** unless you pass --commit (or set DRY_RUN=false). A dry run shows
    exactly what would change and writes nothing.
  - Before changing a post it **backs up** the live post's current content into
    content/backup/<id>.json.
  - 'update' mode keeps each post's CURRENT status, so a published post stays
    published (it never gets silently unpublished). WordPress also keeps a
    revision of the previous version.
  - Refuses to publish a post whose styled HTML still contains a cover-image
    PLACEHOLDER (run the fetch first so real cover images are present).

Modes:
  update      (default) overwrite the existing post's body, keep its status.
  draft-copy  create a NEW draft post (a duplicate) for review; the live post is
              left completely untouched.

Env: WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD
Usage:
  python3 scripts/publish_posts.py --only 4458              # dry run, one post
  python3 scripts/publish_posts.py --only 4458 --commit     # really do it
  python3 scripts/publish_posts.py --mode update --commit   # all market posts
Stdlib only.
"""

import argparse
import base64
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "content", "raw")
BACKUP = os.path.join(REPO, "content", "backup")

# reuse the styling logic
_spec = importlib.util.spec_from_file_location(
    "style_post", os.path.join(os.path.dirname(os.path.abspath(__file__)), "style_post.py"))
style_post = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(style_post)
MARKET_IDS = style_post.MARKET_IDS


def env(name, required=True, default=None):
    val = os.environ.get(name, default)
    if required and not val:
        sys.exit(f"ERROR: environment variable {name} is not set.")
    return val.strip() if isinstance(val, str) else val


def request(method, url, auth, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": auth, "Accept": "application/json",
        "Content-Type": "application/json", "User-Agent": "izebuy-blog-styler/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:600]
        sys.exit(f"ERROR {e.code} {method} {url}\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: could not reach {url} ({e.reason}).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["update", "draft-copy"], default="update")
    ap.add_argument("--only", help="publish a single post id")
    ap.add_argument("--commit", action="store_true",
                    help="actually write to the site (otherwise dry run)")
    args = ap.parse_args()

    # DRY_RUN env overrides too: DRY_RUN=false behaves like --commit
    commit = args.commit or (os.environ.get("DRY_RUN", "").lower() == "false")

    base = env("WP_BASE_URL").rstrip("/")
    auth = "Basic " + base64.b64encode(
        f'{env("WP_USERNAME")}:{env("WP_APP_PASSWORD")}'.encode()).decode()

    ids = [args.only] if args.only else sorted(MARKET_IDS)
    files = {fn.split("-")[0]: fn for fn in os.listdir(RAW) if fn.endswith(".json")}
    os.makedirs(BACKUP, exist_ok=True)

    print(f"Mode: {args.mode}   {'COMMIT (writing to site)' if commit else 'DRY RUN (no changes)'}\n")
    for pid in ids:
        fn = files.get(str(pid))
        if not fn:
            print(f"  [{pid}] no fetched post found — skipping")
            continue
        post, article = style_post.convert(os.path.join(RAW, fn))

        if 'class="ph"' in article:
            print(f"  [{pid}] {post['title'][:40]:42} SKIPPED — cover image is still a "
                  f"placeholder. Re-run the fetch to pull the real Featured Image.")
            continue

        if args.mode == "draft-copy":
            print(f"  [{pid}] {post['title'][:40]:42} -> NEW draft copy")
            if commit:
                new = request("POST", f"{base}/wp-json/wp/v2/posts", auth,
                              {"title": post["title"], "content": article, "status": "draft"})
                print(f"          created draft id {new.get('id')}: {new.get('link')}")
            continue

        # update mode: keep the post's current status (never unpublish a live post)
        if not commit:
            print(f"  [{pid}] {post['title'][:40]:42} -> WOULD update in place "
                  f"(keeps current status; original backed up first)")
            continue
        # back up the live content first, then overwrite the body
        live = request("GET", f"{base}/wp-json/wp/v2/posts/{pid}?context=edit", auth)
        with open(os.path.join(BACKUP, f"{pid}.json"), "w", encoding="utf-8") as f:
            json.dump({"id": pid, "status": live.get("status"),
                       "content_raw": (live.get("content") or {}).get("raw", "")},
                      f, indent=2, ensure_ascii=False)
        status = live.get("status", "publish")
        request("POST", f"{base}/wp-json/wp/v2/posts/{pid}", auth,
                {"content": article, "status": status})
        print(f"  [{pid}] {post['title'][:40]:42} -> updated in place "
              f"(status stays '{status}'); backup saved")

    print("\nDone." + ("" if commit else "  (dry run — re-run with --commit to apply)"))


if __name__ == "__main__":
    main()
