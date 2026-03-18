#!/usr/bin/env python3
"""
Tool: scrape_single_site.py
Purpose: Fetch and extract text content from a single URL.
Usage: python tools/scrape_single_site.py --url <url> [--output <path>] [--delay <seconds>]
"""

import argparse
import json
import time
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies. Run: pip install requests beautifulsoup4")
    raise SystemExit(1)


def scrape(url: str, delay: float = 0) -> dict:
    if delay:
        time.sleep(delay)

    headers = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ""
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()

    return {
        "url": url,
        "title": title,
        "text": text,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def default_output_path(url: str) -> Path:
    domain = urlparse(url).netloc.replace(".", "_")
    return Path(".tmp") / f"scraped_{domain}.json"


def main():
    parser = argparse.ArgumentParser(description="Scrape a single website URL.")
    parser.add_argument("--url", required=True, help="Target URL to scrape")
    parser.add_argument("--output", help="Output file path (default: .tmp/scraped_<domain>.json)")
    parser.add_argument("--delay", type=float, default=0, help="Delay in seconds before fetching")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else default_output_path(args.url)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scraping: {args.url}")
    result = scrape(args.url, delay=args.delay)

    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Saved to: {output_path}")
    print(f"Title: {result['title']}")
    print(f"Text length: {len(result['text'])} chars")


if __name__ == "__main__":
    main()
