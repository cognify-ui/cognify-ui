#!/usr/bin/env python3
"""
Агрегатор реальных новостей - работает без lxml
"""

import json
import hashlib
import time
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

NEWS_FILE = "news.json"
MAX_ARTICLES = 500

# RSS-источники
RSS_FEEDS = {
    "Habr IT": "https://habr.com/ru/rss/hub/it_news/",
    "Habr All": "https://habr.com/ru/rss/hub/all/",
    "TechCrunch": "https://feeds.feedburner.com/TechCrunch",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
}

def fetch_rss_feed(url, source_name):
    """Получает и парсит RSS-ленту без lxml"""
    articles = []
    try:
        response = requests.get(url, timeout=20, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Парсим как HTML (не требует lxml)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Находим все item
        items = soup.find_all('item')
        
        for item in items[:10]:
            # Заголовок
            title_elem = item.find('title')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            if not title:
                continue
            
            # Описание
            desc_elem = item.find('description')
            summary = ""
            if desc_elem:
                summary = BeautifulSoup(desc_elem.get_text(strip=True), 'html.parser').get_text()[:300]
            
            # Ссылка
            link_elem = item.find('link')
            link = link_elem.get_text(strip=True) if link_elem else ""
            
            # Дата
            date_elem = item.find('pubDate')
            pub_date = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
            
            articles.append({
                "id": hashlib.md5(title.encode()).hexdigest()[:16],
                "title": title,
                "summary": summary,
                "content": summary,
                "link": link,
                "source": source_name,
                "published_at": pub_date,
                "tags": ["AI", "технологии"],
            })
            
    except Exception as e:
        print(f"  ❌ {source_name}: {str(e)[:50]}")
    
    return articles

def fetch_all_news():
    """Собирает новости из всех источников"""
    all_articles = []
    print("📡 Сбор новостей...")
    
    for name, url in RSS_FEEDS.items():
        print(f"  📰 {name}...")
        articles = fetch_rss_feed(url, name)
        print(f"     ✅ {len(articles)} новостей")
        all_articles.extend(articles)
        time.sleep(0.5)
    
    # Удаляем дубликаты
    unique = {}
    for article in all_articles:
        if article['title'] not in unique:
            unique[article['title']] = article
    
    result = list(unique.values())
    print(f"\n📊 Итого: {len(result)} уникальных новостей")
    return result

def save_news(articles):
    """Сохраняет новости в JSON"""
    data = {
        "articles": articles[:MAX_ARTICLES],
        "last_updated": datetime.now().isoformat(),
        "total_articles": len(articles),
        "sources": list(RSS_FEEDS.keys())
    }
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранено в {NEWS_FILE}")

def main():
    print("=" * 55)
    print("🚀 АГРЕГАТОР НОВОСТЕЙ (AI & Tech)")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    articles = fetch_all_news()
    
    if articles:
        save_news(articles)
        print("\n📰 Последние новости:")
        for i, art in enumerate(articles[:5], 1):
            print(f"   {i}. {art['title'][:75]}...")
            print(f"      📍 {art['source']}")
    else:
        print("\n⚠️ Не удалось загрузить новости")
        # Создаём демо-новости
        demo_news = [{
            "id": "1",
            "title": "Добро пожаловать в Cognify AI News!",
            "summary": "Новости загружаются из RSS-лент Habr, TechCrunch, The Verge и Wired.",
            "content": "Скоро здесь появятся свежие новости об искусственном интеллекте и технологиях.",
            "link": "#",
            "source": "Cognify AI",
            "published_at": datetime.now().isoformat(),
            "tags": ["info"],
        }]
        save_news(demo_news)
        print("📝 Созданы демо-новости")

if __name__ == "__main__":
    main()
