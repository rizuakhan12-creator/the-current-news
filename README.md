# The Current — RSS collection + manual publishing

Live site: https://rizuakhan12-creator.github.io/the-current-news/
Repository: https://github.com/rizuakhan12-creator/the-current-news

A responsive HTML/CSS/JavaScript news portal with a Python RSS reading list and explicit editorial approval. **No OpenAI calls, API keys, paid AI services, or Python packages are required.** The existing OpenAI secret is unused. Hosting and GitHub Actions remain subject to your account's free allowances; no unlimited free hosting or ad income is promised.

## আপনার কাজের ধাপ

1. GitHub → **Actions → Collect RSS for manual review → Run workflow**। সময়সূচি অনুযায়ী এটি ছয় ঘণ্টা পরপরও চলে।
2. **Code → branch → automation/news-drafts → content/drafts** খুলুন। প্রতিটি JSON-এ source_title, source_excerpt এবং sources-এর original link দেখুন।
3. Original source পড়ে তথ্য যাচাই করুন। GitHub-এর edit বোতাম দিয়ে একই draft JSON-এ নিজের লেখা title, summary, meta_description, author, paragraphs এবং tags লিখুন। source_excerpt কপি করে article বানাবেন না। লেখার ভাষা বাংলা বা ইংরেজি হতে পারে; URL slug ASCII রাখুন।
4. তথ্য, attribution ও reuse rights যাচাই হয়ে গেলে needs_more_reporting-এর মান false করুন। সম্পাদিত JSON **automation/news-drafts branch-এই** commit করুন।
5. **Actions → Prepare manual publication → Run workflow** খুলুন। Branch main রাখুন। Draft-এর 20-character filename দিন (.json বাদ দিয়ে), verification checkbox-এ সম্মতি দিন, তারপর Run workflow চাপুন।
6. Workflow summary-র review link খুলুন। তৈরি হওয়া editorial branch/PR-এর article দেখুন। সব ঠিক থাকলে PR ready করে main-এ merge করুন। এরপর Pages workflow article প্রকাশ করবে।

GitHub bot-এর PR তৈরির অনুমতি না থাকলেও draft/editorial branch সেভ হয়। Workflow summary-র compare link দিয়ে নিজে PR খুলতে পারবেন। কোনো permission বাড়ানো বাধ্যতামূলক নয়। আপনার লিখিত verification ছাড়া source excerpt বা খালি article প্রকাশ হয় না।

## Local preview and tests

Requires Python 3.12+. Frontend build dependencies and pip installation are unnecessary.

PowerShell:

```powershell
$env:SITE_URL='http://localhost:4173'
python scripts/build.py
python -m http.server 4173 --directory dist
```

Bash:

```sh
SITE_URL=http://localhost:4173 python scripts/build.py
python -m http.server 4173 --directory dist
```

Open http://localhost:4173. Six clearly labeled evergreen demo explainers appear in development. Production excludes them and starts empty until reviewed articles are published.

```sh
python -m unittest discover -s tests -v
python -m compileall -q scripts
node --check static/assets/app.js
```

The tests cover RSS/Atom parsing, unsafe XML, deduplication, empty-draft rejection, manual approval, HTML escaping, source/draft exclusions and GitHub project paths. Node is only needed for the optional JavaScript syntax check.

## Configuration and collection

- config/site.json: publication name, description, contact email and six categories.
- config/feeds.json: configured HTTPS feeds. NASA is enabled for attributed editorial leads. BBC is an example, disabled pending review of its reuse terms.
- MAX_ITEMS: GitHub Actions variable, default 10 and hard maximum 30 new leads per run.
- .github/workflows/news.yml: default schedule is minute 17 every six hours, UTC. GitHub schedules may be delayed.
- .env.example: documents environment variables. Scripts read process variables; no .env loader is installed.
- config/ads.json: public advertising configuration, disabled by default. See [ADS.md](ADS.md).

RSS collection reads at most 30 entries per feed with a 30-second timeout and 2 MB cap. It accepts RSS 2.0, RSS 1.0/RDF and Atom, rejects external redirects and DTD/entity declarations, and does not scrape linked pages or copy images/full articles. It strips excerpt HTML and limits stored source excerpts to 1,200 characters. Invalid URLs and dates are skipped individually. Dated items older than seven days or more than one hour in the future are skipped. Undated leads may be collected for manual investigation and retain a null source date.

Canonical source URLs remove tracking parameters/fragments; normalized source headlines prevent exact title variants. Existing pending, rejected and published content is included in deduplication. Editors still need to recognize different publishers' coverage of the same event.

NASA factual news usage requires attribution and must not imply endorsement; third-party content can have separate rights. Review [NASA's usage guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) and each original article before writing or reusing material. Enabling a feed does not license every item or image.

## What a collected lead contains

A lead saves source_title, source_excerpt, source_published_at, fetched_at and sources. It sets status=draft, content_origin=rss_manual, ai_assisted=false, needs_more_reporting=true. Publishing fields are deliberately empty.

When editing a lead, fill these fields with your own checked writing:

```json
{
  "title": "Your original headline",
  "summary": "Your original summary of the checked story.",
  "meta_description": "A concise original search description.",
  "author": "Your byline",
  "paragraphs": ["Your first checked paragraph.", "Your next checked paragraph."],
  "tags": ["Your topic"],
  "needs_more_reporting": false
}
```

This is a partial editing example; preserve the draft's id, slug, sources, category and other fields. Add additional sources used in your reporting. The publication workflow records the GitHub actor as reviewer and assigns your publication date. It does not treat the source publication date as your article's publication date.

## Approve from a local checkout

```sh
git fetch origin automation/news-drafts
git switch -c editorial/review-story origin/main
git restore --source=origin/automation/news-drafts -- content/drafts
# Edit the chosen JSON, write original text, check every fact and set needs_more_reporting=false.
python scripts/approve.py DRAFT_ID --reviewer "Editor Name" --verified
```

Inspect the diff, commit the approved article and draft deletion, open an editorial PR and merge after review. The web workflow does the same branch preparation. It rejects an existing editorial branch to preserve ongoing edits. Approval rejects non-drafts, unresolved reporting, missing text/byline/metadata, invalid URLs or missing verification.

To reject a source permanently, preserve its JSON with status=rejected under content/drafts on main via a PR. Simply deleting it can allow a future feed entry to reintroduce it.

## Persistence and publication safety

The scheduled workflow restores only JSON from automation/news-drafts into a clean main checkout. It never executes scripts from the queue branch. Successful collection updates the review branch with a compare-and-swap push. If one feed fails, successfully collected leads can still be saved and a 14-day workflow artifact provides recovery. Human edits should be committed on the queue branch and not made during an active collection run.

Prepare manual publication imports only the selected JSON, checks for already-published sources, runs approval and creates editorial/DRAFT_ID. It never merges main. Published content remains behind human review. GitHub bot-created PRs may not trigger additional workflows with the default token; human-created editorial PRs do. Main is tested and built on merge.

Only content/articles JSON with status=published and explicit reviewer/verification metadata enters the build. Drafts, excerpts, secrets and raw content JSON never enter dist. Repository visibility still controls access to editorial files: this repository is public, so do not put confidential notes in its drafts.

## Deployment

This repository is already deployed with GitHub Pages. Main changes trigger .github/workflows/pages.yml.

For a new GitHub repository, upload this folder's contents (including .github) at repository root. Select Settings → Pages → Source: GitHub Actions. The workflow derives https://OWNER.github.io/REPOSITORY automatically. Optional Actions variables: SITE_URL for a canonical/custom domain and DEPLOY_TARGET=github. For an account-root Pages repository, explicitly set SITE_URL=https://OWNER.github.io.

For Cloudflare Pages, connect the repository, choose framework None, build command python scripts/build.py, output dist, Python 3.12+, and build variables SITE_URL=https://YOUR_DOMAIN, PRODUCTION=1, INCLUDE_DEMOS=0. Set GitHub Actions DEPLOY_TARGET=cloudflare to skip GitHub Pages deployment, and SITE_URL to the same canonical URL for CI.

For a custom GitHub Pages domain, add static/CNAME with your domain, configure Pages/DNS, update SITE_URL and rebuild. See [GitHub workflow deployment](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) and [Cloudflare static hosting](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/).

## Site features, images and monetization

The portal includes six categories, trending/latest/featured sections, article pages, related reading, local search, theme switching, source attribution, sitemap, robots, canonical/Open Graph metadata and NewsArticle schema for reviewed production articles. Search indexes only published title/summary/tag metadata.

Original local SVG category illustrations have fixed dimensions, lazy secondary loading and explicit illustration credits. For a licensed photo, add it under static/assets and set image to its assets/... path, with image_alt and image_credit. Prefer optimized WebP/AVIF and confirm rights; source RSS images are never copied automatically. Use raster social images if your target platform does not support SVG Open Graph previews.

Before monetization, configure a working contact email and publisher identity, adapt the policy templates to actual practices, publish useful original reporting, and obtain network approval. [ADS.md](ADS.md) explains AdSense, Adsterra and Monetag adapter limitations, consent requirements, publisher codes and root-domain ads.txt. The built-in privacy choice is not a certified CMP; production ads require an external validated consent signal. No fake ad codes or intrusive formats are installed.

System fonts, static HTML and small local CSS/JS keep the critical path light. Measure actual Core Web Vitals after adding photos, a CMP and real ads; no unmeasured score is claimed. Keep trusted ad snippets/config protected, review dependencies and protect main. Legacy AI-assisted article disclosures remain supported, but no current collection or publication workflow invokes an AI service.
