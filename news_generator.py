#!/usr/bin/env python3
"""
Агрегатор реальных новостей (без feedparser)
Сохраняет новости в news.json, НЕ трогает index.html
"""

import json
import hashlib
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

NEWS_FILE = "news.json"
MAX_ARTICLES = 500

# RSS-источники
RSS_FEEDS = {
    "Habr IT": "https://habr.com/ru/rss/hub/it_news/",
    "Habr All": "https://habr.com/ru/rss/hub/all/",
    "РИА Новости": "https://ria.ru/export/rss2/index.xml",
    "РИА Наука": "https://ria.ru/export/rss2/science/index.xml",
    "РИА Технологии": "https://ria.ru/export/rss2/technology/index.xml",
    "Lenta.ru": "https://lenta.ru/rss",
}

def parse_rss(url, source_name):
    """Парсит RSS-ленту"""
    articles = []
    try:
        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(resp.content, 'xml')
        
        for item in soup.find_all('item')[:10]:
            title = item.find('title')
            if not title or not title.get_text(strip=True):
                continue
            
            desc = item.find('description')
            link = item.find('link')
            pub_date = item.find('pubDate')
            
            articles.append({
                "id": hashlib.md5(title.get_text(strip=True).encode()).hexdigest()[:16],
                "title": title.get_text(strip=True),
                "summary": BeautifulSoup(desc.get_text(strip=True) if desc else "", 'html.parser').get_text()[:300],
                "content": BeautifulSoup(desc.get_text(strip=True) if desc else "", 'html.parser').get_text()[:500],
                "link": link.get_text(strip=True) if link else "",
                "source": source_name,
                "published_at": pub_date.get_text(strip=True) if pub_date else datetime.now().isoformat(),
                "tags": ["AI", "технологии"],
            })
    except Exception as e:
        print(f"  Ошибка {source_name}: {e}")
    
    return articles

def fetch_all_news():
    """Собирает новости со всех источников"""
    all_articles = []
    print("📡 Сбор новостей из RSS...")
    
    for name, url in RSS_FEEDS.items():
        print(f"  {name}...")
        all_articles.extend(parse_rss(url, name))
        time.sleep(0.5)
    
    # Удаляем дубликаты
    unique = {}
    for article in all_articles:
        if article['title'] not in unique:
            unique[article['title']] = article
    
    result = list(unique.values())
    print(f"✅ Собрано {len(result)} новостей")
    return result

def save_news(articles):
    """Сохраняет новости в JSON (НЕ ТРОГАЕТ index.html)"""
    data = {
        "articles": articles[:MAX_ARTICLES],
        "last_updated": datetime.now().isoformat(),
        "total_articles": len(articles),
        "sources_count": len(RSS_FEEDS)
    }
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранено в {NEWS_FILE}")
    print(f"📊 Всего новостей: {len(articles)}")
    print(f"🕐 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    print("=" * 50)
    print("🚀 АГРЕГАТОР РЕАЛЬНЫХ НОВОСТЕЙ")
    print("=" * 50)
    
    articles = fetch_all_news()
    
    if articles:
        save_news(articles)
        print("\n📰 Последние 3 новости:")
        for i, art in enumerate(articles[:3], 1):
            print(f"   {i}. {art['title'][:70]}...")
            print(f"      📍 {art['source']}")
    else:
        print("❌ Не удалось загрузить новости")
        # Создаём пустой файл, чтобы не было ошибки 404
        save_news([])

if __name__ == "__main__":
    main()
