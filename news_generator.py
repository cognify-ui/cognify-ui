#!/usr/bin/env python3
"""
Реальный агрегатор новостей из RSS-лент
Без генерации фейков, только настоящие новости
"""

import json
import os
import hashlib
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

import feedparser
import requests
from bs4 import BeautifulSoup

# ==================== КОНФИГУРАЦИЯ ====================

NEWS_FILE = "news.json"
MAX_ARTICLES = 500  # Храним максимум 500 свежих новостей

# Реальные RSS-ленты (русскоязычные и международные)
RSS_FEEDS = {
    # Русскоязычные источники
    "РИА Новости (главное)": "https://ria.ru/export/rss2/index.xml",
    "РИА Новости (наука)": "https://ria.ru/export/rss2/science/index.xml",
    "РИА Новости (технологии)": "https://ria.ru/export/rss2/technology/index.xml",
    "ТАСС (наука)": "https://tass.ru/rss/v2.xml?rubric=science",
    "ТАСС (технологии)": "https://tass.ru/rss/v2.xml?rubric=technology",
    "Ведомости (технологии)": "https://www.vedomosti.ru/rss/rubric/technology",
    "Habr (все потоки)": "https://habr.com/ru/rss/hub/all/?fl=ru",
    "Habr (IT-новости)": "https://habr.com/ru/rss/hub/it_news/",
    "Lenta.ru": "https://lenta.ru/rss",
    "РБК": "https://www.rbc.ru/rss/",
    "Коммерсантъ": "https://www.kommersant.ru/RSS/news.xml",
    "N+1 (научпоп)": "https://nplus1.ru/rss",
    "Чердак (наука)": "https://chrdk.ru/rss/news",
    
    # Международные (на английском)
    "TechCrunch": "https://feeds.feedburner.com/TechCrunch",
    "Wired": "https://www.wired.com/feed/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Science Daily": "https://www.sciencedaily.com/rss/all.xml",
    "Nature": "https://www.nature.com/nature.rss",
    "BBC News (Technology)": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "Reuters (Technology)": "https://www.reutersagency.com/feed/?best-topics=tech",
    "Hacker News": "https://hnrss.org/frontpage",
}

# Теги для автоматической категоризации (по ключевым словам)
KEYWORD_TAGS = {
    "ai": ["ии", "нейросеть", "нейросети", "ai", "искусственный интеллект", "chatgpt", "gemini", "gpt", "llm", "ml", "машинное обучение"],
    "space": ["космос", "space", "марс", "луна", "spacex", "nasa", "roscosmos", "мкс", "спутник", "ракета"],
    "science": ["наука", "ученые", "исследование", "открытие", "лаборатория", "эксперимент", "биология", "физика", "химия"],
    "tech": ["технологии", "гаджеты", "apple", "google", "microsoft", "android", "iphone", "приложение", "софт", "windows"],
    "cybersecurity": ["хакеры", "утечка", "безопасность", "вирус", "взлом", "security", "данные", "пароль"],
    "business": ["бизнес", "стартап", "инвестиции", "рынок", "акции", "миллиард", "компания"],
    "medicine": ["медицина", "здоровье", "болезнь", "лекарство", "вакцина", "больница", "врачи"],
    "ecology": ["экология", "климат", "природа", "загрязнение", "глобальное потепление", "энергия"],
}


def get_tags_for_article(title: str, summary: str) -> List[str]:
    """Автоматически определяет теги статьи по ключевым словам"""
    text = (title + " " + summary).lower()
    tags = set()
    
    for tag, keywords in KEYWORD_TAGS.items():
        for keyword in keywords:
            if keyword in text:
                tags.add(tag)
                break
    
    # Если тегов не нашлось, добавляем базовый
    if not tags:
        tags.add("news")
    
    # Ограничиваем количество тегов
    return list(tags)[:5]


def fetch_articles_from_feed(feed_url: str, source_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Загружает статьи из одного RSS-потока"""
    articles = []
    
    try:
        print(f"   📡 Загружаем {source_name}...")
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:  # Ошибка парсинга
            print(f"   ⚠️ Ошибка при загрузке {source_name}: {feed.bozo_exception}")
            return []
        
        for i, entry in enumerate(feed.entries[:limit]):
            # Извлекаем дату публикации
            published_at = datetime.now().isoformat()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6]).isoformat()
            
            # Извлекаем контент
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Очищаем HTML от контента
            content_clean = BeautifulSoup(content, 'html.parser').get_text()[:500]
            
            # Извлекаем автора
            author = ""
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'creator'):
                author = entry.creator
            
            # Формируем статью
            article = {
                "title": entry.get('title', '').strip(),
                "summary": BeautifulSoup(entry.get('summary', '')[:300], 'html.parser').get_text().strip(),
                "content": content_clean,
                "link": entry.get('link', ''),
                "source": source_name,
                "author": author,
                "published_at": published_at,
                "tags": get_tags_for_article(entry.get('title', ''), entry.get('summary', '')),
                "real_sources": [source_name],
                "image_url": extract_image_url(entry, content),
            }
            
            # Пропускаем пустые заголовки
            if article['title']:
                articles.append(article)
                
    except Exception as e:
        print(f"   ❌ Ошибка при загрузке {source_name}: {str(e)}")
    
    return articles


def extract_image_url(entry: feedparser.FeedParserDict, content: str) -> str:
    """Пытается извлечь URL изображения из RSS-записи"""
    
    # Проверяем стандартные поля RSS
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image/'):
                return enclosure.get('href', '')
    
    # Пробуем найти изображение в HTML-контенте
    if content:
        soup = BeautifulSoup(content, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img['src']
    
    # Возвращаем плейсхолдер с тематикой
    return None


def fetch_all_news() -> List[Dict[str, Any]]:
    """Собирает новости из всех RSS-источников"""
    all_articles = []
    
    print("\n🔄 Начинаем сбор новостей из RSS-лент...")
    print("-" * 50)
    
    for source_name, feed_url in RSS_FEEDS.items():
        articles = fetch_articles_from_feed(feed_url, source_name, limit=8)
        all_articles.extend(articles)
        time.sleep(0.5)  # Небольшая задержка, чтобы не забанили
    
    # Удаляем дубликаты по заголовку
    unique_articles = []
    seen_titles = set()
    
    for article in all_articles:
        title_hash = hashlib.md5(article['title'].encode()).hexdigest()
        if title_hash not in seen_titles:
            seen_titles.add(title_hash)
            unique_articles.append(article)
    
    # Сортируем по дате (свежие сверху)
    unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    
    print("-" * 50)
    print(f"📊 Собрано {len(unique_articles)} уникальных новостей из {len(RSS_FEEDS)} источников")
    
    return unique_articles


def load_existing_news() -> Dict[str, Any]:
    """Загружает существующие новости из файла"""
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return {
        "articles": [],
        "last_updated": datetime.now().isoformat(),
        "total_articles": 0
    }


def save_news_articles(articles: List[Dict[str, Any]]) -> bool:
    """Сохраняет новости в JSON-файл"""
    
    # Добавляем SEO-метаданные
    for article in articles:
        article['seo_metadata'] = {
            "meta_title": f"{article['title']} | Cognify AI News",
            "meta_description": article.get('summary', '')[:160],
            "meta_keywords": ", ".join(article.get('tags', [])),
        }
        # Добавляем временную метку обновления
        article['cached_at'] = datetime.now().isoformat()
    
    data = {
        "articles": articles[:MAX_ARTICLES],
        "last_updated": datetime.now().isoformat(),
        "total_articles": len(articles),
        "sources_count": len(RSS_FEEDS)
    }
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True


def update_news_html(articles: List[Dict[str, Any]]):
    """Обновляет HTML-страницу с новостями"""
    
    # Сортируем для отображения
    recent_articles = articles[:50]  # Последние 50 новостей
    
    html_content = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Актуальные новости | Cognify AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            font-size: 0.9rem;
        }
        
        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 25px;
        }
        
        .news-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .news-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        
        .card-content {
            padding: 20px;
        }
        
        .source {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            margin-bottom: 12px;
        }
        
        .title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        
        .title a {
            color: #333;
            text-decoration: none;
        }
        
        .title a:hover {
            color: #667eea;
        }
        
        .summary {
            color: #666;
            line-height: 1.5;
            margin-bottom: 15px;
            font-size: 0.95rem;
        }
        
        .meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: #999;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        
        .tag {
            background: #f0f0f0;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.7rem;
            color: #666;
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            color: white;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .news-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 Актуальные новости</h1>
            <div class="subtitle">Реальные новости из проверенных источников</div>
            <div class="stats">
                <span>📊 Всего новостей: """ + str(len(articles)) + """</span>
                <span>📡 Источников: """ + str(len(RSS_FEEDS)) + """</span>
                <span>🕐 Обновлено: """ + datetime.now().strftime('%d.%m.%Y %H:%M') + """</span>
            </div>
        </div>
        
        <div class="news-grid">
"""
    
    for article in recent_articles:
        source = article.get('source', 'Unknown')
        title = article.get('title', '')
        summary = article.get('summary', '')[:200]
        link = article.get('link', '#')
        tags = article.get('tags', [])
        published_at = article.get('published_at', '')
        
        # Форматируем дату
        try:
            pub_date = datetime.fromisoformat(published_at).strftime('%d.%m.%Y %H:%M')
        except:
            pub_date = 'Недавно'
        
        html_content += f"""
            <div class="news-card">
                <div class="card-content">
                    <span class="source">📌 {source}</span>
                    <div class="title">
                        <a href="{link}" target="_blank">{title}</a>
                    </div>
                    <div class="summary">{summary}...</div>
                    <div class="tags">
"""
        for tag in tags[:3]:
            html_content += f'<span class="tag">#{tag}</span>'
        
        html_content += f"""
                    </div>
                    <div class="meta">
                        <span>🕐 {pub_date}</span>
                    </div>
                </div>
            </div>
"""
    
    html_content += """
        </div>
        <div class="footer">
            <p>© 2026 Cognify AI — Агрегатор реальных новостей из RSS-лент</p>
            <p>Данные собираются автоматически из открытых источников</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Обновлена HTML-страница")


def main():
    print("=" * 60)
    print("🚀 ЗАПУСК РЕАЛЬНОГО АГРЕГАТОРА НОВОСТЕЙ")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Собираем свежие новости из RSS
    articles = fetch_all_news()
    
    if articles:
        # Сохраняем в JSON
        save_news_articles(articles)
        
        # Обновляем HTML-страницу
        update_news_html(articles)
        
        print("\n" + "=" * 60)
        print(f"✅ ГОТОВО! Сохранено {len(articles)} реальных новостей")
        print(f"📁 JSON файл: {NEWS_FILE}")
        print(f"🌐 HTML страница: index.html")
        print("=" * 60)
        
        # Показываем 5 последних новостей
        print("\n📰 Последние новости:")
        for i, article in enumerate(articles[:5], 1):
            print(f"   {i}. {article['title'][:80]}...")
            print(f"      📍 {article['source']}")
    else:
        print("\n❌ Не удалось загрузить новости. Проверьте подключение к интернету.")
        
        # Проверяем, есть ли закешированные новости
        existing = load_existing_news()
        if existing.get('articles'):
            print(f"📦 Загружаем {len(existing['articles'])} закешированных новостей")
            update_news_html(existing['articles'])


if __name__ == "__main__":
    main()
