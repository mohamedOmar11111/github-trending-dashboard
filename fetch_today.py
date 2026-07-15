#!/usr/bin/env python3
"""
GitHub Trending Fetcher (CI-friendly).
Mirrors fetch_trending.ps1 logic in pure Python.
Fetches today's trending repos from GitHub API and writes a markdown report.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "github-trending-dashboard-bot",
}
if os.environ.get("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

AI_TERMS = (
    r"ai|llm|gpt|claude|agent|machine-learning|deep-learning|generative|"
    r"copilot|assistant|automation|dev-tool|developer-tool|cli|mcp"
)


def fetch_json(url: str, timeout: int = 30) -> dict | None:
    """GET a URL, return parsed JSON or None on error."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {url}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"  URL error for {url}: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"  Fetch failed for {url}: {e}", file=sys.stderr)
    return None


def get_repos(days: int, limit: int) -> list[dict]:
    """Fetch top repos created within `days` days, sorted by stars."""
    date_limit = (
        datetime.now(timezone.utc)
        .replace(hour=0, minute=0, second=0, microsecond=0)
    )
    from datetime import timedelta
    date_limit = (date_limit - timedelta(days=days)).strftime("%Y-%m-%d")
    q = f"created:>{date_limit}"
    url = (
        f"https://api.github.com/search/repositories?"
        f"q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page={limit}"
    )
    time.sleep(2)  # Respect rate limits
    data = fetch_json(url)
    return data.get("items", []) if data else []


def get_ai_repos(limit: int = 5) -> list[dict]:
    """Fetch AI/DEV trending by topic."""
    from datetime import timedelta
    date_limit = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).strftime("%Y-%m-%d")
    q = f"created:>{date_limit}+topic:ai+topic:llm+topic:agent"
    url = (
        f"https://api.github.com/search/repositories?"
        f"q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page={limit}"
    )
    time.sleep(2)
    data = fetch_json(url)
    return data.get("items", []) if data else []


def is_ai_dev(repo: dict) -> bool:
    """Check if a repo matches AI/DEV heuristic."""
    import re
    text = " ".join([
        str(repo.get("description") or ""),
        str(repo.get("full_name") or ""),
        " ".join(repo.get("topics") or []),
    ]).lower()
    return bool(re.search(AI_TERMS, text))


def fmt_stars(n: int) -> str:
    return f"{n:,}"


def render_section(title: str, repos: list[dict], tag_ai: bool = False) -> str:
    """Render one markdown section."""
    lines = [f"\n## {title}\n"]
    if not repos:
        lines.append("_No repos found._\n")
        return "".join(lines)
    for i, repo in enumerate(repos, 1):
        tag = " **[AI/DEV]**" if (tag_ai and is_ai_dev(repo)) else ""
        name = repo.get("full_name", "unknown/unknown")
        url = repo.get("html_url", "#")
        stars = fmt_stars(repo.get("stargazers_count", 0))
        lang = repo.get("language") or "Unknown"
        created = (repo.get("created_at") or "")[:10]
        topics = ", ".join(repo.get("topics") or [])
        desc = (repo.get("description") or "").replace("\n", " ").strip()
        lines.append(
            f"{i}. [{name}]({url}){tag} - {stars} stars, {lang}, "
            f"Created: {created}<br>"
            f"Topics: {topics}<br>"
            f"Description: {desc}\n"
        )
    return "".join(lines)


def main() -> int:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")
    output_file = os.path.join(SCRIPT_DIR, f"{date_str}-trending.md")

    # Idempotency: if today's report exists, skip.
    if os.path.exists(output_file):
        print(f"  Today's report already exists: {output_file}")
        return 0

    print(f"Fetching trending for {date_str}...")

    day_repos = get_repos(1, 5)
    week_repos = get_repos(7, 20)
    month_repos = get_repos(30, 5)
    ai_repos = get_ai_repos(5)

    if not week_repos and not day_repos:
        print("  No data fetched; aborting.", file=sys.stderr)
        return 1

    # Top AI pick = first AI-tagged weekly repo
    top_ai = next((r for r in week_repos if is_ai_dev(r)), None)
    ai_relevant_count = sum(1 for r in week_repos if is_ai_dev(r))

    md = f"# GitHub Trending - {date_str} ({day_of_week})\n\n"
    md += render_section("Top 20 Trending This Week", week_repos, tag_ai=True)
    md += render_section("Top 5 Trending This Last 24 Hours", day_repos)
    md += render_section("Top 5 AI/DEV Specific Trending", ai_repos)
    md += render_section("Top 5 Trending This Month", month_repos)

    md += "\n## Content Radar\n"
    md += f"- **{ai_relevant_count}** AI/DEV-relevant repos out of {len(week_repos)} this week."
    if top_ai:
        md += (
            f"\n- **Top AI Pick**: [{top_ai.get('full_name','')}]"
            f"({top_ai.get('html_url','')}) "
            f"({fmt_stars(top_ai.get('stargazers_count', 0))} stars) - "
            f"{top_ai.get('description','') or ''}"
        )
    md += "\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"  Wrote {output_file}")
    print(f"  Week repos: {len(week_repos)}, AI-tagged: {ai_relevant_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
