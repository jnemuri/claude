# Changelog

## 2026-03-23

### Fixed
- **HTML code fences in email** — Claude was wrapping output in ` ```html ``` ` markdown fences. Fixed `generate_newsletter.py` to strip these before saving the draft.
- **Beehiiv API enterprise-only** — The Create Post endpoint requires an enterprise plan. Switched to **Buttondown** (free API). Created `tools/post_to_buttondown.py`.
- **Buttondown first-send header** — First API send requires `X-Buttondown-Live-Dangerously: true` header. Added to `post_to_buttondown.py`.
- **Buttondown duplicate detection** — Buttondown rejects emails with identical subjects. Keep subject lines unique per issue (avoid re-sending same issue number without changing subject).
- **Beehiiv publication ID format** — Beehiiv expects `pub_xxxx` format, not raw UUIDs. Fixed by using correct ID from dashboard.
- **Scraper blocked by major finance sites** — Reuters, Bloomberg, WSJ, Barron's, 247wallst all return 401/403. Fixed by:
  - Updating `search_web.py` to target scraper-friendly sources (Investopedia, CNBC, Benzinga, NerdWallet, TechCrunch, Seeking Alpha, Motley Fool)
  - Adding Brave snippet fallback in `run_newsletter.py` — when full scrape fails, uses the search result description as content
- **Anthropic API credit error** — `400: credit balance too low` means the API key's account has no credits. Fix: add credits at console.anthropic.com or use a key from a funded account.

### Added
- `tools/post_to_buttondown.py` — Buttondown API integration (replaces Beehiiv)
- Brave snippet fallback in scraper pipeline — paywalled article descriptions still feed into generation
- `site:` targeted Brave queries for better source quality
- Box.com book insight step in pipeline (partially working — PDF folder traversal needs debugging)

### Known Issues
- **Box insight step fails** — `get_box_insight.py` can't find PDFs in the Box library folder traversal. Needs debugging.
- **WSJ/Barron's/MarketWatch site: query** returns 0 results from Brave Search. May need different query format.
- **Subscriber must exist** — Buttondown won't deliver emails if there are 0 subscribers. Add yourself first via the dashboard.

## 2026-03-23 (initial)

### Added
- Full newsletter pipeline: search → scrape → generate → post → self-critique
- macOS launchd scheduling (weekdays at 11 AM)
