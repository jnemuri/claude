#!/usr/bin/env python3
"""
Tool: post_to_beehiiv.py
Purpose: POST a newsletter HTML draft to Beehiiv as a new post.
API: POST https://api.beehiiv.com/v2/publications/{pub_id}/posts
Usage: python tools/post_to_beehiiv.py
         --title "Capital Signal #1: ..."
         [--html .tmp/newsletter_draft.html]
         [--status draft|confirmed]
         [--subtitle "Your weekly business & finance brief"]
         [--output .tmp/last_post.json]
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

BEEHIIV_BASE = "https://api.beehiiv.com/v2"


def post_to_beehiiv(
    title: str,
    html_body: str,
    subtitle: str,
    api_key: str,
    pub_id: str,
    status: str = "draft",
) -> dict:
    """POST a new issue to Beehiiv. Returns the API response dict."""
    url = f"{BEEHIIV_BASE}/publications/{pub_id}/posts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "subtitle": subtitle,
        "body_content": html_body,
        "status": status,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code == 422:
        # Save request body for debugging
        Path(".tmp/beehiiv_error.json").write_text(
            json.dumps({"payload": payload, "response": response.text}, indent=2)
        )
        print("ERROR: Beehiiv 422. Debug info saved to .tmp/beehiiv_error.json")

    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Post newsletter HTML to Beehiiv.")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--html", default=".tmp/newsletter_draft.html")
    parser.add_argument(
        "--status", default="draft", choices=["draft", "confirmed"],
        help="'draft' to review in dashboard, 'confirmed' to publish"
    )
    parser.add_argument("--subtitle", default="Your weekly business & finance brief")
    parser.add_argument("--output", default=".tmp/last_post.json")
    args = parser.parse_args()

    api_key = os.environ.get("BEEHIIV_API_KEY")
    pub_id = os.environ.get("BEEHIIV_PUBLICATION_ID")
    if not api_key or not pub_id:
        raise SystemExit("ERROR: BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID must be set in .env")

    html_path = Path(args.html)
    if not html_path.exists():
        raise SystemExit(f"ERROR: HTML file not found: {args.html}")
    html_body = html_path.read_text()

    print(f"Posting to Beehiiv (status={args.status})...")
    print(f"  Title: {args.title}")
    print(f"  HTML size: {len(html_body):,} chars")

    result = post_to_beehiiv(args.title, html_body, args.subtitle, api_key, pub_id, args.status)

    post_id = result.get("data", {}).get("id", "unknown")
    output = {
        "post_id": post_id,
        "title": args.title,
        "status": args.status,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    Path(args.output).write_text(json.dumps(output, indent=2))
    print(f"Posted successfully. Post ID: {post_id}")
    print(f"  -> Log saved: {args.output}")


if __name__ == "__main__":
    main()
