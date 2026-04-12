#!/usr/bin/env python3
import json
import requests
from datetime import datetime
import hashlib
import feedparser
import re
import os
import time
import sys

NEWS_FILE = "news.json"
MAX_ARTICLES = 50

# Расширенный список RSS-источников (с запасными)
RSS_SOURCES = [
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://towardsdatascience.com/feed/tagged/ai",
    "https://news.mit.edu/topic/artificial-intelligence2-rss.xml",
    "https://www.zdnet.com/topic/artificial-intelligence/rss.xml"
]

def clean_html(text):
    """Удаляет HTML теги"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_rss(url):
    """Получает новости из RSS с повторными попытками"""
    max_retries = 2
    user_agents = [
        "Mozilla/5.0 (compatible; CognifyBot/1.0; +https://cognify-ui.github.io)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ]
    
    for attempt in range(max_retries):
        try:
            # Меняем User-Agent при каждой попытке
            feedparser.USER_AGENT = user_agents[attempt % len(user_agents)]
            
            # Увеличиваем таймаут
            feed = feedparser.parse(url, timeout=30)
            
            # Проверяем на ошибки
            if feed.bozo and attempt == max_retries - 1:
                print(f"   ⚠️ Предупреждение: {str(feed.bozo_exception)[:100]}")
            
            if not feed.entries:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                print(f"   ⚠️ Нет записей в {url}")
                return []
            
            articles = []
            for entry in feed.entries[:5]:
                link = entry.get('link', '')
                if not link:
                    continue
                    
                article_id = hashlib.md5(link.encode()).hexdigest()[:12]
                title = clean_html(entry.get('title', ''))[:100]
                
                if not title:
                    title = "AI Новость"
                
                # Пробуем получить summary из разных полей
                summary = clean_html(entry.get('summary', ''))
                if not summary:
                    summary = clean_html(entry.get('description', ''))
                if not summary:
                    summary = f"{title}. Подробнее в источнике."
                
                # Пробуем получить content
                content = ""
                if entry.get('content'):
                    content = clean_html(entry['content'][0].get('value', ''))
                if not content and summary:
                    content = summary[:1000]
                if not content:
                    content = summary
                
                # Форматируем дату
                pub_date = entry.get('published', entry.get('updated', ''))
                if not pub_date:
                    pub_date = datetime.now().isoformat()
                
                articles.append({
                    "id": article_id,
                    "title": title,
                    "summary": summary[:300],
                    "content": content[:1500],
                    "link": link,
                    "published": pub_date,
                    "source": feed.feed.get('title', url.split('/')[2])
                })
            
            return articles
            
        except Exception as e:
            print(f"   ❌ Ошибка (попытка {attempt+1}): {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return []

def generate_tags(title):
    """Генерирует теги из заголовка"""
    title_lower = title.lower()
    tags = []
    
    keywords = {
        'groq': 'groq', 'cerebras': 'cerebras', 'gemini': 'gemini',
        'google': 'google', 'openai': 'openai', 'chatgpt': 'chatgpt',
        'gpt': 'gpt', 'claude': 'claude', 'meta': 'meta', 
        'llama': 'llama', 'mistral': 'mistral', 'ai': 'ai',
        'ml': 'ml', 'robot': 'роботы', 'нейросеть': 'нейросети'
    }
    
    for key, tag in keywords.items():
        if key in title_lower:
            tags.append(tag)
    
    return tags[:4] if tags else ['ai', 'news']

def update_news_json(new_articles):
    """Обновляет файл новостей"""
    existing = {"last_updated": "", "articles": []}
    
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            print("   ⚠️ Файл повреждён, создаю новый")
    
    existing_ids = {a.get('id') for a in existing.get('articles', [])}
    
    new_count = 0
    for article in new_articles:
        if article['id'] in existing_ids:
            continue
        
        formatted = {
            "id": article['id'],
            "title": article['title'],
            "summary": article['summary'],
            "content": article['content'],
            "source": article.get('source', 'AI News'),
            "source_url": article.get('link', ''),
            "published_at": article.get('published', datetime.now().isoformat()),
            "tags": generate_tags(article['title'])
        }
        
        existing['articles'].insert(0, formatted)
        new_count += 1
    
    existing['articles'] = existing['articles'][:MAX_ARTICLES]
    existing['last_updated'] = datetime.now().isoformat()
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    return new_count

def create_demo_news():
    """Создаёт демо-новости для первого запуска"""
    demo_articles = [
        {
            "id": "demo1",
            "title": "Cognify AI запущен!",
            "summary": "Новый бесплатный сервис с 4 AI моделями: Groq, Cerebras, Cloudflare и Gemini",
            "content": "Cognify AI предоставляет бесплатный доступ к 4 мощным AI моделям. Без лимитов, с историей чатов и системой аккаунтов. Просто откройте сайт и начните общение!",
            "source": "Cognify AI",
            "source_url": "https://cognify-ui.github.io",
            "published_at": datetime.now().isoformat(),
            "tags": ["cognify", "ai", "бесплатно", "groq", "gemini"]
        }
    ]
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "articles": demo_articles
        }, f, ensure_ascii=False, indent=2)
    
    print("📝 Создан демо-файл с новостями")

def main():
    print(f"🚀 Запуск: {datetime.now()}")
    print(f"📡 Источников: {len(RSS_SOURCES)}")
    print(f"🐍 Python: {sys.version}")
    print("-" * 50)
    
    all_articles = []
    
    for url in RSS_SOURCES:
        source_name = url.split('/')[2]
        print(f"📥 Парсинг: {source_name}...")
        articles = fetch_rss(url)
        print(f"   ✅ Получено: {len(articles)} статей")
        all_articles.extend(articles)
        time.sleep(2)  # Пауза между запросами
    
    # Удаляем дубликаты
    unique = []
    seen_links = set()
    for a in all_articles:
        if a['link'] not in seen_links:
            seen_links.add(a['link'])
            unique.append(a)
    
    print(f"📊 Уникальных статей: {len(unique)}")
    
    if unique:
        new_count = update_news_json(unique)
        print(f"✨ Добавлено новых: {new_count}")
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📄 Всего в файле: {len(data['articles'])} статей")
        except:
            pass
    else:
        print("⚠️ Не найдено новых статей")
        if not os.path.exists(NEWS_FILE):
            create_demo_news()
    
    print("✅ Готово!")

if __name__ == "__main__":
    main()
