# GitHub Trending Library

A daily-updated, searchable dashboard of GitHub's trending repositories. New data is fetched automatically every day at 06:00 UTC via GitHub Actions.

## Live Site
https://mohamedOmar11111.github.io/github-trending-dashboard/dashboard.html

## Features
- **Overview** — Stats cards, language distribution, avg stars over time, top 5 all-time
- **Browse** — Full search by name/description/topics, sort, filter by language/date
- **AI/DEV filter** — One-click view of AI-tagged repos
- **Top All-Time** — Top 50 repos by stars
- **Repo Cards** — Click any card for full detail modal
- **Dark theme** — Glassmorphism UI

## Architecture
```
GitHub API  →  fetch_today.py  →  *.md  →  extract_data.py  →  trending_data.json
                                                                        ↓
                                              GitHub Pages  ←  dashboard.html
```
- **Source data:** GitHub REST API (no token required for public read; 60 req/h)
- **Storage:** Markdown reports committed per day + a single `trending_data.json` dataset
- **Refresh:** Scheduled GitHub Action (cron: `0 6 * * *`) or manual trigger
- **Hosting:** GitHub Pages, served from `main` branch root

## Local Use
```bash
# 1. Extract data from existing markdown files
python extract_data.py

# 2. Launch local dashboard
python serve.py
# Opens http://localhost:8080/dashboard.html
```

## Repo Structure
```
├── dashboard.html              # Single-file SPA (Chart.js via CDN)
├── extract_data.py             # Markdown → JSON parser
├── fetch_today.py              # CI fetcher (Python)
├── fetch_trending.ps1          # Local fetcher (PowerShell, Windows)
├── serve.py                    # Local HTTP server
├── trending_data.json          # Generated dataset
├── 2026-*-trending.md          # Daily reports
├── .github/workflows/daily.yml # Cron + manual trigger
└── LICENSE                     # MIT
```

## License
MIT
