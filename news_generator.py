#!/usr/bin/env python3
"""
Агрегатор реальных новостей - всегда сохраняет ссылки на оригиналы
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
    "Habr All": "https://habr.com/ru/rss/hub/all/",
    "Habr IT": "https://habr.com/ru/rss/hub/it_news/",
    "TechCrunch": "https://feeds.feedburner.com/TechCrunch",
    "Wired": "https://www.wired.com/feed/rss",
}

def clean_cdata(text):
    """Убирает обёртку CDATA из текста"""
    if not text:
        return ""
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text)
    return text.strip()

def clean_html(text):
    """Очищает HTML от тегов"""
    if not text:
        return ""
    return BeautifulSoup(text, 'html.parser').get_text().strip()

def extract_images_from_html(html_text):
    """Извлекает все изображения из HTML"""
    if not html_text:
        return []
    
    soup = BeautifulSoup(html_text, 'html.parser')
    images = []
    
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src and not src.startswith('data:'):
            if not src.startswith('http'):
                src = 'https:' + src if src.startswith('//') else src
            images.append(src)
    
    return images

def extract_link_from_item(item):
    """Извлекает ссылку из RSS-элемента любым способом"""
    # Пробуем link
    link_elem = item.find('link')
    if link_elem:
        link_text = link_elem.get_text(strip=True)
        if link_text and link_text.startswith('http'):
            return link_text
        if link_elem.get('href') and link_elem.get('href').startswith('http'):
            return link_elem.get('href')
    
    # Пробуем guid (часто содержит ссылку)
    guid = item.find('guid')
    if guid:
        guid_text = guid.get_text(strip=True)
        if guid_text and guid_text.startswith('http'):
            return guid_text
    
    # Пробуем найти ссылку в comments
    comments = item.find('comments')
    if comments:
        comments_text = comments.get_text(strip=True)
        if comments_text and comments_text.startswith('http'):
            return comments_text
    
    return None

def fetch_rss_feed(url, source_name):
    """Получает и парсит RSS-ленту"""
    articles = []
    try:
        response = requests.get(url, timeout=20, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')
        
        for item in items[:15]:
            # Заголовок
            title_elem = item.find('title')
            if not title_elem:
                continue
            title = clean_cdata(title_elem.get_text(strip=True))
            if not title:
                continue
            
            # Ссылка - ОБЯЗАТЕЛЬНО извлекаем
            link = extract_link_from_item(item)
            if not link:
                # Если ссылки нет, пропускаем эту новость
                print(f"     ⚠️ Нет ссылки: {title[:50]}...")
                continue
            
            # Получаем полный контент
            full_content = ""
            images = []
            
            # Пробуем content:encoded (полный HTML)
            content_elem = item.find('content:encoded')
            if content_elem:
                raw_content = clean_cdata(content_elem.get_text(strip=True))
                images = extract_images_from_html(raw_content)
                full_content = clean_html(raw_content)
            
            # Если нет content:encoded, берем description
            if not full_content:
                desc_elem = item.find('description')
                if desc_elem:
                    raw_desc = clean_cdata(desc_elem.get_text(strip=True))
                    images = extract_images_from_html(raw_desc)
                    full_content = clean_html(raw_desc)
            
            # Ограничиваем длину до 5000 символов
            if len(full_content) > 5000:
                full_content = full_content[:5000] + "\n\n...(продолжение в оригинале)"
            
            # Краткое описание (первые 300 символов)
            summary = full_content[:300] if full_content else ""
            
            # Первое изображение как превью
            preview_image = images[0] if images else None
            
            # Дата
            date_elem = item.find('pubDate')
            pub_date = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
            
            articles.append({
                "id": hashlib.md5(title.encode()).hexdigest()[:16],
                "title": title,
                "summary": summary,
                "content": full_content,
                "link": link,  # ОБЯЗАТЕЛЬНО сохраняем ссылку
                "source": source_name,
                "published_at": pub_date,
                "tags": ["AI", "технологии", "IT"],
                "images": images,
                "preview_image": preview_image,
            })
            
    except Exception as e:
        print(f"  ❌ {source_name}: {str(e)[:50]}")
    
    return articles

def fetch_all_news():
    """Собирает новости со всех источников"""
    all_articles = []
    print("📡 Сбор новостей с гарантированными ссылками...")
    print("=" * 50)
    
    for name, url in RSS_FEEDS.items():
        print(f"  📰 {name}...")
        articles = fetch_rss_feed(url, name)
        print(f"     ✅ {len(articles)} новостей (все со ссылками)")
        for art in articles:
            if art['images']:
                print(f"        🖼️ {len(art['images'])} изображений")
        all_articles.extend(articles)
        time.sleep(1)
    
    # Удаляем дубликаты
    unique = {}
    for article in all_articles:
        if article['title'] not in unique:
            unique[article['title']] = article
    
    result = list(unique.values())
    print("=" * 50)
    print(f"📊 Итого: {len(result)} уникальных новостей")
    
    # Проверяем наличие ссылок
    with_links = sum(1 for a in result if a.get('link'))
    print(f"🔗 Новостей со ссылками: {with_links}")
    
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
    print("🚀 АГРЕГАТОР НОВОСТЕЙ (с гарантированными ссылками)")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    articles = fetch_all_news()
    
    if articles:
        save_news(articles)
        print("\n📰 Последние новости:")
        for i, art in enumerate(articles[:5], 1):
            print(f"   {i}. {art['title'][:60]}...")
            print(f"      📍 {art['source']}")
            print(f"      🔗 {art.get('link', 'НЕТ ССЫЛКИ!')[:60]}...")
            if art['images']:
                print(f"      🖼️ Картинок: {len(art['images'])}")
            print()
    else:
        print("\n⚠️ Не удалось загрузить новости")
        demo_news = [{
            "id": "1",
            "title": "Добро пожаловать в Cognify AI News!",
            "summary": "Новости загружаются из RSS-лент с полными текстами до 5000 символов, изображениями и ссылками.",
            "content": "Теперь каждая новость содержит полный текст, картинки и ссылку на оригинал. Наслаждайтесь чтением!",
            "link": "https://cognify-ui.github.io",
            "source": "Cognify AI",
            "published_at": datetime.now().isoformat(),
            "tags": ["info"],
            "images": [],
            "preview_image": None,
        }]
        save_news(demo_news)

if __name__ == "__main__":
    main()
