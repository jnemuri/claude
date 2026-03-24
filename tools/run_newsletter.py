#!/usr/bin/env python3
"""
Tool: run_newsletter.py
Purpose: Master orchestrator for the weekly newsletter pipeline.
         Runs search -> scrape -> generate -> post -> log -> self-critique.
Usage: python tools/run_newsletter.py [--dry-run] [--status draft|confirmed]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent


def run_tool(cmd: list[str]) -> int:
    """Run a tool script as a subprocess from the project root. Returns exit code."""
    full_cmd = [sys.executable] + cmd
    print(f"  -> {' '.join(full_cmd)}")
    result = subprocess.run(full_cmd, cwd=ROOT)
    return result.returncode


def load_log() -> dict:
    log_path = ROOT / ".tmp" / "newsletter_log.json"
    if log_path.exists():
        return json.loads(log_path.read_text())
    return {"issues": [], "pending_improvements": []}


def save_log(log: dict):
    log_path = ROOT / ".tmp" / "newsletter_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, indent=2))


def generate_self_critique(html_content: str, topics: list[str], api_key: str) -> str:
    """Ask Claude for a 2-3 sentence critique of the current issue."""
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    "Review this newsletter issue and write a 2–3 sentence self-critique. "
                    "Be specific. Focus on: content quality, section balance, actionability "
                    "of the Income Strategy Tip, and one concrete thing to improve next week.\n\n"
                    f"Topics covered: {', '.join(topics[:5])}\n\n"
                    f"Newsletter HTML (first 3000 chars):\n{html_content[:3000]}\n\n"
                    "Reply with ONLY the critique text, no preamble."
                ),
            }
        ],
    )
    return message.content[0].text.strip()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the weekly newsletter pipeline.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run all steps except posting to Beehiiv"
    )
    parser.add_argument(
        "--status", default="confirmed", choices=["draft", "confirmed"],
        help="Beehiiv post status (default: confirmed)"
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: ANTHROPIC_API_KEY not set in .env")

    log = load_log()
    issue_number = len(log["issues"]) + 1
    date_str = datetime.now().strftime("%Y-%m-%d")
    display_date = datetime.now().strftime("%B %d, %Y")
    title = f"Capital Signal #{issue_number}: Weekly Business & Finance Brief — {display_date}"
    errors = []

    print(f"\n{'='*55}")
    print(f"  Capital Signal | Issue #{issue_number} | {display_date}")
    print(f"{'='*55}\n")

    # ── Step 1: Search ──────────────────────────────────────
    print("[1/5] Searching for business/finance news...")
    rc = run_tool(["tools/search_web.py", "--date", date_str])
    if rc != 0:
        errors.append("search_web failed")
        print("  WARN: Search failed. Checking for cached results...")

    search_results_path = ROOT / ".tmp" / "search_results.json"
    if not search_results_path.exists():
        raise SystemExit("ERROR: No search results available. Cannot continue.")
    search_data = json.loads(search_results_path.read_text())
    result_urls = [r["url"] for r in search_data.get("results", [])]
    print(f"  Found {len(result_urls)} URLs to scrape\n")

    # ── Step 2: Scrape ──────────────────────────────────────
    print("[2/5] Scraping articles...")
    scraped = []
    for i, item in enumerate(search_data.get("results", [])[:10]):
        url = item["url"]
        out_path = f".tmp/scrape_{i}.json"
        rc = run_tool([
            "tools/scrape_single_site.py",
            "--url", url,
            "--output", out_path,
            "--delay", "1.5",
        ])
        if rc == 0:
            try:
                data = json.loads((ROOT / out_path).read_text())
                if data.get("text") and len(data["text"]) > 200:
                    scraped.append(data)
                    continue
            except Exception:
                pass
        # Scrape failed — use Brave search description as fallback content
        description = item.get("description", "").strip()
        title = item.get("title", "").strip()
        if description and len(description) > 50:
            scraped.append({
                "url": url,
                "title": title,
                "text": f"{title}. {description}",
                "source": "brave_snippet",
            })
            print(f"  (used Brave snippet for: {url[:60]}...)")

    if len(scraped) < 3:
        errors.append(f"Only {len(scraped)} articles scraped (minimum 3 required)")
        raise SystemExit(f"ERROR: Only {len(scraped)} usable articles. Too few to generate newsletter.")

    scraped_path = ROOT / ".tmp" / "scraped_articles.json"
    scraped_path.write_text(json.dumps({"articles": scraped, "date": date_str}, indent=2))
    print(f"  Scraped {len(scraped)} usable articles\n")

    # ── Step 2b: Box Insight ─────────────────────────────────
    box_insight_path = ROOT / ".tmp" / "box_insight.json"
    print("[2b/5] Pulling investment insight from Box library...")
    rc_box = run_tool(["tools/get_box_insight.py"])
    if rc_box != 0:
        print("  WARN: Box insight skipped (will use Claude's own Income Strategy Tip)\n")
    else:
        print()

    # ── Step 3: Generate ────────────────────────────────────
    print("[3/5] Generating newsletter HTML via Claude...")
    generate_cmd = [
        "tools/generate_newsletter.py",
        "--issue-number", str(issue_number),
        "--date", display_date,
    ]
    if box_insight_path.exists():
        generate_cmd += ["--box-insight", str(box_insight_path)]
    rc = run_tool(generate_cmd)
    if rc != 0:
        errors.append("generate_newsletter failed")
        raise SystemExit("ERROR: Newsletter generation failed. Cannot continue.")

    draft_path = ROOT / ".tmp" / "newsletter_draft.html"
    html_content = draft_path.read_text()
    print(f"  Draft: {len(html_content):,} chars\n")

    # ── Step 4: Post ────────────────────────────────────────
    post_id = "dry-run"
    if args.dry_run:
        print("[4/5] Skipping Buttondown post (--dry-run)\n")
    else:
        bd_status = "about_to_send" if args.status == "confirmed" else "draft"
        print(f"[4/5] Posting to Buttondown (status={bd_status})...")
        rc = run_tool([
            "tools/post_to_buttondown.py",
            "--subject", title,
            "--status", bd_status,
        ])
        if rc != 0:
            errors.append("post_to_buttondown failed")
            print("  ERROR: Post failed. Draft saved locally.\n")
        else:
            try:
                post_id = json.loads((ROOT / ".tmp" / "last_post.json").read_text()).get("post_id", "unknown")
            except Exception:
                post_id = "unknown"
            print()

    # ── Step 5: Self-critique + Log ─────────────────────────
    print("[5/5] Generating self-critique and logging run...")
    topics = [r.get("title", "") for r in search_data.get("results", [])[:5]]
    critique = generate_self_critique(html_content, topics, api_key)

    entry = {
        "issue_number": issue_number,
        "date": date_str,
        "topics_covered": topics,
        "articles_scraped": len(scraped),
        "post_id": post_id,
        "status": args.status if not args.dry_run else "dry-run",
        "open_rate": None,
        "click_rate": None,
        "self_critique": critique,
        "improvements_applied": log.get("pending_improvements", []),
        "run_at": datetime.now(timezone.utc).isoformat(),
        "errors": errors,
    }
    log["issues"].append(entry)
    log["pending_improvements"] = []  # Clear after applying
    save_log(log)

    print(f"\n{'='*55}")
    print(f"  Issue #{issue_number} complete {'(DRY RUN)' if args.dry_run else ''}")
    print(f"  Post ID : {post_id}")
    print(f"  Errors  : {errors or 'none'}")
    print(f"  Critique: {critique[:120]}...")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
