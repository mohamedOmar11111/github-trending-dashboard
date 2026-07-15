#!/usr/bin/env python3
"""
GitHub Trending Library Server
Serves the dashboard HTML and extracted trending data.
"""

import http.server
import socketserver
import os
import sys
import webbrowser
import json

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, format, *args):
        if len(args) >= 3:
            print(f"  {args[0]} {args[1]} {args[2]}")

    def end_headers(self):
        # CORS headers for local dev
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def main():
    # First, ensure data is extracted
    data_file = os.path.join(DIR, "trending_data.json")
    if not os.path.exists(data_file):
        print("📊 Data file not found. Running extractor...")
        # Safe: extract_data.py guards module-level code with `if __name__ == "__main__"`
        from extract_data import extract_all
        data = extract_all()
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Extracted {data['total_repos']} repos")
    else:
        print("✅ Data file found.")

    # Start server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print(f"\n{'='*50}")
        print(f"  🚀 GitHub Trending Library")
        print(f"  {'='*50}")
        print(f"  Open:  {url}")
        print(f"  Quit:  Ctrl+C")
        print(f"{'='*50}\n")

        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")


if __name__ == "__main__":
    main()
