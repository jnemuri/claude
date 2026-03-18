#!/usr/bin/env python3
"""
Tool: search_web.py
Purpose: Query Brave Search API for top business/finance news to research the weekly newsletter.
Usage: python tools/search_web.py [--output .tmp/search_results.json] [--date YYYY-MM-DD]
"""

import argparse
import json
import time
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

WEEKLY_QUERIES = [
    # General market — prefers open sites (Benzinga, Yahoo Finance, Investopedia)
    "stock market weekly recap {date} site:benzinga.com OR site:finance.yahoo.com OR site:investopedia.com",
    "business finance news this week {date} site:benzinga.com OR site:marketwatch.com OR site:cnbc.com",
    # Passive income & strategy — Investopedia and NerdWallet are scraper-friendly
    "passive income investing strategy tips {date} site:investopedia.com OR site:nerdwallet.com OR site:benzinga.com",
    # VC / startup — open sources
    "startup venture capital funding news {date} site:techcrunch.com OR site:crunchbase.com OR site:benzinga.com",
    # Macro — broad query to catch WSJ/Barron's/MarketWatch snippets via Brave
    "global economy macro trends investing {date} site:wsj.com OR site:barrons.com OR site:marketwatch.com",
    # Fallback broad queries to fill gaps
    "stock market outlook this week {date}",
    "top investment ideas {date} site:seekingalpha.com OR site:motleyfool.com",
]


def search(query: str, api_key: str, count: int = 3) -> list[dict]:
    """Execute a single Brave Search query. Returns list of {title, url, description}."""
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    params = {"q": query, "count": count, "country": "us", "search_lang": "en"}
    response = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("web", {}).get("results", [])
    return [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "description": r.get("description", ""),
        }
        for r in results
    ]


def run_all_queries(api_key: str, date_str: str) -> list[dict]:
    """Run all weekly queries, deduplicate by URL, return combined results."""
    all_results = []
    seen_urls = set()

    for query_template in WEEKLY_QUERIES:
        query = query_template.format(date=date_str)
        try:
            results = search(query, api_key)
            for r in results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append({**r, "query": query})
            print(f"  Query: '{query}' -> {len(results)} results")
        except requests.HTTPError as e:
            print(f"  WARN: Query failed ({query}): {e}")
        time.sleep(1.2)  # Stay under 1 req/sec with buffer

    return all_results


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Search Brave for business/finance news.")
    parser.add_argument("--output", default=".tmp/search_results.json")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: BRAVE_SEARCH_API_KEY not set in .env")

    print(f"Searching for business/finance news ({args.date})...")
    results = run_all_queries(api_key, args.date)

    output = {
        "date": args.date,
        "result_count": len(results),
        "results": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, indent=2))
    print(f"\nFound {len(results)} unique results -> {args.output}")


if __name__ == "__main__":
    main()
