#!/usr/bin/env python3
import json
import os
import hashlib
import re
import time
import random
from datetime import datetime
from google import genai
import requests
from bs4 import BeautifulSoup

NEWS_FILE = "news.json"
MAX_ARTICLES = 1000

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ Ошибка: GEMINI_API_KEY не найден")
    exit(1)

print(f"✅ API ключ найден: {GEMINI_API_KEY[:15]}...")

client = genai.Client(api_key=GEMINI_API_KEY)

# Модели для генерации текста
FIXED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

# ==================== ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ====================

def generate_image_for_article(title, summary, tags, seo_topic):
    """Генерирует уникальное изображение для статьи с помощью Gemini Imagen"""
    
    print(f"   🎨 Генерируем изображение для статьи...")
    
    # Создаем детальный промпт для генерации изображения
    image_prompt = f"""Create a professional, high-quality illustration for a tech news article with the following details:

ARTICLE TITLE: {title}
TOPIC: {seo_topic}
TAGS: {', '.join(tags[:5])}
SUMMARY: {summary}

Requirements:
- Modern, clean, professional style
- Relevant to the topic
- Suitable for a tech news website header
- No text on the image
- High resolution, vibrant colors
- Futuristic but realistic style
- Eye-catching and engaging

Style inspiration: Wired, TechCrunch, MIT Technology Review"""

    try:
        # Пытаемся использовать Gemini Imagen (если доступно)
        response = client.models.generate_content(
            model="imagen-3.0-generate-001",  # Модель для генерации изображений
            contents=image_prompt,
            config={
                "temperature": 0.8,
                "candidate_count": 1,
            }
        )
        
        # Проверяем, есть ли сгенерированное изображение
        if hasattr(response, 'candidates') and response.candidates:
            # Получаем base64 изображения
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                    import base64
                    image_data = part.inline_data.data
                    
                    # Сохраняем изображение временно
                    temp_path = f"/tmp/article_img_{hashlib.md5(title.encode()).hexdigest()[:8]}.png"
                    with open(temp_path, 'wb') as f:
                        f.write(image_data)
                    
                    # Загружаем на бесплатный хостинг (imgbb или подобный)
                    image_url = upload_image_to_hosting(temp_path)
                    
                    # Удаляем временный файл
                    os.remove(temp_path)
                    
                    if image_url:
                        print(f"   ✅ Изображение создано и загружено!")
                        return image_url
                    
    except Exception as e:
        print(f"   ⚠️ Imagen не доступен: {str(e)[:80]}")
    
    # Fallback: Генерируем URL через DiceBear с тематическими параметрами
    print(f"   🎨 Используем стилизованный fallback...")
    return generate_themed_dicebear_image(title, tags, seo_topic)

def upload_image_to_hosting(image_path):
    """Загружает изображение на бесплатный хостинг (imgbb)"""
    
    # Бесплатный API ключ для ImgBB (можно зарегистрироваться бесплатно)
    IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY', '6d207e02198a847aa98d0a2a901485a5')  # Демо ключ
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'key': IMGBB_API_KEY}
            
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['data']['url']
                    
    except Exception as e:
        print(f"   ⚠️ Ошибка загрузки: {str(e)[:50]}")
    
    return None

def generate_themed_dicebear_image(title, tags, seo_topic):
    """Генерирует тематическое изображение через DiceBear API"""
    
    # Создаем seed на основе заголовка и тегов
    seed_text = f"{title} {' '.join(tags[:3])} {seo_topic}"
    seed = hashlib.md5(seed_text.encode()).hexdigest()[:16]
    
    # Выбираем стиль в зависимости от темы
    styles = {
        'ai': 'bottts',
        'tech': 'identicon',
        'space': 'pixel-art',
        'science': 'micah',
        'default': 'adventurer'
    }
    
    style = styles.get(seo_topic, styles['default'])
    
    # Определяем тему для цвета
    if 'ai' in seo_topic or 'нейросеть' in seo_topic:
        bg_color = '6366f1'  # Индиго
        icon = 'sparkles'
    elif 'космос' in seo_topic or 'space' in seo_topic:
        bg_color = '1e1b4b'  # Темно-синий
        icon = 'rocket'
    elif 'робот' in seo_topic:
        bg_color = '0f766e'  # Тиркуаз
        icon = 'robot'
    elif 'биотех' in seo_topic:
        bg_color = '15803d'  # Зеленый
        icon = 'leaf'
    else:
        bg_color = '7c3aed'  # Фиолетовый
        icon = 'bulb'
    
    # Генерируем URL с кастомными параметрами
    image_url = f"https://api.dicebear.com/7.x/{style}/png?seed={seed}&backgroundColor={bg_color}&radius=50&size=1200x600"
    
    print(f"   ✅ Тематическое изображение: {style} стиль")
    return image_url

# ==================== СБОР РЕАЛЬНЫХ НОВОСТЕЙ ====================

def fetch_real_news():
    """Собирает реальные новости из интернета"""
    all_news = []
    
    print("\n📡 Собираем реальные новости...")
    
    # RSS источники (бесплатные и легальные)
    rss_feeds = [
        {"url": "https://techcrunch.com/feed/", "source": "TechCrunch", "category": "tech"},
        {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge", "category": "tech"},
        {"url": "https://www.wired.com/feed/rss", "source": "Wired", "category": "tech"},
        {"url": "https://arstechnica.com/feed/", "source": "Ars Technica", "category": "tech"},
        {"url": "https://www.sciencedaily.com/rss/all.xml", "source": "Science Daily", "category": "science"},
        {"url": "https://www.space.com/feeds/all", "source": "Space.com", "category": "space"},
        {"url": "https://news.mit.edu/rss", "source": "MIT News", "category": "science"},
        {"url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "source": "NASA", "category": "space"},
        {"url": "https://www.newscientist.com/feed/home", "source": "New Scientist", "category": "science"},
        {"url": "https://www.technologyreview.com/feed/", "source": "MIT Tech Review", "category": "tech"},
    ]
    
    for feed in rss_feeds:
        try:
            print(f"   📰 Читаем {feed['source']}...")
            response = requests.get(feed['url'], timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)
                
                for item in items[:5]:
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    desc_match = re.search(r'<description>(.*?)</description>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                    
                    if title_match and link_match:
                        title = title_match.group(1)
                        description = desc_match.group(1) if desc_match else ""
                        description = re.sub(r'<[^>]+>', '', description)[:300]
                        
                        all_news.append({
                            "title": title,
                            "summary": description,
                            "url": link_match.group(1),
                            "source": feed['source'],
                            "category": feed['category'],
                            "published": pub_match.group(1) if pub_match else datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
                        })
                        
            print(f"      ✅ Найдено {len([i for i in items[:5]])} новостей")
            
        except Exception as e:
            print(f"      ⚠️ Ошибка: {str(e)[:50]}")
            continue
        
        time.sleep(0.5)
    
    # Hacker News
    try:
        print(f"   📰 Читаем Hacker News...")
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        if response.status_code == 200:
            top_ids = response.json()[:10]
            for news_id in top_ids:
                news_response = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{news_id}.json", timeout=10)
                if news_response.status_code == 200:
                    news_data = news_response.json()
                    if news_data.get('title') and news_data.get('url'):
                        all_news.append({
                            "title": news_data['title'],
                            "summary": news_data.get('text', '')[:200] or news_data.get('title'),
                            "url": news_data['url'],
                            "source": "Hacker News",
                            "category": "tech",
                            "published": datetime.fromtimestamp(news_data.get('time', 0)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                        })
        print(f"      ✅ Найдено новостей: {len(top_ids)}")
    except Exception as e:
        print(f"      ⚠️ Hacker News ошибка: {str(e)[:50]}")
    
    print(f"\n✅ Всего собрано реальных новостей: {len(all_news)}")
    return all_news

def generate_news_from_real_events(real_news):
    """Генерирует уникальную статью на основе реальных новостей"""
    
    if not real_news:
        return None
    
    selected_news = random.sample(real_news, min(3, len(real_news)))
    
    context = "Вот реальные новости из интернета за сегодня:\n\n"
    for i, news in enumerate(selected_news, 1):
        context += f"""
НОВОСТЬ {i}:
Источник: {news['source']}
Заголовок: {news['title']}
Описание: {news['summary']}
Ссылка: {news['url']}
---
"""
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    current_date_full = datetime.now().strftime("%d %B %Y")
    current_year = datetime.now().strftime("%Y")
    
    prompt = f"""Ты - профессиональный журналист. Напиши уникальную новость-дайджест на основе реальных новостей ниже.

{context}

Требования:
- Язык: русский
- Длина: 2000-4000 символов
- СЕГОДНЯШНЯЯ ДАТА: {current_date} ({current_date_full})
- Объедини эти новости в связную статью
- Добавь свои аналитические выводы и комментарии экспертов
- Упомяни все источники в тексте

ВАЖНО: Используй ТОЛЬКО сегодняшнюю дату: {current_date}

Ответ дай ТОЛЬКО в формате JSON:
{{
    "title": "Заголовок новости-дайджеста",
    "summary": "Краткое описание (150-200 символов)",
    "content": "Полный текст новости (сегодня {current_date})...",
    "source": "Cognify AI News",
    "tags": ["тег1", "тег2", "тег3", "тег4", "тег5"]
}}
"""
    
    for model in FIXED_MODELS:
        try:
            print(f"   🧠 Генерируем статью через {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            text = response.text
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end+1]
            
            article = json.loads(text)
            
            required = ['title', 'summary', 'content', 'source', 'tags']
            if all(k in article for k in required):
                article['content'] = re.sub(r'\d{1,2}\.\d{1,2}\.\d{4}', current_date, article['content'])
                article['content'] = re.sub(r'\d{1,2} \w+ \d{4}', current_date_full, article['content'])
                
                article['seo_topic'] = "news_digest"
                article['used_model'] = model
                article['generated_date'] = current_date
                article['real_sources'] = [n['source'] for n in selected_news]
                article['source_urls'] = [n['url'] for n in selected_news]
                
                print(f"   ✅ Успех! Длина: {len(article['content'])} символов")
                return article
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
            continue
        
        time.sleep(2)
    
    return None

def generate_news_article():
    """Генерирует одну новость"""
    
    real_news = fetch_real_news()
    
    if real_news:
        print("\n📝 Генерируем уникальную статью на основе реальных новостей...")
        article = generate_news_from_real_events(real_news)
        if article:
            return article
    
    print("\n⚠️ Используем резервный метод генерации...")
    
    TOPICS = [
        "искусственный интеллект", "нейросети", "chatgpt", "openai", "google gemini",
        "робототехника", "квантовые вычисления", "биотехнологии", "космос", "IT инновации"
    ]
    
    topic = random.choice(TOPICS)
    current_date = datetime.now().strftime("%d.%m.%Y")
    current_date_full = datetime.now().strftime("%d %B %Y")
    current_year = datetime.now().strftime("%Y")
    
    prompt = f"""Ты - профессиональный журналист. Напиши уникальную новость на тему "{topic}".

Требования:
- Язык: русский
- Длина: 2000-4000 символов
- СЕГОДНЯШНЯЯ ДАТА: {current_date} ({current_date_full})
- ГОД: {current_year}
- Добавь цитаты экспертов и конкретные цифры
- Источник: любое известное техно-издание

ВАЖНО: Используй ТОЛЬКО сегодняшнюю дату: {current_date}

Ответ дай ТОЛЬКО в формате JSON:
{{
    "title": "Заголовок новости",
    "summary": "Краткое описание",
    "content": "Полный текст новости (сегодня {current_date})...",
    "source": "Название источника",
    "tags": ["тег1", "тег2", "тег3", "тег4", "тег5"]
}}
"""
    
    for model in FIXED_MODELS:
        try:
            print(f"   🧠 Пробуем {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            text = response.text
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end+1]
            
            article = json.loads(text)
            
            required = ['title', 'summary', 'content', 'source', 'tags']
            if all(k in article for k in required):
                article['content'] = re.sub(r'\d{1,2}\.\d{1,2}\.\d{4}', current_date, article['content'])
                article['content'] = re.sub(r'\d{1,2} \w+ \d{4}', current_date_full, article['content'])
                
                print(f"   ✅ Успех! Длина: {len(article['content'])} символов")
                article['seo_topic'] = topic
                article['used_model'] = model
                article['generated_date'] = current_date
                return article
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
            continue
        
        time.sleep(2)
    
    return None

# ==================== ОСТАЛЬНЫЕ ФУНКЦИИ ====================

def load_existing_news():
    """Загружает существующие новости"""
    if not os.path.exists(NEWS_FILE):
        return {"articles": []}
    
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"articles": []}

def generate_sitemap(articles):
    """Генерирует sitemap.xml"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += '  <url>\n'
    sitemap += '    <loc>https://cognify-ui.github.io/</loc>\n'
    sitemap += f'    <lastmod>{today}</lastmod>\n'
    sitemap += '    <changefreq>daily</changefreq>\n'
    sitemap += '    <priority>1.0</priority>\n'
    sitemap += '  </url>\n'
    
    for article in articles[:20]:
        pub_date = article.get('published_at', today)[:10]
        sitemap += '  <url>\n'
        sitemap += f'    <loc>https://cognify-ui.github.io/news/{article["id"]}.html</loc>\n'
        sitemap += f'    <lastmod>{pub_date}</lastmod>\n'
        sitemap += '    <changefreq>weekly</changefreq>\n'
        sitemap += '    <priority>0.8</priority>\n'
        sitemap += '  </url>\n'
    
    sitemap += '</urlset>'
    
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap)
    
    print(f"   ✅ Sitemap создан: {len(articles[:20]) + 1} URL")

def generate_robots_txt():
    """Создает robots.txt"""
    robots = '''User-agent: *
Allow: /
Sitemap: https://cognify-ui.github.io/sitemap.xml
Disallow: /news.json
Disallow: /news_generator.py
'''
    with open('robots.txt', 'w', encoding='utf-8') as f:
        f.write(robots)
    print("   ✅ robots.txt создан")

def generate_news_html(article):
    """Генерирует HTML страницу для новости с красивым изображением"""
    import html
    os.makedirs('news', exist_ok=True)
    
    title = html.escape(article.get('title', 'Новость'))
    summary = html.escape(article.get('summary', ''))
    content = html.escape(article.get('content', '')).replace('\n', '<br>')
    source = html.escape(article.get('source', 'Cognify AI'))
    article_id = article.get('id', '')
    image_url = article.get('image_url', '')
    published_at = article.get('published_at', '')
    tags = article.get('tags', [])
    
    sources_html = ""
    if article.get('real_sources'):
        sources_html = '<div class="sources"><strong>📚 Источники:</strong><br>'
        for src in article.get('real_sources', []):
            sources_html += f'• {html.escape(src)}<br>'
        sources_html += '</div>'
    
    if published_at:
        pub_date = published_at.split('T')[0]
    else:
        pub_date = datetime.now().strftime('%Y-%m-%d')
    
    tags_html = ''.join([f'<a href="/?tag={html.escape(tag)}" class="tag">#{html.escape(tag)}</a>' for tag in tags[:5]])
    
    image_html = ''
    if image_url:
        image_html = f'''
        <div class="article-image-container">
            <img class="article-image" src="{html.escape(image_url)}" alt="{title}" loading="eager">
            <div class="image-overlay"></div>
        </div>'''
    
    html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Cognify AI News</title>
    <meta name="description" content="{summary[:160]}">
    <meta name="keywords" content="{', '.join(tags)}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{summary[:200]}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:url" content="https://cognify-ui.github.io/news/{article_id}.html">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Cognify AI News">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="{image_url}">
    <link rel="canonical" href="https://cognify-ui.github.io/news/{article_id}.html">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
            transition: transform 0.3s ease;
        }}
        .container:hover {{
            transform: translateY(-5px);
        }}
        .article-image-container {{
            position: relative;
            width: 100%;
            height: 450px;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .article-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }}
        .article-image:hover {{
            transform: scale(1.05);
        }}
        .image-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 100px;
            background: linear-gradient(to top, rgba(0,0,0,0.5), transparent);
        }}
        .article-content {{ padding: 48px; }}
        h1 {{
            font-size: 38px;
            margin-bottom: 24px;
            line-height: 1.3;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .meta {{
            display: flex;
            gap: 24px;
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 2px solid #f3f4f6;
            flex-wrap: wrap;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .content {{
            font-size: 18px;
            line-height: 1.8;
            color: #374151;
            margin-bottom: 40px;
        }}
        .content p {{
            margin-bottom: 20px;
        }}
        .sources {{
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            padding: 20px;
            border-radius: 16px;
            margin: 32px 0;
            font-size: 14px;
            border-left: 4px solid #667eea;
        }}
        .tags {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 32px 0; }}
        .tag {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 8px 20px;
            border-radius: 25px;
            font-size: 13px;
            color: white;
            text-decoration: none;
            transition: transform 0.2s, box-shadow 0.2s;
            display: inline-block;
        }}
        .tag:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 40px;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: gap 0.3s;
        }}
        .back-link:hover {{
            gap: 12px;
        }}
        @media (max-width: 768px) {{
            .article-content {{ padding: 24px; }}
            h1 {{ font-size: 28px; }}
            .article-image-container {{ height: 300px; }}
            .meta {{ gap: 16px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {image_html}
        <div class="article-content">
            <h1>{title}</h1>
            <div class="meta">
                <div class="meta-item">📅 {pub_date}</div>
                <div class="meta-item">🔗 {source}</div>
                <div class="meta-item">📖 {len(article.get('content', ''))} символов</div>
                <div class="meta-item">⚡ {article.get('used_model', 'AI').upper()}</div>
            </div>
            <div class="content">{content}</div>
            {sources_html}
            <div class="tags">{tags_html}</div>
            <a href="/" class="back-link">← На главную</a>
        </div>
    </div>
</body>
</html>'''
    
    html_path = f"news/{article_id}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ Создана страница: {html_path}")
    return html_path

def save_news_article(article):
    """Сохраняет новость с генерацией изображения"""
    data = load_existing_news()
    
    article_id = hashlib.md5(f"{article['title']}{datetime.now()}".encode()).hexdigest()[:12]
    
    # ГЕНЕРИРУЕМ УНИКАЛЬНОЕ ИЗОБРАЖЕНИЕ
    print("\n🎨 Генерируем тематическое изображение...")
    image_url = generate_image_for_article(
        title=article.get('title', ''),
        summary=article.get('summary', ''),
        tags=article.get('tags', []),
        seo_topic=article.get('seo_topic', 'news')
    )
    
    new_article = {
        "id": article_id,
        "title": article.get('title'),
        "summary": article.get('summary'),
        "content": article.get('content'),
        "source": article.get('source'),
        "source_url": f"https://cognify-ui.github.io/news/{article_id}.html",
        "published_at": datetime.now().isoformat(),
        "tags": article.get('tags', ['news']),
        "seo_topic": article.get('seo_topic', 'news'),
        "used_model": article.get('used_model', 'unknown'),
        "image_url": image_url,
        "real_sources": article.get('real_sources', []),
        "seo_metadata": {
            "meta_title": f"{article.get('title')} | Cognify AI News",
            "meta_description": article.get('summary', '')[:160],
            "meta_keywords": ", ".join(article.get('tags', [])),
        }
    }
    
    existing_titles = [a.get('title') for a in data.get('articles', [])]
    if new_article['title'] in existing_titles:
        print(f"   ⚠️ Дубликат, пропускаем")
        return False
    
    if 'articles' not in data:
        data['articles'] = []
    
    data['articles'].insert(0, new_article)
    data['articles'] = data['articles'][:MAX_ARTICLES]
    data['last_updated'] = datetime.now().isoformat()
    data['total_articles'] = len(data['articles'])
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    generate_news_html(new_article)
    generate_sitemap(data['articles'])
    generate_robots_txt()
    
    print(f"\n✅ Сохранено! Всего: {len(data['articles'])}")
    print(f"📰 {new_article['title'][:80]}...")
    print(f"🖼️ Изображение: {image_url[:80]}...")
    print(f"📅 Дата: {new_article['published_at'][:10]}")
    
    return True

def main():
    print("=" * 60)
    print(f"🚀 ЗАПУСК ГЕНЕРАТОРА НОВОСТЕЙ (С AI ИЗОБРАЖЕНИЯМИ)")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Сегодня: {datetime.now().strftime('%d.%m.%Y')}")
    print("=" * 60)
    
    article = generate_news_article()
    
    if article:
        success = save_news_article(article)
        if not success:
            print("\n⚠️ Дубликат, пробуем ещё раз...")
            article = generate_news_article()
            if article:
                save_news_article(article)
    else:
        print("\n❌ Не удалось сгенерировать новость")
        
        data = load_existing_news()
        if len(data.get('articles', [])) == 0:
            print("\n📝 Создаём демо-новость...")
            demo = {
                "title": "Cognify AI: Бесплатный доступ к 4 AI моделям",
                "summary": "Откройте мир искусственного интеллекта бесплатно! Cognify AI предоставляет доступ к Groq, Cerebras, Cloudflare AI и Google Gemini.",
                "content": f"Cognify AI — инновационная платформа, объединяющая 4 передовые AI модели. Пользователи могут общаться с Groq, Cerebras, Cloudflare AI и Google Gemini абсолютно бесплатно. Дата запуска: {datetime.now().strftime('%d.%m.%Y')}",
                "source": "Cognify AI",
                "tags": ["cognify", "бесплатный ai", "groq", "cerebras", "gemini"],
                "seo_topic": "free ai",
                "used_model": "demo"
            }
            save_news_article(demo)
    
    print("\n" + "=" * 60)
    print("✅ ГОТОВО! Все статьи с уникальными AI-изображениями")
    print("=" * 60)

if __name__ == "__main__":
    main()
