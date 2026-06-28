# Setup: credentials for talking to WordPress

The fetch (and later the publish) tooling authenticates to WordPress with an
**Application Password** — a built-in WordPress feature, safer than your real
login password and revocable at any time.

## 1. Create an Application Password in WordPress

1. Log in to the site's `wp-admin` as an **Administrator** (or Editor).
2. Go to **Users → Profile** (your own user).
3. Scroll to **Application Passwords**.
4. Type a name, e.g. `blog-styler`, and click **Add New Application Password**.
5. Copy the password it shows you — a string like `abcd EFGH ijkl MNOP qrst UVWX`.
   You only see it once. The spaces are fine; keep them or remove them.

> The user you create it under must have rights to **edit posts** (Administrator
> or Editor), because we read raw content and will write drafts back.

## 2. Add three secrets to GitHub

In the GitHub repo: **Settings → Secrets and variables → Actions → New
repository secret**. Add these three (names must match exactly):

| Secret name | Value |
| --- | --- |
| `WP_BASE_URL` | The site URL, e.g. `https://development.izebuy.com` (no trailing slash) |
| `WP_USERNAME` | The WordPress user login the Application Password belongs to |
| `WP_APP_PASSWORD` | The Application Password from step 1 |

That's all the credentials needed. Secrets are encrypted and never printed in
logs.

## 3. Run the fetch

> ⚠️ For the **Run workflow** button to appear in the Actions tab, the workflow
> file must exist on the repository's **default branch** (`main`). It currently
> lives on the working branch — so either merge this work to `main` first, or
> tell me and I'll open a PR. (Alternatively, run the script locally — see
> below — which needs no merge.)

Once it's on `main`: **Actions → Fetch blog posts from WordPress → Run
workflow**. It pulls every post into `content/` and commits them. Then I read
them and build the HTML generator.

### Running locally instead (optional)

Anywhere with network access to the site:

```bash
export WP_BASE_URL="https://development.izebuy.com"
export WP_USERNAME="your-wp-login"
export WP_APP_PASSWORD="abcd EFGH ijkl MNOP qrst UVWX"
python3 scripts/fetch_posts.py
```

Then commit the `content/` folder it creates.
