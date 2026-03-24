# Changelog

All notable changes to Capital Signal are documented here.

## 2026-03-23 — Session 2: Buttondown Migration & Fixes

### Added
- `tools/post_to_buttondown.py` — Buttondown API integration (replaces Beehiiv)
- `README.md` — project overview, setup instructions, and structure
- `CHANGELOG.md` — this file

### Changed
- **Email provider: Beehiiv → Buttondown** — Beehiiv's Create Post API is enterprise-only ($$$). Buttondown's free tier has full API access.
- **Schedule: Monday 11 AM → Weekdays (Mon–Fri) 11 AM** — user requested daily weekday delivery for testing/iteration.
- `run_newsletter.py` — step 4 now calls `post_to_buttondown.py` instead of `post_to_beehiiv.py`. Maps `--status confirmed` to Buttondown's `about_to_send`.

### Fixed
- **HTML code fences in email body** — Claude wrapped output in ` ```html ``` ` markdown fences, which rendered as literal text in the email. Added stripping logic in `generate_newsletter.py` (line 129).
- **Buttondown first-send rejection** — First API call with `status: about_to_send` requires `X-Buttondown-Live-Dangerously: true` header. Added to `post_to_buttondown.py`.
- **Buttondown duplicate email rejection** — Buttondown rejects emails with identical subjects. Lesson: keep subject lines unique per issue.
- **Beehiiv publication ID format** — Beehiiv expects `pub_xxxx` prefix, not raw UUIDs. Fixed by using correct ID from dashboard.
- **No subscribers = no delivery** — Buttondown silently succeeds but delivers to nobody if subscriber list is empty. Must add at least one subscriber via dashboard first.

### Known Issues
- `get_box_insight.py` — Box PDF folder traversal fails. Can't find PDFs across the 59 subfolders. Needs debugging.
- WSJ/Barron's/MarketWatch `site:` Brave query returns 0 results. May need different query format.

---

## 2026-03-23 — Session 1: Pipeline Build & First Run

### Added
- **Complete newsletter pipeline** built from scratch using WAT framework:
  - `tools/run_newsletter.py` — master orchestrator (search → scrape → generate → post → self-critique → log)
  - `tools/search_web.py` — Brave Search API queries for business/finance news
  - `tools/scrape_single_site.py` — article scraper using requests + BeautifulSoup
  - `tools/generate_newsletter.py` — Claude API (claude-sonnet-4-6) generates styled HTML newsletter
  - `tools/post_to_beehiiv.py` — Beehiiv API posting (later replaced by Buttondown)
  - `tools/get_box_insight.py` — Box.com library integration to pull investment tips from user's finance book collection
- `workflows/newsletter_weekly.md` — full pipeline SOP
- `workflows/newsletter_improve.md` — Wednesday self-improvement feedback loop
- `workflows/scrape_website.md` — general web scraping SOP
- `CLAUDE.md` — WAT framework instructions and project conventions
- `.gitignore` — excludes `.env`, `.venv/`, `.tmp/`, credentials
- `requirements.txt` — Python dependencies
- macOS launchd schedule (`~/Library/LaunchAgents/com.josephnemuri.newsletter.plist`)
- Git repo initialized and pushed to `github.com/jnemuri/claude`

### Fixed (during first dry runs)
- **Anthropic API credit error** — `400: credit balance too low`. Cause: API key belonged to an account with no credits. Fixed by adding credits and generating a new key on the funded account.
- **Major finance sites blocking scraper (401/403)** — Reuters, Bloomberg, WSJ, Barron's, TheStreet, 247wallst all block simple HTTP requests. Fixed two ways:
  1. Updated `search_web.py` queries to target scraper-friendly sources: Investopedia, CNBC, Benzinga, NerdWallet, TechCrunch, Seeking Alpha, Motley Fool
  2. Added Brave snippet fallback in `run_newsletter.py` — when full scrape fails, uses the Brave search result description as content so paywalled article context isn't lost entirely
- **Scrape success rate: 3/10 → 10/10** after source targeting fix
- **Only 3 articles → hallucinated content** — When only 3 low-quality articles were available, Claude fabricated stories (e.g. "RoboForce" funding round). Self-critique caught this. Fix: better sources + snippet fallback ensures enough real content.

### Environment Setup
- `BRAVE_SEARCH_API_KEY` — Brave Search API ($5/1,000 requests, ~$0.025/newsletter run)
- `ANTHROPIC_API_KEY` — Claude API for newsletter generation + self-critique
- `BEEHIIV_API_KEY` + `BEEHIIV_PUBLICATION_ID` — later replaced by Buttondown
- `BUTTONDOWN_API_KEY` — current email provider
