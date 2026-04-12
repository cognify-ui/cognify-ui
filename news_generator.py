#!/usr/bin/env python3
import json
import os
import hashlib
import re
import time
import random
from datetime import datetime, timedelta
from google import genai

NEWS_FILE = "news.json"
MAX_ARTICLES = 50
MAX_RETRIES = 3

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ Ошибка: GEMINI_API_KEY не найден")
    exit(1)

print(f"✅ API ключ найден: {GEMINI_API_KEY[:15]}...")

client = genai.Client(api_key=GEMINI_API_KEY)

# Фиксированный список моделей для генерации
FIXED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
]

# SEO темы
SEO_TOPICS = [
    "chatgpt", "openai", "google gemini", "microsoft copilot", "claude ai",
    "midjourney", "stable diffusion", "dall-e 3", "ai art", "neural networks",
    "deep learning", "machine learning", "nvidia h100", "ai startup", "ai funding",
    "ai safety", "generative ai", "llm", "ai agents", "agi", "ai chip", "gpu",
    "quantum ai", "edge ai", "ai healthcare", "ai medicine", "ai finance",
    "ai education", "humanoid robot", "self-driving car", "computer vision",
    "ai video generation", "sora ai", "ai coding", "github copilot", "ai cybersecurity",
    "deepseek", "llama 3", "mistral ai", "perplexity ai",
    "iphone", "samsung galaxy", "google pixel", "playstation", "xbox",
    "nintendo switch", "windows", "macos", "android", "ios",
    "spotify", "netflix", "cybersecurity", "5g", "6g", "wifi 7",
    "smartwatch", "smart home", "iot", "electric car", "tesla", "spacex", "nasa",
    "quantum computing", "medical research", "cancer treatment", "gene editing",
    "crispr", "james webb", "mars mission", "climate change", "renewable energy",
    "fusion energy", "cryptocurrency", "bitcoin", "ethereum", "blockchain",
    "inflation", "global economy", "startup funding", "ipo",
    "elon musk", "jeff bezos", "mark zuckerberg",
]

# Конфигурация изображений
IMAGE_THEMES = {
    'chatgpt': {'style': 'bottts', 'color': '10a37f'},
    'openai': {'style': 'bottts', 'color': '10a37f'},
    'google': {'style': 'identicon', 'color': '4285f4'},
    'gemini': {'style': 'identicon', 'color': '8e6ced'},
    'microsoft': {'style': 'micah', 'color': '00a4ef'},
    'claude': {'style': 'adventurer', 'color': 'd97757'},
    'nvidia': {'style': 'bottts', 'color': '76b900'},
    'iphone': {'style': 'bottts', 'color': '34c759'},
    'samsung': {'style': 'bottts', 'color': '1428a0'},
    'tesla': {'style': 'bottts', 'color': 'e82127'},
    'spacex': {'style': 'bottts', 'color': '005288'},
    'bitcoin': {'style': 'identicon', 'color': 'f7931a'},
    'health': {'style': 'adventurer', 'color': '2ecc71'},
    'default': {'style': 'bottts', 'color': '6366f1'}
}

def get_available_models():
    """Возвращает доступные модели"""
    print("\n📋 Загружаем список моделей...")
    available_models = []
    
    try:
        api_models = []
        for model in client.models.list():
            model_name = model.name.replace('models/', '')
            api_models.append(model_name)
        
        for model in FIXED_MODELS:
            if model in api_models:
                available_models.append(model)
                print(f"   ✅ {model}")
        
        if not available_models and api_models:
            available_models = api_models[:3]
            
    except Exception as e:
        print(f"   ⚠️ Ошибка: {e}")
        available_models = FIXED_MODELS.copy()
    
    return available_models

def generate_news_with_model(model_name, prompt, retry_count=0):
    """Генерирует новость с указанной моделью"""
    try:
        print(f"   🧠 Пробуем {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        text = response.text
        
        # Извлекаем JSON
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
        
        article = json.loads(text)
        
        if all(k in article for k in ['title', 'summary', 'content', 'source', 'tags']):
            print(f"   ✅ Успех! {len(article['content'])} символов")
            return article
            
    except Exception as e:
        if "429" in str(e) and retry_count < MAX_RETRIES:
            print(f"   ⏳ Лимит, ждём 30 сек...")
            time.sleep(30)
            return generate_news_with_model(model_name, prompt, retry_count + 1)
        else:
            print(f"   ❌ Ошибка: {str(e)[:100]}")
    
    return None

def generate_news():
    """Генерирует новость"""
    models = get_available_models()
    if not models:
        print("❌ Нет моделей")
        return None
    
    for attempt in range(3):
        topic = random.choice(SEO_TOPICS)
        
        prompt = f"""Сгенерируй УНИКАЛЬНУЮ новость на тему: {topic}

ТРЕБОВАНИЯ:
1. Дата: сегодня или вчера
2. Источник: {random.choice(['The Verge', 'TechCrunch', 'Wired', 'Reuters', 'BBC News'])}
3. Язык: русский
4. Длина: 2000-5000 символов
5. Добавь цитаты и цифры

ФОРМАТ JSON:
{{
    "title": "Заголовок",
    "summary": "Краткое описание (до 350 символов)",
    "content": "Полный текст новости...",
    "source": "Источник",
    "tags": ["тег1", "тег2", "тег3", "тег4", "тег5"]
}}
"""
        
        for model in models:
            article = generate_news_with_model(model, prompt)
            if article:
                article['seo_topic'] = topic
                article['used_model'] = model
                article['generation_time'] = datetime.now().isoformat()
                return article
        
        time.sleep(20)
    
    return None

def generate_image_url(title, tags):
    """Генерирует URL изображения"""
    title_lower = title.lower()
    tags_lower = [t.lower() for t in tags]
    
    theme = 'default'
    for key in IMAGE_THEMES:
        if key in title_lower or any(key in tag for tag in tags_lower):
            theme = key
            break
    
    config = IMAGE_THEMES[theme]
    seed = hashlib.md5(f"{title}{datetime.now().date()}".encode()).hexdigest()[:10]
    
    return f"https://api.dicebear.com/7.x/{config['style']}/svg?seed={seed}&backgroundColor={config['color']}&radius=50"

def generate_news_html(article):
    """Генерирует HTML страницу для новости"""
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
    
    if published_at:
        pub_date = published_at.split('T')[0]
    else:
        pub_date = datetime.now().strftime('%Y-%m-%d')
    
    tags_html = ''.join([f'<a href="/?tag={html.escape(tag)}" class="tag">#{html.escape(tag)}</a>' for tag in tags[:5]])
    
    image_html = ''
    if image_url:
        image_html = f'<img class="article-image" src="{html.escape(image_url)}" alt="{title}">'
    
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
    <link rel="canonical" href="https://cognify-ui.github.io/news/{article_id}.html">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .article-image {{
            width: 100%;
            height: 400px;
            object-fit: cover;
        }}
        .article-content {{ padding: 40px; }}
        h1 {{ font-size: 32px; margin-bottom: 20px; }}
        .meta {{
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .content {{ font-size: 18px; line-height: 1.8; margin-bottom: 30px; }}
        .tags {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 30px 0; }}
        .tag {{
            background: #f0f0f0;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            color: #667eea;
            text-decoration: none;
        }}
        .back-link {{
            display: inline-block;
            margin-top: 30px;
            color: #667eea;
            text-decoration: none;
        }}
        @media (max-width: 768px) {{
            .article-content {{ padding: 20px; }}
            h1 {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {image_html}
        <div class="article-content">
            <h1>{title}</h1>
            <div class="meta">
                <span>📅 {pub_date}</span>
                <span>🔗 {source}</span>
                <span>📖 {len(article.get('content', ''))} символов</span>
            </div>
            <div class="content">{content}</div>
            <div class="tags">{tags_html}</div>
            <a href="/" class="back-link">← Назад к новостям</a>
        </div>
    </div>
</body>
</html>'''
    
    html_path = f"news/{article_id}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ Создана страница: {html_path}")
    return html_path

def generate_sitemap():
    """Генерирует sitemap.xml"""
    if not os.path.exists(NEWS_FILE):
        return
    
    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    today = datetime.now().strftime("%Y-%m-%d")
    
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += '  <url>\n'
    sitemap += '    <loc>https://cognify-ui.github.io/</loc>\n'
    sitemap += f'    <lastmod>{today}</lastmod>\n'
    sitemap += '    <changefreq>daily</changefreq>\n'
    sitemap += '    <priority>1.0</priority>\n'
    sitemap += '  </url>\n'
    
    for article in articles:
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
    
    print(f"✅ Sitemap создан: {len(articles) + 1} URL")

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
    print("✅ robots.txt создан")

def generate_rss_feed():
    """Генерация RSS фида"""
    import html
    if not os.path.exists(NEWS_FILE):
        return
    
    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])[:20]
    
    rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
    rss += '<channel>\n'
    rss += '    <title>Cognify AI News</title>\n'
    rss += '    <link>https://cognify-ui.github.io/</link>\n'
    rss += '    <description>AI news generated by Gemini</description>\n'
    rss += '    <language>ru</language>\n'
    rss += '    <lastBuildDate>' + datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000') + '</lastBuildDate>\n'
    rss += '    <atom:link href="https://cognify-ui.github.io/rss.xml" rel="self" type="application/rss+xml"/>\n'
    
    for article in articles:
        pub_date = article.get('published_at', '')
        try:
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            rss_date = dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
        except:
            rss_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        rss += '    <item>\n'
        rss += f'        <title>{html.escape(article["title"])}</title>\n'
        rss += f'        <link>https://cognify-ui.github.io/news/{article["id"]}.html</link>\n'
        rss += f'        <description>{html.escape(article["summary"][:500])}</description>\n'
        rss += f'        <pubDate>{rss_date}</pubDate>\n'
        rss += f'        <guid>https://cognify-ui.github.io/news/{article["id"]}.html</guid>\n'
        rss += '    </item>\n'
    
    rss += '</channel>\n</rss>'
    
    with open('rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss)
    
    print("✅ RSS фид создан")

def clean_and_fix_news_file():
    """Очищает и восстанавливает news.json файл"""
    if not os.path.exists(NEWS_FILE):
        return {"last_updated": "", "articles": [], "total_articles": 0}
    
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'articles' not in data:
            data = {"last_updated": "", "articles": [], "total_articles": 0}
        
        clean_articles = []
        seen_titles = set()
        
        for article in data.get('articles', []):
            if not all(k in article for k in ['id', 'title', 'published_at']):
                continue
            
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                clean_articles.append(article)
        
        clean_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        clean_articles = clean_articles[:MAX_ARTICLES]
        
        result = {
            "last_updated": datetime.now().isoformat(),
            "articles": clean_articles,
            "total_articles": len(clean_articles)
        }
        
        with open(NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Очищено: {len(clean_articles)} статей")
        return result
        
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return {"last_updated": "", "articles": [], "total_articles": 0}

def save_news_article(article):
    """Сохраняет новость"""
    existing = clean_and_fix_news_file()
    
    article_id = hashlib.md5(f"{article['title']}{datetime.now()}".encode()).hexdigest()[:12]
    image_url = generate_image_url(article['title'], article.get('tags', []))
    
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
        "seo_metadata": {
            "meta_title": f"{article.get('title')} | Cognify AI News",
            "meta_description": article.get('summary', '')[:160],
            "meta_keywords": ", ".join(article.get('tags', [])),
        }
    }
    
    existing_titles = [a.get('title') for a in existing.get('articles', [])]
    if new_article['title'] in existing_titles:
        print(f"⚠️ Дубликат!")
        return False
    
    existing['articles'].insert(0, new_article)
    existing['articles'] = existing['articles'][:MAX_ARTICLES]
    existing['last_updated'] = datetime.now().isoformat()
    existing['total_articles'] = len(existing['articles'])
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    generate_news_html(new_article)
    generate_sitemap()
    generate_robots_txt()
    generate_rss_feed()
    
    print(f"\n✅ Сохранено! Всего: {len(existing['articles'])}")
    print(f"📰 {new_article['title'][:80]}...")
    return True

def create_demo_news():
    """Создаёт демо-новость"""
    demo = {
        "title": "Cognify AI: Бесплатный доступ к 4 мощным AI моделям",
        "summary": "Откройте мир искусственного интеллекта бесплатно! Cognify AI предоставляет доступ к Groq, Cerebras, Cloudflare AI и Google Gemini без ограничений.",
        "content": "Cognify AI — инновационная платформа, объединяющая 4 передовые AI модели. Пользователи могут общаться с Groq, Cerebras, Cloudflare AI и Google Gemini абсолютно бесплатно. Сервис предлагает историю чатов, систему аккаунтов и интуитивный интерфейс.",
        "source": "Cognify AI",
        "tags": ["cognify", "бесплатный ai", "groq", "cerebras", "gemini"],
        "seo_topic": "free ai",
        "used_model": "demo"
    }
    return save_news_article(demo)

def main():
    print("=" * 60)
    print(f"🚀 ЗАПУСК ГЕНЕРАТОРА НОВОСТЕЙ")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    clean_and_fix_news_file()
    
    article = generate_news()
    
    if article:
        success = save_news_article(article)
        if not success:
            print("⚠️ Дубликат, пробуем ещё раз...")
            article = generate_news()
            if article:
                save_news_article(article)
    else:
        print("❌ Не удалось сгенерировать новость")
        
        if os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, 'r') as f:
                data = json.load(f)
                if len(data.get('articles', [])) == 0:
                    create_demo_news()
        else:
            create_demo_news()
    
    print("\n" + "=" * 60)
    print("✅ ГОТОВО!")
    print("=" * 60)

if __name__ == "__main__":
    main()
