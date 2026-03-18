# Workflow: Newsletter Self-Improvement Loop

## Objective
48–72 hours after each issue publishes, backfill performance stats from Beehiiv and generate concrete improvement suggestions for the next issue. This closes the feedback loop automatically.

## When to Run
Every Wednesday at 9:00 AM (48h after Monday publish, when open rates have stabilized).

Schedule via launchd: `~/Library/LaunchAgents/com.josephnemuri.newsletter-improve.plist`

Or run manually after any issue:
```bash
python tools/improve_newsletter.py
```

## Steps

### Step 1 — Backfill Open & Click Rates
Call the Beehiiv Get Post endpoint to fetch stats for the last published issue:
```
GET https://api.beehiiv.com/v2/publications/{pub_id}/posts/{post_id}?expand[]=stats
```
Parse:
- `data.stats.email.open_rate` → percentage (e.g., 24.1)
- `data.stats.email.click_rate` → percentage (e.g., 2.3)

Update the matching entry in `.tmp/newsletter_log.json` with these values.

### Step 2 — Analyze Recent Performance
Read `.tmp/newsletter_log.json`. Extract the last 3–5 issues with:
- `self_critique`
- `open_rate`
- `click_rate`
- `topics_covered`

### Step 3 — Generate Improvement Plan
Send the performance summary to Claude with this prompt:
> "Based on these newsletter issues and their performance stats, suggest exactly 3 specific, concrete improvements for next week's issue. Focus on what will most improve open rate and click rate. Format as a JSON array of 3 strings."

Save the 3 improvements to `.tmp/newsletter_log.json` under the top-level key `pending_improvements`.

### Step 4 — Verify
Confirm that `.tmp/newsletter_log.json` now contains:
- Non-null `open_rate` and `click_rate` on the latest issue entry
- A `pending_improvements` array with 3 items

## How Improvements Feed Back Into Generation
`run_newsletter.py` passes `pending_improvements` to `generate_newsletter.py`, which injects them into the Claude generation prompt alongside the last 3 `self_critique` entries. The improvements are automatically cleared from the log after being applied.

## Performance Benchmarks (goals to work toward)
| Metric | Good | Great |
|---|---|---|
| Open rate | >25% | >40% |
| Click rate | >2% | >5% |
| Issue length | 800–1200 words | — |

## Improvement Triggers
| Condition | Focus area |
|---|---|
| Open rate < 20% | Subject line, preview text, send time |
| Click rate < 2% | CTAs, Income Strategy Tip specificity, link placement |
| Consistent low open rate | Audience targeting, topic relevance |
| Self-critique mentions same issue 2+ weeks | Escalate — fix the system prompt in `generate_newsletter.py` |

## Notes
- The `improvements_applied` field in each log entry tracks which `pending_improvements` were active during that run — useful for attribution
- If Beehiiv stats show 0 for open/click rate 48h after publish, the issue may not have been sent yet — check the Beehiiv dashboard
- Keep the log trimmed to the last 52 entries (1 year) to prevent unbounded growth
