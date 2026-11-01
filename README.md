# The Current — source-linked news publishing

A responsive, static HTML/CSS/JavaScript news portal with Python RSS discovery, OpenAI-assisted drafting, an editorial review queue, and optional advertising. No application server or database is needed. Production builds exclude all demonstration articles. There are no fabricated current news reports or publisher codes.

## Run locally

Requires Python 3.12+ and Git. No Node dependencies or frontend bundler are needed.

```sh
python scripts/build.py
python -m http.server 4173 --directory dist
```

Open `http://localhost:4173`. The six included evergreen explainers are visibly marked **DEMO**. All development pages are noindex. Do not deploy the development build as a live news publication.

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The build itself needs only the Python standard library. Ingestion needs the packages in `requirements.txt`. `.env.example` documents settings; scripts read process environment variables, not `.env` files automatically. Never commit a real `.env` or API key.

## Layout

```text
config/site.json        publication name, contact, categories, fallback URL
config/feeds.json       opt-in source feeds and rights confirmation
config/ads.json         public publisher configuration (disabled by default)
content/articles/       reviewed, published JSON; includes development samples
content/drafts/         private editorial staging; never copied to dist
scripts/news.py         RSS to attributed AI drafts
scripts/approve.py      explicit editorial verification and publication
scripts/review_queue.py persistent GitHub draft-review branch
scripts/build.py        static HTML, metadata, search index, sitemap, robots
static/assets/          local fonts via system stacks, CSS, JS, original SVG art
static/ads.txt          authorized-seller records supplied by your network
tests/                  review, duplicate, deployment-path and leak checks
.github/workflows/      scheduled drafting and validated deployment
dist/                   generated hosting output; ignored by Git
```

## Put this project in GitHub

Use the **contents of this folder** as the repository root; `.github` must be at the top level. This deliverable was prepared locally because no target repository was supplied.

Create an empty repository in GitHub, then from this folder:

```sh
git init
git add .
git commit -m "Build source-linked news publication"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the remote URL. If importing into an existing repository, use its normal branch and PR process instead. Set the default branch to `main` or update both workflows accordingly. Protect `main` and require editorial review. Fork PR workflows have no access to the OpenAI secret.

## Cloudflare Pages deployment

1. Connect the GitHub repository in Workers & Pages → Create → Pages → Import Git repository.
2. Framework preset: None. Build command: `python scripts/build.py`. Output directory: `dist`.
3. Set build environment variables `SITE_URL=https://your-final-domain.example`, `PRODUCTION=1`, `INCLUDE_DEMOS=0`. Choose a Python 3.12+ build environment. No OpenAI key belongs in the Pages environment.
4. Set the same `SITE_URL` as a GitHub repository Actions variable so PR checks build correctly. Set `DEPLOY_TARGET=cloudflare` to skip the GitHub Pages deploy job.
5. Deploy `main`. Add your domain in Pages, complete its DNS instructions, then rebuild with the final canonical domain. Disable production ads on preview deployments (`PRODUCTION=0`), and keep previews noindex.

Cloudflare automatically rebuilds after approved content merges. See [Cloudflare static HTML guide](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/).

## GitHub Pages deployment

1. Repository Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. GitHub Pages deployment is the default. The workflow automatically derives `https://YOUR_ACCOUNT.github.io/YOUR_REPOSITORY`; optionally set Actions variables `DEPLOY_TARGET=github` and `SITE_URL` to override it. For an account-root repository (`YOUR_ACCOUNT.github.io`), set `SITE_URL=https://YOUR_ACCOUNT.github.io` explicitly.
3. Push to `main` or run **Validate and deploy site**. It tests, builds and uploads `dist`, then deploys with Pages OIDC permissions. PRs build only.
4. For a custom domain, set `SITE_URL=https://news.yourdomain.example`, create `static/CNAME` containing that domain, configure Pages/DNS, and rebuild.

The builder derives the base path from `SITE_URL`; category links, article URLs, assets, search and metadata work beneath `/YOUR_REPOSITORY/`. A custom domain is recommended for ads because `ads.txt` is expected at the domain root. Project Pages cannot supply `https://YOUR_ACCOUNT.github.io/ads.txt` from a repository subpath.

See [GitHub custom deployment workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages). Hosting eligibility, usage limits and advertising policies should be checked for your intended publication.

## Configure RSS and OpenAI

1. Review each source's feed license and reuse terms. Attribution alone does not grant republication rights. Example feeds are **disabled** until you set `enabled` and `rights_confirmed` to `true` in `config/feeds.json`. Use final HTTPS feed addresses; automatic redirects are deliberately rejected. Add your licensed sources for all six categories.
2. Add `OPENAI_API_KEY` in GitHub Actions **Secrets**. Set `OPENAI_MODEL` as a repository variable to a Structured Outputs-capable model your account can access. The default is `gpt-4.1-mini`; change it for your needs. Set API spend limits in your OpenAI project.
3. Optional variable: `MAX_DRAFTS` (default 3, hard maximum 10 per run). Edit the UTC cron in `.github/workflows/news.yml`; default is every six hours at minute 17. GitHub schedules may be delayed and inactive-repository schedules may need re-enabling.
4. Repository Settings → Actions → General: allow GitHub Actions to create pull requests. The draft job requires `contents: write` and `pull-requests: write`; it never merges or publishes an article.
5. Run **Draft news for editorial review** manually first. It fetches at most 30 entries per feed, skips old or undated entries and short excerpts, deduplicates canonical URLs and normalized source titles, and saves bounded, structured drafts. It uses the [OpenAI Responses Structured Outputs API](https://developers.openai.com/api/docs/guides/structured-outputs) with `store=False`.

Original source URLs are selected by code, not invented by the model. Source text is stripped of HTML and treated as untrusted input. Only the configured feeds are fetched, with timeouts and a 2 MB cap; linked webpages are not scraped. Feed snippets alone may be incomplete, misleading or wrong. The model's output is a **draft**, never verified reporting. Editors must open the source, check every claim and add evidence or discard the story. The script records source excerpts, fetch time and source publication time in the private draft JSON.

Canonical URLs remove tracking parameters and fragments. Normalized title matching also blocks exact title variants with punctuation differences. Different publishers' coverage of the same event can still require human deduplication; this is not a semantic plagiarism detector.

## Manual approval and publication

The scheduled job maintains `automation/news-drafts` and a draft PR. Each run restores only pending JSON from that branch into a clean `main` checkout, checks those drafts and published articles for duplicates, and updates the queue with a compare-and-swap Git push. It does not execute scripts from the review branch. Workflow artifacts provide a 14-day recovery copy. Keep review history in Git, and avoid editing the bot branch while a run is active.

1. Fetch the review branch and create your own editorial branch from current `main`:

   ```sh
   git fetch origin automation/news-drafts
   git switch -c editorial/review-story origin/main
   git restore --source=origin/automation/news-drafts -- content/drafts
   ```

2. Inspect each draft's `source_excerpt`, original source URLs and `verification_notes`. Independently check facts, dates, quotes, names, numbers and context. Confirm text and image rights. Improve the reporting; do not pad a short excerpt with invented background. Resolve `needs_more_reporting` only after obtaining adequate evidence.
3. Edit the JSON's title, body paragraphs, summary, metadata, tags and author. Add all sources used; source objects contain `name` and an HTTPS `url`. Do not include HTML in body text.
4. Approve a checked story explicitly:

   ```sh
   python scripts/approve.py DRAFT_FILENAME_WITHOUT_JSON --reviewer "Editor Name" --verified
   python -m unittest discover -s tests -v
   # Set SITE_URL and PRODUCTION=1 in the shell before a production check:
   python scripts/build.py
   ```

   PowerShell: `$env:SITE_URL='https://yourdomain.example'; $env:PRODUCTION='1'`.
   Bash: `SITE_URL=https://yourdomain.example PRODUCTION=1 python scripts/build.py`.

5. Commit `content/articles` and the reviewed draft deletion on the editorial branch, open a PR, inspect the generated article, and merge after review. `published_at` is your publication date; `source_published_at` remains separate. The build rejects non-demo articles without reviewer and verification fields. This attestation records human responsibility; software cannot establish factual truth.
6. The next queue refresh omits drafts whose source URLs are now published. Do not merge the bot PR to publish unverified stories. To retain a rejected story in the duplicate set, keep its JSON with `status: "rejected"` under `content/drafts` on `main` via a review PR. Do not just delete it, or a later feed entry can reintroduce it.

No automatic publication mode is enabled. The manual approval step is intentional. If the bot lacks branch/PR permissions or races a human update, it fails visibly instead of bypassing protections. Check the workflow log and restore the artifact if needed. GitHub automation-created PRs may not trigger additional Actions workflows with the default token; your human-created editorial PR does.

## Article format and images

The checked-in examples show the JSON format. Required fields include `slug`, `title`, `summary`, `meta_description`, `category`, `author`, timezone-aware `published_at`, `paragraphs`, `tags`, `sources`, `status: "published"`, `reviewed_by`, `verified_at`. AI-assisted articles set `ai_assisted: true` and disclose review on the page. Never change `demo` to bypass review.

Every category has original local SVG editorial artwork with fixed dimensions and descriptive article alt text. It is explicitly labeled an illustration, never a documentary image of an event. To use a licensed photograph, add it under `static/assets/`, set `image` to its `assets/...` path, and supply `image_alt` and `image_credit`. Prefer compressed WebP/AVIF, provide the source's license/credit, and keep images approximately 1000 × 640. Never copy an RSS image without permission.

## Advertising and launch

Read [ADS.md](ADS.md) for actual publisher code, consent, ads.txt and placement setup. Ad scripts are disabled in development and in the supplied production configuration. This project cannot register your publisher account, obtain approval, or provide real publisher codes.

Before launch, update `config/site.json` with your identity and working editorial email, replace the starter policy language with your actual policies, publish substantive original reporting, verify accessibility and mobile layouts, then apply to your chosen network. Do not apply with an empty production edition. Do not buy fake traffic, encourage ad clicks, disguise ads as headlines, or use unlicensed copied articles. Approval, traffic and revenue are not guaranteed.

## SEO, performance and operations

- Static per-article HTML and clean directory URLs work without client routing. Each page gets a title, description, canonical and Open Graph metadata. Published non-demo articles have `NewsArticle` structured data. Demo articles are noindex and excluded from the sitemap.
- Sitemap and robots use `SITE_URL`. Submit the sitemap in search engine webmaster tools after launch; indexability does not guarantee ranking. Do not mass-produce low-value paraphrases to manipulate rankings.
- Local system fonts, small JS/CSS, fixed image dimensions, lazy secondary images and no framework runtime keep the critical path small. Measure actual LCP/CLS/INP on mobile after adding real images, ads and a CMP. No unmeasured Core Web Vitals score is claimed.
- Search downloads only published title/summary/tag metadata. It uses DOM text APIs rather than interpolating user input as HTML. Consider a hosted search index if the archive becomes too large for a browser download.
- No OpenAI calls occur in the browser; only trusted scheduled automation receives the key. Draft evidence is excluded from `dist`. Private draft confidentiality also depends on repository visibility: use a private repository if source excerpts or editorial work must remain private.
- Trusted ad snippets and CMP head files execute publisher-controlled third-party code. Restrict who can edit them, review vendor domains, and do not accept visitor-supplied code. Add a tested CSP for the exact vendor domains after integration; no broad wildcard CSP is supplied.
- Use protected branches and dependency update reviews. Major Actions tags and bounded Python dependencies are readable starter settings; for a hardened production deployment, review and pin verified Action commit SHAs and a dependency lockfile with hashes.

## Verification

`python -m unittest discover -s tests -v` checks URL deduplication, editorial gating, internal links under a repository base path, secret/draft exclusions, and production exclusion of demo content. `node --check static/assets/app.js` checks browser JavaScript syntax when Node is available. Paid OpenAI requests and real ad impressions are not part of tests. Those require your credentials and network accounts.
