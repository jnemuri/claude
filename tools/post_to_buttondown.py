#!/usr/bin/env python3
"""
Tool: post_to_buttondown.py
Purpose: POST a newsletter HTML draft to Buttondown as a new email.
API: POST https://api.buttondown.com/v1/emails
Usage: python tools/post_to_buttondown.py
         --subject "Capital Signal #1: ..."
         [--html .tmp/newsletter_draft.html]
         [--status draft|about_to_send]
         [--output .tmp/last_post.json]
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

BUTTONDOWN_API = "https://api.buttondown.com/v1/emails"


def post_to_buttondown(
    subject: str,
    html_body: str,
    api_key: str,
    status: str = "draft",
) -> dict:
    """POST a new email to Buttondown. Returns the API response dict."""
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "X-Buttondown-Live-Dangerously": "true",
    }
    payload = {
        "subject": subject,
        "body": html_body,
        "status": status,
    }
    response = requests.post(BUTTONDOWN_API, json=payload, headers=headers, timeout=30)

    if not response.ok:
        Path(".tmp/buttondown_error.json").write_text(
            json.dumps({"status": response.status_code, "response": response.text}, indent=2)
        )
        print(f"ERROR: Buttondown {response.status_code}. Debug info saved to .tmp/buttondown_error.json")

    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Post newsletter HTML to Buttondown.")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--html", default=".tmp/newsletter_draft.html")
    parser.add_argument(
        "--status", default="draft", choices=["draft", "about_to_send"],
        help="'draft' to review first, 'about_to_send' to publish immediately"
    )
    parser.add_argument("--output", default=".tmp/last_post.json")
    args = parser.parse_args()

    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: BUTTONDOWN_API_KEY not set in .env")

    html_path = Path(args.html)
    if not html_path.exists():
        raise SystemExit(f"ERROR: HTML file not found: {args.html}")
    html_body = html_path.read_text()

    print(f"Posting to Buttondown (status={args.status})...")
    print(f"  Subject: {args.subject}")
    print(f"  HTML size: {len(html_body):,} chars")

    result = post_to_buttondown(args.subject, html_body, api_key, args.status)

    post_id = result.get("id", "unknown")
    output = {
        "post_id": post_id,
        "subject": args.subject,
        "status": args.status,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    Path(args.output).write_text(json.dumps(output, indent=2))
    print(f"Posted successfully. Email ID: {post_id}")
    print(f"  -> Log saved: {args.output}")


if __name__ == "__main__":
    main()
