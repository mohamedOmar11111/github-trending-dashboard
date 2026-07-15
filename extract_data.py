#!/usr/bin/env python3
"""
GitHub Trending Data Extractor
Parses all trending markdown files into a clean, structured JSON dataset.
"""

import os
import re
import json
from datetime import datetime
from collections import defaultdict

TRENDING_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(TRENDING_DIR, "trending_data.json")

# Sections we know about
SECTION_PATTERNS = {
    "weekly": r"## Top 20 Trending This Week",
    "daily": r"## Top 5 Trending This Last 24 Hours",
    "aidev": r"## Top 5 AI/DEV Specific Trending",
    "monthly": r"## Top 5 Trending This Month",
}

REPO_PATTERN = re.compile(
    r"^\d+\.\s+\[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)"
    r"(?:\s+\*\*\[(?P<tags>[^\]]*)\]\*\*)?"
    r"\s*-\s*(?P<stars>[\d,]+)\s+stars,"
    r"\s*(?P<language>[^,]*),"
    r"\s*Created:\s*(?P<created>[^<\n]+)"
    r"(?:<br>(?:Topics:\s*(?P<topics>[^<]*))?)?"
    r"(?:<br>)?"
    r"(?:Description:\s*(?P<description>.*))?"
)

CONTENT_RADAR_PATTERN = re.compile(
    r"\*\*(?P<count>\d+)\*\* AI/DEV-relevant repos out of"
)
TOP_AI_PICK_PATTERN = re.compile(
    r"\*\*Top AI Pick\*\*:\s+\[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)\s+\((?P<stars>[\d,]+)\s+stars\)\s*-\s*(?P<description>.*)"
)


def parse_markdown_file(filepath: str) -> list[dict]:
    """Parse a single markdown file and return list of repos found."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    repos = []
    lines = content.split("\n")
    current_section = None
    date_str = os.path.basename(filepath)[:10]

    # Extract content radar
    radar_match = CONTENT_RADAR_PATTERN.search(content)
    ai_relevant_count = int(radar_match.group("count")) if radar_match else 0

    top_ai_pick = None
    top_ai_match = TOP_AI_PICK_PATTERN.search(content)
    if top_ai_match:
        top_ai_pick = {
            "name": top_ai_match.group("name"),
            "url": top_ai_match.group("url"),
            "stars": int(top_ai_match.group("stars").replace(",", "")),
            "description": top_ai_match.group("description").strip(),
        }

    for line in lines:
        # Detect section headers
        for section_key, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, line):
                current_section = section_key
                break

        match = REPO_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            tags = groups.get("tags") or ""
            topics_raw = groups.get("topics") or ""

            repo = {
                "name": groups["name"].strip(),
                "url": groups["url"].strip(),
                "stars": int(groups["stars"].replace(",", "")),
                "language": groups["language"].strip() if groups.get("language") else "",
                "created": groups["created"].strip() if groups.get("created") else "",
                "topics": [t.strip() for t in topics_raw.split(",") if t.strip()],
                "description": groups["description"].strip() if groups.get("description") else "",
                "date": date_str,
                "section": current_section,
                "is_ai_dev": "[AI/DEV]" in tags,
            }
            repos.append(repo)

    return repos, {"date": date_str, "ai_relevant_count": ai_relevant_count, "top_ai_pick": top_ai_pick}


def extract_all() -> dict:
    """Extract all trending data from all markdown files."""
    all_repos = []
    all_metadata = {}
    seen_repos = set()  # Deduplicate by (name, date)

    files = sorted(
        [f for f in os.listdir(TRENDING_DIR) if f.endswith("-trending.md")],
        reverse=True,
    )

    for filename in files:
        filepath = os.path.join(TRENDING_DIR, filename)
        repos, metadata = parse_markdown_file(filepath)

        # Deduplicate
        for repo in repos:
            key = (repo["name"], repo["date"])
            if key not in seen_repos:
                seen_repos.add(key)
                all_repos.append(repo)

        all_metadata[metadata["date"]] = {
            "ai_relevant_count": metadata["ai_relevant_count"],
            "top_ai_pick": metadata["top_ai_pick"],
        }

    # Build language stats
    language_stats = defaultdict(lambda: {"count": 0, "total_stars": 0, "repos": []})
    for repo in all_repos:
        lang = repo["language"] or "Unknown"
        language_stats[lang]["count"] += 1
        language_stats[lang]["total_stars"] += repo["stars"]
        language_stats[lang]["repos"].append(repo["name"])

    # Sort languages by count
    language_stats = dict(
        sorted(language_stats.items(), key=lambda x: x[1]["count"], reverse=True)
    )

    # Build date stats
    date_stats = defaultdict(lambda: {"count": 0, "total_stars": 0, "ai_count": 0})
    for repo in all_repos:
        date_stats[repo["date"]]["count"] += 1
        date_stats[repo["date"]]["total_stars"] += repo["stars"]
        if repo["is_ai_dev"]:
            date_stats[repo["date"]]["ai_count"] += 1

    # Top repos ever
    all_stars_sorted = sorted(all_repos, key=lambda r: r["stars"], reverse=True)[:50]

    output = {
        "last_updated": datetime.now().isoformat(),
        "total_repos": len(all_repos),
        "total_dates": len(all_metadata),
        "total_unique_languages": len(language_stats),
        "repos": all_repos,
        "metadata": all_metadata,
        "language_stats": dict(language_stats),
        "date_stats": dict(
            sorted(date_stats.items(), reverse=True)
        ),
        "top_50_all_time": all_stars_sorted,
    }

    return output


if __name__ == "__main__":
    print("📊 Extracting GitHub trending data...")
    data = extract_all()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Extracted {data['total_repos']} repos from {data['total_dates']} dates")
    print(f"   Languages: {data['total_unique_languages']}")
    print(f"   Output: {OUTPUT_FILE}")
