#!/usr/bin/env python3
"""
Агрегатор реальных новостей - полные тексты + картинки
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

def clean_cdata(text):
    """Убирает обёртку CDATA из текста"""
    if not text:
        return ""
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text)
    return text.strip()

def clean_html(text):
    """Очищает HTML, но сохраняет изображения"""
    if not text:
        return ""
    return text

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

def html_to_markdown(html_text):
    """Конвертирует HTML в Markdown с сохранением изображений"""
    if not html_text:
        return ""
    
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Заменяем теги на Markdown
    for p in soup.find_all('p'):
        p.insert_before('\n\n')
        p.unwrap()
    
    for br in soup.find_all('br'):
        br.replace_with('\n')
    
    for h2 in soup.find_all('h2'):
        h2.insert_before('\n## ')
        h2.unwrap()
    
    for h3 in soup.find_all('h3'):
        h3.insert_before('\n### ')
        h3.unwrap()
    
    for strong in soup.find_all(['strong', 'b']):
        strong.insert_before('**')
        strong.insert_after('**')
        strong.unwrap()
    
    for em in soup.find_all(['em', 'i']):
        em.insert_before('*')
        em.insert_after('*')
        em.unwrap()
    
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text()
        if href:
            a.replace_with(f'[{text}]({href})')
    
    # Изображения в Markdown
    for img in soup.find_all('img'):
        src = img.get('src', '')
        alt = img.get('alt', '')
        if src and not src.startswith('data:'):
            if not src.startswith('http'):
                src = 'https:' + src if src.startswith('//') else src
            img.replace_with(f'\n\n![{alt}]({src})\n\n')
    
    text = str(soup)
    # Убираем лишние пробелы и переносы
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def fetch_rss_feed(url, source_name):
    """Получает и парсит RSS-ленту"""
    articles = []
    try:
        response = requests.get(url, timeout=30, headers={
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
            
            # Получаем полный контент
            full_content = ""
            images = []
            
            # Пробуем content:encoded (полный HTML)
            content_elem = item.find('content:encoded')
            if content_elem:
                raw_content = clean_cdata(content_elem.get_text(strip=True))
                images = extract_images_from_html(raw_content)
                full_content = html_to_markdown(raw_content)
            
            # Если нет content:encoded, берем description
            if not full_content:
                desc_elem = item.find('description')
                if desc_elem:
                    raw_desc = clean_cdata(desc_elem.get_text(strip=True))
                    images = extract_images_from_html(raw_desc)
                    full_content = html_to_markdown(raw_desc)
            
            # Ограничиваем длину до 5000 символов
            if len(full_content) > 5000:
                full_content = full_content[:5000] + "\n\n...(продолжение в оригинале)"
            
            # Краткое описание (первые 300 символов)
            summary = full_content[:300] if full_content else ""
            
            # Первое изображение как превью
            preview_image = images[0] if images else None
            
            # Ссылка на оригинал
            link_elem = item.find('link')
            link = link_elem.get_text(strip=True) if link_elem else ""
            
            # Дата
            date_elem = item.find('pubDate')
            pub_date = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
            
            articles.append({
                "id": hashlib.md5(title.encode()).hexdigest()[:16],
                "title": title,
                "summary": summary,
                "content": full_content,
                "link": link,
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
    """Собирает новости из всех источников"""
    all_articles = []
    print("📡 Сбор новостей с картинками...")
    print("=" * 50)
    
    for name, url in RSS_FEEDS.items():
        print(f"  📰 {name}...")
        articles = fetch_rss_feed(url, name)
        print(f"     ✅ {len(articles)} новостей")
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
    
    # Считаем новости с картинками
    with_images = sum(1 for a in result if a['images'])
    print(f"🖼️ Новостей с картинками: {with_images}")
    
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
    print("🚀 АГРЕГАТОР НОВОСТЕЙ (полные тексты + картинки)")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    articles = fetch_all_news()
    
    if articles:
        save_news(articles)
        print("\n📰 Последние новости:")
        for i, art in enumerate(articles[:5], 1):
            print(f"   {i}. {art['title'][:60]}...")
            print(f"      📍 {art['source']}")
            print(f"      📝 Длина: {len(art['content'])} символов")
            if art['images']:
                print(f"      🖼️ Картинок: {len(art['images'])}")
            print()
    else:
        print("\n⚠️ Не удалось загрузить новости")
        demo_news = [{
            "id": "1",
            "title": "Добро пожаловать в Cognify AI News!",
            "summary": "Новости загружаются из RSS-лент с полными текстами до 5000 символов и изображениями.",
            "content": "Теперь каждая новость содержит полный текст, картинки и ссылку на оригинал. Наслаждайтесь чтением!",
            "link": "#",
            "source": "Cognify AI",
            "published_at": datetime.now().isoformat(),
            "tags": ["info"],
            "images": [],
            "preview_image": None,
        }]
        save_news(demo_news)

if __name__ == "__main__":
    main()
