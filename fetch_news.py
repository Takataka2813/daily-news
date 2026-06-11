"""
fetch_news.py
RSSフィードから記事を取得して news.json に書き出す
"""

import json
import feedparser
from datetime import datetime, timezone

# ── RSSフィード設定 ──────────────────────────────────────────
FEEDS = [
    # Technology
    {"url": "https://feeds.feedburner.com/TechCrunch", "category": "Technology", "source": "TechCrunch"},
    {"url": "https://www.wired.com/feed/rss",           "category": "Technology", "source": "Wired"},
    # Business / Economy
    {"url": "https://feeds.reuters.com/reuters/businessNews", "category": "Business", "source": "Reuters"},
    {"url": "http://feeds.bbci.co.uk/news/business/rss.xml",  "category": "Business", "source": "BBC Business"},
    # Sports
    {"url": "https://www.espn.com/espn/rss/news",          "category": "Sports", "source": "ESPN"},
    {"url": "http://feeds.bbci.co.uk/sport/rss.xml",       "category": "Sports", "source": "BBC Sport"},
    # Science / Health
    {"url": "https://feeds.sciencedaily.com/sciencedaily/top_news", "category": "Science", "source": "ScienceDaily"},
    {"url": "http://feeds.bbci.co.uk/news/health/rss.xml",          "category": "Science", "source": "BBC Health"},
]

ARTICLES_PER_FEED = 5   # 1フィードあたりの最大記事数
# ──────────────────────────────────────────────────────────────


def parse_date(entry):
    """公開日時をISO 8601文字列で返す"""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return None


def fetch_feed(feed_cfg):
    articles = []
    try:
        parsed = feedparser.parse(feed_cfg["url"])
        for entry in parsed.entries[:ARTICLES_PER_FEED]:
            title = entry.get("title", "").strip()
            if not title:
                continue

            # description / summary を取得（HTMLタグを除去）
            desc = entry.get("summary", "") or entry.get("description", "")
            # 簡易タグ除去
            import re
            desc = re.sub(r"<[^>]+>", "", desc).strip()
            desc = desc[:280] if desc else ""

            url = entry.get("link", "")
            articles.append({
                "title":       title,
                "description": desc,
                "url":         url,
                "source":      feed_cfg["source"],
                "category":    feed_cfg["category"],
                "publishedAt": parse_date(entry),
            })
    except Exception as e:
        print(f"[WARN] Failed to fetch {feed_cfg['url']}: {e}")
    return articles


def main():
    all_articles = []
    for feed in FEEDS:
        print(f"Fetching {feed['source']} ({feed['category']})…")
        all_articles.extend(fetch_feed(feed))

    print(f"Total articles: {len(all_articles)}")

    output = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "articles":  all_articles,
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("news.json written.")


if __name__ == "__main__":
    main()
