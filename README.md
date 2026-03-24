# Capital Signal

Automated business & finance newsletter powered by the WAT framework (Workflows, Agents, Tools).

## How It Works

1. **Search** — Queries Brave Search API for business/finance news from Investopedia, CNBC, Benzinga, TechCrunch, NerdWallet, Seeking Alpha, Motley Fool
2. **Scrape** — Extracts full article text; falls back to Brave snippets for paywalled sites (WSJ, Barron's, MarketWatch)
3. **Generate** — Claude API produces a styled HTML newsletter with market recap, key stories, income strategy tip, and VC/startup section
4. **Publish** — Posts to Buttondown, which emails all subscribers
5. **Self-Critique** — Claude reviews the issue and logs improvements for next time

## Schedule

Runs **Monday–Friday at 11:00 AM** via macOS launchd.

## Setup

### Requirements
```bash
pip install -r requirements.txt
```

### Environment Variables (`.env`)
```
BRAVE_SEARCH_API_KEY=...
ANTHROPIC_API_KEY=...
BUTTONDOWN_API_KEY=...
```

### Run
```bash
# Dry run (no email sent)
python tools/run_newsletter.py --dry-run

# Live send
python tools/run_newsletter.py --status confirmed
```

## Project Structure

```
tools/
  run_newsletter.py        # Master orchestrator
  search_web.py            # Brave Search queries
  scrape_single_site.py    # Article scraper with snippet fallback
  generate_newsletter.py   # Claude API HTML generation
  post_to_buttondown.py    # Buttondown API publishing
  get_box_insight.py       # Box library integration (WIP)
workflows/
  newsletter_weekly.md     # Full pipeline SOP
  newsletter_improve.md    # Self-improvement feedback loop
.tmp/                      # Intermediate files (gitignored)
```
