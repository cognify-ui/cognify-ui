#!/usr/bin/env python3
import json
import hashlib
import feedparser
import re
import os
import time
from datetime import datetime

NEWS_FILE = "news.json"
MAX_ARTICLES = 100  # Увеличено с 50 до 100

# РАСШИРЕННЫЙ список RSS источников (15 источников вместо 5)
RSS_SOURCES = [
    # Крупные технологические издания
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    "https://www.techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.wired.com/category/artificial-intelligence/feed/rss",
    
    # Научные и исследовательские
    "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
    "https://news.mit.edu/topic/artificial-intelligence2-rss.xml",
    "https://www.newscientist.com/subject/ai/feed/",
    "https://www.nature.com/subjects/artificial-intelligence.rss",
    
    # AI сообщества и разработчики
    "https://towardsdatascience.com/feed/tagged/ai",
    "https://medium.com/feed/tag/artificial-intelligence",
    "https://huggingface.co/blog/feed.xml",
    "https://deepmind.com/blog/feed/basic",
    
    # Дополнительные новости
    "https://www.ibm.com/blogs/artificial-intelligence/feed/",
    "https://www.microsoft.com/en-us/research/blog/feed/"
]

def clean_html(text):
    """Удаляет HTML теги"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def generate_tags(title):
    """Генерирует теги из заголовка (расширенный список)"""
    title_lower = title.lower()
    tags = []
    
    keywords = {
        # Компании
        'openai': 'openai', 'chatgpt': 'chatgpt', 'gpt': 'gpt',
        'google': 'google', 'gemini': 'gemini', 'deepmind': 'deepmind',
        'anthropic': 'anthropic', 'claude': 'claude',
        'meta': 'meta', 'llama': 'llama',
        'microsoft': 'microsoft', 'copilot': 'copilot',
        'apple': 'apple', 'siri': 'siri',
        'amazon': 'amazon', 'alexa': 'alexa',
        'tesla': 'tesla', 'xai': 'xai',
        
        # Технологии
        'groq': 'groq', 'cerebras': 'cerebras',
        'mistral': 'mistral', 'cohere': 'cohere',
        'stability': 'stability', 'midjourney': 'midjourney',
        
        # Общие темы
        'robot': 'роботы', 'нейросеть': 'нейросети',
        'ml': 'ml', 'ai': 'ai', 'agi': 'agi',
        'чип': 'чипы', 'gpu': 'gpu', 'nvidia': 'nvidia'
    }
    
    for key, tag in keywords.items():
        if key in title_lower:
            tags.append(tag)
    
    # Убираем дубликаты и ограничиваем
    unique_tags = list(dict.fromkeys(tags))
    return unique_tags[:5] if unique_tags else ['ai', 'news']

def fetch_rss(url):
    """Получает новости из RSS"""
    try:
        feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        feed = feedparser.parse(url)
        
        if feed.bozo:
            print(f"   ⚠️ Предупреждение: {str(feed.bozo_exception)[:80]}")
        
        if not feed.entries:
            return []
        
        articles = []
        # Берём до 7 статей из каждого источника (было 5)
        for entry in feed.entries[:7]:
            link = entry.get('link', '')
            if not link:
                continue
                
            article_id = hashlib.md5(link.encode()).hexdigest()[:12]
            title = clean_html(entry.get('title', ''))[:120]
            
            if not title:
                title = "AI Новость"
            
            # Получаем описание
            summary = clean_html(entry.get('summary', ''))
            if not summary:
                summary = clean_html(entry.get('description', ''))
            if not summary:
                summary = f"{title}."
            
            # Получаем полный текст
            content = ""
            if entry.get('content'):
                content = clean_html(entry['content'][0].get('value', ''))
            if not content and summary:
                content = summary
            if not content:
                content = title
            
            # Дата публикации
            pub_date = entry.get('published', entry.get('updated', ''))
            if not pub_date:
                pub_date = datetime.now().isoformat()
            
            articles.append({
                "id": article_id,
                "title": title,
                "summary": summary[:350],
                "content": content[:2000],
                "link": link,
                "published": pub_date,
                "source": feed.feed.get('title', url.split('/')[2])
            })
        
        return articles
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:100]}")
        return []

def update_news_json(new_articles):
    """Обновляет файл новостей"""
    existing = {"last_updated": "", "articles": []}
    
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            pass
    
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
    
    # Ограничиваем до 100 статей
    existing['articles'] = existing['articles'][:MAX_ARTICLES]
    existing['last_updated'] = datetime.now().isoformat()
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    return new_count

def create_demo_news():
    """Создаёт демо-новости при первом запуске"""
    demo_articles = [
        {
            "id": "welcome1",
            "title": "🎉 Добро пожаловать в Cognify AI!",
            "summary": "Бесплатный доступ к 4 AI моделям: Groq, Cerebras, Cloudflare и Gemini",
            "content": "Cognify AI — это бесплатный сервис с 4 мощными AI моделями. Без лимитов, с историей чатов и системой аккаунтов.",
            "source": "Cognify AI",
            "source_url": "https://cognify-ui.github.io",
            "published_at": datetime.now().isoformat(),
            "tags": ["cognify", "ai", "бесплатно"]
        }
    ]
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "articles": demo_articles
        }, f, ensure_ascii=False, indent=2)
    
    print("📝 Создан демо-файл с новостями")

def main():
    print(f"🚀 Запуск генератора новостей: {datetime.now()}")
    print(f"📡 RSS источников: {len(RSS_SOURCES)}")
    print(f"📊 Максимум статей: {MAX_ARTICLES}")
    print("-" * 60)
    
    all_articles = []
    successful_sources = 0
    
    for url in RSS_SOURCES:
        source_name = url.split('/')[2]
        print(f"📥 Парсинг: {source_name}...")
        articles = fetch_rss(url)
        if articles:
            successful_sources += 1
            print(f"   ✅ Получено: {len(articles)} статей")
            all_articles.extend(articles)
        else:
            print(f"   ⚠️ Не удалось загрузить")
        time.sleep(0.5)  # Небольшая пауза
    
    # Удаляем дубликаты
    unique = []
    seen_links = set()
    for a in all_articles:
        if a['link'] not in seen_links:
            seen_links.add(a['link'])
            unique.append(a)
    
    print("-" * 60)
    print(f"📊 Успешных источников: {successful_sources}/{len(RSS_SOURCES)}")
    print(f"📊 Уникальных статей: {len(unique)}")
    
    if unique:
        new_count = update_news_json(unique)
        print(f"✨ Добавлено новых: {new_count}")
        
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📄 Всего в файле: {len(data['articles'])} статей")
            print(f"🕐 Последнее обновление: {data['last_updated']}")
    else:
        print("⚠️ Не найдено новых статей из RSS")
        if not os.path.exists(NEWS_FILE) or os.path.getsize(NEWS_FILE) < 100:
            create_demo_news()
    
    print("✅ Готово!")

if __name__ == "__main__":
    main()
