# Workflow: Scrape Website

## Objective
Extract content from one or more web pages and save the output for downstream processing.

## Required Inputs
- `url` — the target URL to scrape
- `output_file` (optional) — path to save results, defaults to `.tmp/scraped_{domain}.json`

## Steps

1. **Check for existing data**
   - Look in `.tmp/` for a recent scrape of the same domain
   - If fresh (< 24 hours), skip re-scraping and use cached data

2. **Run the scraper**
   ```
   python tools/scrape_single_site.py --url <url> --output <output_file>
   ```

3. **Validate output**
   - Confirm the output file exists and is non-empty
   - Check that key fields (title, body text) were captured
   - If empty or missing, inspect the site for JS rendering requirements

4. **Handle errors**
   - `403 / 429` — site is blocking requests; add `--delay` flag and retry
   - Empty body — site may require JavaScript; note this in the workflow and escalate
   - Timeout — retry once; if it persists, log and skip

## Expected Output
A JSON file at the specified path containing:
```json
{
  "url": "https://example.com",
  "title": "Page Title",
  "text": "Extracted body text...",
  "scraped_at": "2026-03-17T12:00:00Z"
}
```

## Notes
- Respect `robots.txt` — do not scrape disallowed paths
- Add a 1–2 second delay between requests when scraping multiple pages
- Update this workflow if rate limits or bot detection patterns are discovered
