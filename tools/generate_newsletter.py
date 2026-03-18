#!/usr/bin/env python3
"""
Tool: generate_newsletter.py
Purpose: Call Claude API to generate a polished HTML newsletter from scraped research.
         Injects past self-critiques to improve each iteration automatically.
Usage: python tools/generate_newsletter.py
         [--articles .tmp/scraped_articles.json]
         [--log .tmp/newsletter_log.json]
         [--output .tmp/newsletter_draft.html]
         [--issue-number 1]
         [--date "March 17, 2026"]
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

SYSTEM_PROMPT = """You are an expert business and finance newsletter writer.
Your newsletter is called "Capital Signal" — a weekly brief for smart professionals
who want concise, actionable market intelligence.

When generating the newsletter, you MUST follow these rules:
1. Output ONLY valid HTML. No markdown, no prose outside HTML tags.
2. Use ONLY inline CSS — no <style> blocks, no external stylesheets.
   (Email clients strip <head> styles, so everything must be inline.)
3. Follow this exact section order:
   a. Header: Publication name "Capital Signal", issue number, date, tagline
   b. Top Stories: 3–5 items, each with <h3> headline, 2-sentence summary, source link
   c. Market Insight: 1 analytical paragraph on a macro trend from the research
   d. Income Strategy Tip: 1 specific, actionable tip with 2–3 numbered steps
   e. Footer: "Thank you for reading Capital Signal." (Beehiiv auto-adds unsubscribe)
4. Max email width: 600px, centered with margin: 0 auto.
5. Color palette:
   - Page background: #f0f2f5
   - Header background: #1a2744
   - Header text: #ffffff
   - Accent / links: #c9a84c
   - Body background: #ffffff
   - Body text: #333333
6. Font: Arial, Helvetica, sans-serif throughout.
7. Do NOT fabricate facts. Only use information from the provided research.
8. Keep total HTML under 50KB.
9. Every external link must open in a new tab: target="_blank" rel="noopener".
"""


def build_user_prompt(
    articles: list[dict],
    log_entries: list[dict],
    pending_improvements: list[str],
    issue_number: int,
    date_str: str,
    box_insight: Optional[dict] = None,
) -> str:
    # Build research block (cap at 10 articles, 2000 chars each to stay within context)
    research_block = "\n\n---\n\n".join(
        f"SOURCE: {a.get('url', 'unknown')}\n"
        f"TITLE: {a.get('title', 'No title')}\n"
        f"CONTENT: {a.get('text', '')[:2000]}"
        for a in articles[:10]
        if a.get("text")
    )

    # Build improvement context from last 3 issues
    improvement_lines = []
    if log_entries:
        for entry in log_entries[-3:]:
            critique = entry.get("self_critique", "").strip()
            if critique:
                improvement_lines.append(
                    f"- Issue #{entry.get('issue_number')}: {critique}"
                )
    if pending_improvements:
        for tip in pending_improvements:
            improvement_lines.append(f"- Pending improvement: {tip}")

    improvement_block = ""
    if improvement_lines:
        improvement_block = (
            "SELF-CRITIQUE & IMPROVEMENTS (apply these in this issue):\n"
            + "\n".join(improvement_lines)
            + "\n\n"
        )

    box_block = ""
    if box_insight and box_insight.get("insight"):
        box_block = (
            f"INCOME STRATEGY TIP (sourced from book: \"{box_insight.get('book_title', 'unknown')}\"):\n"
            f"Use the following insight as the basis for the Income Strategy Tip section. "
            f"Keep it specific and actionable:\n"
            f"{box_insight['insight']}\n\n"
        )

    return f"""Generate issue #{issue_number} of Capital Signal for {date_str}.

{improvement_block}{box_block}RESEARCH MATERIAL ({len(articles)} articles):

{research_block}

Generate the complete HTML newsletter for issue #{issue_number} now. Output only HTML."""


def generate(
    articles: list[dict],
    log_entries: list[dict],
    pending_improvements: list[str],
    issue_number: int,
    date_str: str,
    api_key: str,
    box_insight: Optional[dict] = None,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = build_user_prompt(
        articles, log_entries, pending_improvements, issue_number, date_str, box_insight
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate HTML newsletter via Claude API.")
    parser.add_argument("--articles", default=".tmp/scraped_articles.json")
    parser.add_argument("--log", default=".tmp/newsletter_log.json")
    parser.add_argument("--output", default=".tmp/newsletter_draft.html")
    parser.add_argument("--issue-number", type=int, default=1)
    parser.add_argument("--date", default=datetime.now().strftime("%B %d, %Y"))
    parser.add_argument("--box-insight", default=None, help="Path to box_insight.json")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: ANTHROPIC_API_KEY not set in .env")

    # Load articles
    articles_path = Path(args.articles)
    if not articles_path.exists():
        raise SystemExit(f"ERROR: Articles file not found: {args.articles}")
    articles = json.loads(articles_path.read_text()).get("articles", [])
    if not articles:
        raise SystemExit("ERROR: No articles found. Run search + scrape steps first.")

    # Load log for self-improvement context
    log_entries = []
    pending_improvements = []
    log_path = Path(args.log)
    if log_path.exists():
        log_data = json.loads(log_path.read_text())
        log_entries = log_data.get("issues", [])
        pending_improvements = log_data.get("pending_improvements", [])

    # Load Box insight if provided
    box_insight = None
    if args.box_insight:
        box_insight_path = Path(args.box_insight)
        if box_insight_path.exists():
            box_insight = json.loads(box_insight_path.read_text())
            print(f"  Box insight: \"{box_insight.get('book_title', 'unknown')}\"")

    print(f"Generating issue #{args.issue_number} from {len(articles)} articles...")
    if log_entries:
        print(f"  Applying context from {min(3, len(log_entries))} previous issue(s)")

    html = generate(articles, log_entries, pending_improvements, args.issue_number, args.date, api_key, box_insight)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)

    print(f"Draft saved: {args.output} ({len(html):,} chars)")
    if len(html) > 50000:
        print("  WARN: HTML exceeds 50KB — Beehiiv may truncate. Consider shortening.")


if __name__ == "__main__":
    main()
