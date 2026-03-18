# Workflow: Weekly Business & Finance Newsletter

## Objective
Produce and publish a polished HTML newsletter ("Capital Signal") to Beehiiv every Monday at 9am. The newsletter covers business/finance news, market insights, and income strategy tips. Each issue self-improves by incorporating critiques from prior runs.

## Required Inputs (all in `.env`)
- `BRAVE_SEARCH_API_KEY` — Brave Search API key
- `ANTHROPIC_API_KEY` — Claude API key
- `BEEHIIV_API_KEY` — Beehiiv API key
- `BEEHIIV_PUBLICATION_ID` — Beehiiv publication ID (format: `pub_xxxx...`)

## Schedule
Every Monday at 9:00 AM via launchd (`~/Library/LaunchAgents/com.josephnemuri.newsletter.plist`).

## Standard Run (automated)
```bash
python tools/run_newsletter.py --status confirmed
```

## Manual Run Options
```bash
# Test without posting to Beehiiv
python tools/run_newsletter.py --dry-run

# Post as draft for review in Beehiiv dashboard before publishing
python tools/run_newsletter.py --status draft

# Run individual steps for debugging
python tools/search_web.py --date 2026-03-17
python tools/generate_newsletter.py --issue-number 5
python tools/post_to_beehiiv.py --title "Capital Signal #5" --status draft
```

## Pipeline Steps (managed by orchestrator)
1. **Search** — `search_web.py` queries Brave Search with 5 targeted queries, deduplicates by URL, saves to `.tmp/search_results.json`
2. **Scrape** — `scrape_single_site.py` is called in a loop for each URL, results aggregated into `.tmp/scraped_articles.json`
3. **Generate** — `generate_newsletter.py` calls Claude API with research + past critiques, outputs HTML to `.tmp/newsletter_draft.html`
4. **Post** — `post_to_beehiiv.py` POSTs HTML to Beehiiv `POST /v2/publications/{pub_id}/posts`
5. **Log** — Orchestrator calls Claude for a self-critique, appends full entry to `.tmp/newsletter_log.json`

## Expected Outputs
| File | Description |
|---|---|
| `.tmp/search_results.json` | Raw search results (ephemeral, regenerated each run) |
| `.tmp/scraped_articles.json` | Article content for generation (ephemeral) |
| `.tmp/newsletter_draft.html` | Generated HTML (open in browser to preview) |
| `.tmp/last_post.json` | Beehiiv post ID and status |
| `.tmp/newsletter_log.json` | **Persistent** cumulative run log — never delete |

## Newsletter Structure
1. **Header** — "Capital Signal", issue #, date
2. **Top Stories** — 3–5 items with headline, 2-sentence summary, source link
3. **Market Insight** — 1 analytical paragraph on a macro trend
4. **Income Strategy Tip** — 1 actionable tip with numbered steps
5. **Footer** — Beehiiv auto-injects CAN-SPAM compliant unsubscribe

## Error Handling
| Error | Action |
|---|---|
| Brave API 429 | Wait 60s, retry once. If persists, skip search and use last `.tmp/search_results.json` |
| Scrape 403/timeout | Skip that URL, continue. Minimum 3 articles required to proceed |
| Claude API error | Retry once after 30s. If fails again, abort and check API key |
| Beehiiv 401 | Regenerate API key in Beehiiv dashboard → Settings → API |
| Beehiiv 422 | Debug info saved to `.tmp/beehiiv_error.json` — inspect payload |

## Important Notes
- **Never delete** `.tmp/newsletter_log.json` — it is the system's memory
- Beehiiv auto-injects unsubscribe footer. Do NOT include one in the HTML body
- HTML must be under 50KB or Beehiiv may truncate
- If the machine was asleep at 9am Monday, launchd will run the job when it wakes (unlike cron which silently skips)
- The issue number auto-increments from the log. No manual tracking needed
