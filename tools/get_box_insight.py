#!/usr/bin/env python3
"""
Tool: get_box_insight.py
Purpose: Pick a random book from the Box stock_market_books library and extract
         one actionable investment insight using Box AI.
Usage: python tools/get_box_insight.py [--output .tmp/box_insight.json]
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# Box API endpoints
BOX_API = "https://api.box.com/2.0"
BOX_AI_API = "https://api.box.com/2.0/ai/ask"

# Folder IDs for stock_market_books subfolders (001–059)
BOOK_FOLDER_IDS = [
    "10957030825", "10956901926", "10956758992", "10957006346", "10957172283",
    "10956913009", "10956893426", "10956631647", "10956577743", "10956614540",
    "10956863768", "10957037888", "10956650626", "10956976731", "10957339766",
    "10956487149", "10956214615", "10956977755", "10957340534", "10956712935",
    "10956765392", "10957389690", "10957273895", "10956616844", "10956643530",
    "10957390856", "10956600491", "10956952564", "10956809069", "10956988763",
]


def get_box_token() -> str:
    token = os.environ.get("BOX_ACCESS_TOKEN") or os.environ.get("BOX_TOKEN")
    if not token:
        raise SystemExit("ERROR: BOX_ACCESS_TOKEN not set in .env")
    return token


def list_pdfs_in_folder(folder_id: str, token: str) -> list[dict]:
    """List PDF files in a Box folder."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{BOX_API}/folders/{folder_id}/items",
        headers=headers,
        params={"fields": "id,name,type", "limit": 100},
        timeout=15,
    )
    resp.raise_for_status()
    return [
        item for item in resp.json().get("entries", [])
        if item["type"] == "file" and item["name"].lower().endswith(".pdf")
    ]


def extract_insight_via_box_ai(file_id: str, file_name: str, token: str) -> str:
    """Use Box AI to extract one actionable investment insight from a PDF."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "mode": "single_item_qa",
        "prompt": (
            "Extract ONE specific, actionable investment insight or trading strategy from this book. "
            "Format it as: a 1-sentence insight followed by 2-3 numbered steps a reader can take this week. "
            "Be concrete — cite specific concepts from the book, not generic advice."
        ),
        "items": [{"type": "file", "id": file_id}],
    }
    resp = requests.post(BOX_AI_API, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json().get("answer", "").strip()


def pick_random_book(token: str) -> tuple[str, str]:
    """Pick a random PDF from the Box library. Returns (file_id, file_name)."""
    # Try up to 5 random folders to find one with PDFs
    folder_ids = random.sample(BOOK_FOLDER_IDS, min(5, len(BOOK_FOLDER_IDS)))
    for folder_id in folder_ids:
        try:
            pdfs = list_pdfs_in_folder(folder_id, token)
            if pdfs:
                chosen = random.choice(pdfs)
                return chosen["id"], chosen["name"]
        except requests.HTTPError:
            continue
    raise SystemExit("ERROR: Could not find any PDFs in Box library after 5 attempts.")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Extract investment insight from Box book library.")
    parser.add_argument("--output", default=".tmp/box_insight.json")
    args = parser.parse_args()

    token = get_box_token()

    print("Picking a random book from Box library...")
    file_id, file_name = pick_random_book(token)
    print(f"  Selected: {file_name}")

    print("  Extracting insight via Box AI...")
    insight = extract_insight_via_box_ai(file_id, file_name, token)

    if not insight:
        print("  WARN: Box AI returned empty response. Skipping.")
        sys.exit(1)

    result = {
        "file_id": file_id,
        "book_title": file_name.replace(".pdf", ""),
        "insight": insight,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(f"  Insight saved -> {args.output}")
    print(f"  Book: {result['book_title']}")


if __name__ == "__main__":
    main()
