"""
fetch_news.py
信頼できるRSSフィードから記事を取得して news.json に書き出す
・ドメイン検証で偽サイトを除外
・48時間以内の記事のみ採用
"""

import json
import re
import feedparser
from datetime import datetime, timezone, timedelta

# ── 信頼済みドメイン（ホワイトリスト）──────────────────────────
TRUSTED_DOMAINS = {
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "bbc.com",
    "bbc.co.uk",
    "reuters.com",
    "espn.com",
    "scitechdaily.com",
    "theguardian.com",
    "bloomberg.com",
}

# ── RSSフィード設定 ──────────────────────────────────────────
FEEDS = [
    # Technology
    {"url": "https://www.theverge.com/rss/index.xml",           "category": "Technology", "source": "The Verge"},
    {"url": "https://www.wired.com/feed/rss",                   "category": "Technology", "source": "Wired"},
    {"url": "http://feeds.arstechnica.com/arstechnica/index/",  "category": "Technology", "source": "Ars Technica"},
    # Business / Economy
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",   "category": "Business",   "source": "BBC Business"},
    {"url": "https://www.theguardian.com/business/rss",         "category": "Business",   "source": "The Guardian"},
    # Sports
    {"url": "https://www.espn.com/espn/rss/news",               "category": "Sports",     "source": "ESPN"},
    {"url": "https://feeds.bbci.co.uk/sport/rss.xml",           "category": "Sports",     "source": "BBC Sport"},
    # Science / Health
    {"url": "https://www.scitechdaily.com/feed/",               "category": "Science",    "source": "SciTechDaily"},
    {"url": "https://feeds.bbci.co.uk/news/health/rss.xml",     "category": "Science",    "source": "BBC Health"},
]

ARTICLES_PER_FEED = 8    # 1フィードあたりの取得上限
MAX_AGE_HOURS     = 48   # 何時間以内の記事を採用するか
# ──────────────────────────────────────────────────────────────


def extract_domain(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else ""


def is_trusted(url: str) -> bool:
    domain = extract_domain(url)
    return any(domain == d or domain.endswith("." + d) for d in TRUSTED_DOMAINS)


def parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return " ".join(text.split()).strip()


def fetch_feed(feed_cfg: dict, cutoff: datetime) -> list:
    articles = []
    try:
        parsed = feedparser.parse(feed_cfg["url"])
        for entry in parsed.entries[:ARTICLES_PER_FEED]:
            title = clean_html(entry.get("title", ""))
            url   = entry.get("link", "")

            if not title or not url:
                continue

            # ── ドメイン検証 ──
            if not is_trusted(url):
                print(f"  [SKIP] Untrusted domain: {extract_domain(url)}")
                continue

            # ── 新鮮さチェック ──
            pub = parse_date(entry)
            if pub and pub < cutoff:
                continue  # 古い記事はスキップ

            desc = clean_html(
                entry.get("summary", "") or entry.get("description", "")
            )
            desc = desc[:300] if desc else ""

            articles.append({
                "title":       title,
                "description": desc,
                "url":         url,
                "source":      feed_cfg["source"],
                "category":    feed_cfg["category"],
                "publishedAt": pub.isoformat() if pub else None,
            })
    except Exception as e:
        print(f"  [WARN] Failed to fetch {feed_cfg['url']}: {e}")
    return articles


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    print(f"Cutoff: {cutoff.strftime('%Y-%m-%d %H:%M UTC')} ({MAX_AGE_HOURS}h)")

    all_articles = []
    for feed in FEEDS:
        print(f"Fetching {feed['source']} ({feed['category']})…")
        articles = fetch_feed(feed, cutoff)
        print(f"  → {len(articles)} articles")
        all_articles.extend(articles)

    # 新しい順にソート
    all_articles.sort(
        key=lambda a: a["publishedAt"] or "",
        reverse=True
    )

    print(f"\nTotal articles: {len(all_articles)}")

    output = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "articles":  all_articles,
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("news.json written.")


if __name__ == "__main__":
    main()
