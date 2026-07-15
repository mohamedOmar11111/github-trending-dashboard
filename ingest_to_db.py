import sqlite3
import os
import re
import sys
from datetime import datetime

DB_PATH = "C:/Users/mooma/Desktop/Growth_Architect_HQ/hq.db"
TRENDING_DIR = "C:/Users/mooma/Desktop/github-trending"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS github_trending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT,
            repo_full_name TEXT,
            stars INTEGER,
            language TEXT,
            created_at TEXT,
            is_ai_dev INTEGER,
            horizon TEXT
        )
    """)
    conn.commit()
    conn.close()

def ingest_latest():
    files = sorted([f for f in os.listdir(TRENDING_DIR) if f.endswith("-trending.md")], reverse=True)
    if not files: return
    
    latest_file = os.path.join(TRENDING_DIR, files[0])
    report_date = files[0][:10]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Regex to capture: Rank, Repo, Stars, Lang, Is_AI
    # Pattern: \d+\. \[(.*?)/(.*?)\]\(.*?\) (.*?) - (.*?) stars, (.*?), Created: (.*?)<br>
    repo_pattern = re.compile(r'\d+\. \[(.*?)\]\(.*?\) ?(\*\*\[AI/DEV\]\*\*)? - (.*?) stars, (.*?), Created: (.*?)(?:<br>| Topics)')
    
    matches = repo_pattern.findall(content)
    
    for full_name, ai_tag, stars, lang, created in matches:
        stars_int = int(stars.replace(',', ''))
        is_ai = 1 if ai_tag else 0
        
        cursor.execute("""
            INSERT INTO github_trending (report_date, repo_full_name, stars, language, created_at, is_ai_dev)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (report_date, full_name, stars_int, lang.strip(), created.strip(), is_ai))
        
    conn.commit()
    conn.close()
    print(f"Ingested {len(matches)} repos from {report_date}")

if __name__ == "__main__":
    init_db()
    ingest_latest()
