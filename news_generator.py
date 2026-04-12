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
    print("Добавьте секрет в GitHub: Settings → Secrets and variables → Actions")
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

# ========== РАСШИРЕННЫЕ ТЕМЫ ДЛЯ НОВОСТЕЙ (ВСЕ ПОПУЛЯРНЫЕ ТЕМЫ) ==========
SEO_TOPICS = [
    # === AI и ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ ===
    "chatgpt", "openai", "google gemini", "microsoft copilot", "claude ai",
    "midjourney", "stable diffusion", "dall-e 3", "ai art", "neural networks",
    "deep learning", "machine learning", "data science", "nvidia h100", "amd instinct",
    "ai startup", "ai investment", "ai funding", "eu ai act", "ai safety",
    "china ai", "us ai", "europe ai", "ai ethics", "artificial general intelligence",
    "generative ai", "llm", "large language model", "ai agents", "agi",
    "ai chip", "gpu", "ai hardware", "quantum ai", "edge ai", "cloud ai",
    "ai healthcare", "ai medicine", "ai finance", "ai education", "humanoid robot",
    "self-driving car", "autonomous vehicle", "computer vision", "nlp", "speech recognition",
    "ai video generation", "sora ai", "runway ml", "pika labs", "ai music generation",
    "ai coding", "github copilot", "cursor ai", "ai programming", "ai cybersecurity",
    "deepseek", "qwen", "llama 3", "mistral ai", "perplexity ai",
    
    # === ТЕХНОЛОГИИ ===
    "iphone 17", "samsung galaxy s25", "xiaomi 15", "google pixel 10", "oneplus 13",
    "apple vision pro", "meta quest 4", "playstation 6", "xbox series next",
    "nintendo switch 2", "steam deck 2", "windows 12", "macos sequoia", "android 16",
    "ios 19", "telegram update", "whatsapp new features", "instagram updates",
    "tiktok news", "youtube new features", "spotify ai", "netflix changes",
    "disney plus updates", "cybersecurity threat", "hacker attack", "data breach",
    "5g rollout", "6g technology", "wifi 7", "bluetooth 6", "usb c",
    "foldable phone", "smartwatch", "fitness tracker", "smart home", "iot",
    "electric car", "tesla", "ev charging", "autonomous driving", "spacex",
    "starship", "nasa mission", "blue origin", "space news", "rocket launch",
    
    # === НАУКА ===
    "physics discovery", "quantum computing", "biology breakthrough", "medical research",
    "vaccine news", "cancer treatment", "gene editing", "crispr", "space telescope",
    "james webb", "mars mission", "moon landing", "climate change", "renewable energy",
    "solar power", "fusion energy", "nuclear reactor", "battery technology",
    "archaeology discovery", "dinosaur fossil", "ancient civilization", "paleontology",
    "ocean exploration", "deep sea", "volcano eruption", "earthquake prediction",
    
    # === БИЗНЕС И ЭКОНОМИКА ===
    "stock market", "cryptocurrency", "bitcoin news", "ethereum", "blockchain",
    "real estate", "inflation", "interest rates", "fed decision", "global economy",
    "china economy", "us economy", "europe economy", "startup funding", "ipo news",
    "merger acquisition", "billionaire news", "elon musk", "jeff bezos", "mark zuckerberg",
    "tesla stock", "apple stock", "nvidia stock", "microsoft stock", "amazon stock",
    "gold price", "oil price", "forex market", "crypto market", "defi",
    
    # === ЗДОРОВЬЕ ===
    "health news", "wellness tips", "nutrition", "fitness trends", "mental health",
    "covid update", "flu season", "pandemic news", "who announcement", "healthcare reform",
    "telemedicine", "digital health", "wearable health tech", "sleep science",
    "longevity", "anti aging", "stem cell research", "personalized medicine",
    
    # === СПОРТ ===
    "football news", "soccer transfer", "premier league", "champions league", "world cup",
    "basketball nba", "lebron james", "stephen curry", "nba finals", "olympics",
    "tennis grand slam", "novak djokovic", "carlos alcaraz", "us open", "wimbledon",
    "formula 1", "max verstappen", "lewis hamilton", "f1 race", "grand prix",
    "boxing fight", "mma ufc", "conor mcgregor", "heavyweight championship",
    "hockey nhl", "baseball mlb", "cricket world cup", "rugby championship",
    
    # === РАЗВЛЕЧЕНИЯ ===
    "hollywood news", "blockbuster movie", "oscar winners", "netflix series", "tv show",
    "marvel movie", "dc universe", "star wars", "game of thrones", "stranger things",
    "kpop news", "bts comeback", "blackpink", "newjeans", "music release",
    "concert tour", "taylor swift", "beyonce", "the weeknd", "bad bunny",
    "celeb gossip", "celebrity news", "royal family", "kardashians", "reality tv",
    
    # === ОБЩЕСТВО ===
    "world news", "politics", "election news", "president news", "government policy",
    "climate action", "environmental news", "sustainability", "green energy",
    "education reform", "school news", "university ranking", "student life",
    "travel news", "tourism trends", "best destinations", "aviation news",
    "crime news", "legal news", "court ruling", "law changes"
]

# Конфигурация изображений по темам
IMAGE_THEMES = {
    'chatgpt': {'style': 'bottts', 'color': '10a37f'},
    'openai': {'style': 'bottts', 'color': '10a37f'},
    'google': {'style': 'identicon', 'color': '4285f4'},
    'gemini': {'style': 'identicon', 'color': '8e6ced'},
    'microsoft': {'style': 'micah', 'color': '00a4ef'},
    'copilot': {'style': 'micah', 'color': '00a4ef'},
    'claude': {'style': 'adventurer', 'color': 'd97757'},
    'meta': {'style': 'lorelei', 'color': '0064e1'},
    'midjourney': {'style': 'pixel-art', 'color': 'ff6b35'},
    'stable diffusion': {'style': 'pixel-art', 'color': 'ff6b35'},
    'nvidia': {'style': 'bottts', 'color': '76b900'},
    'robot': {'style': 'bottts', 'color': '6b7280'},
    'autonomous': {'style': 'bottts', 'color': 'ef4444'},
    'iphone': {'style': 'bottts', 'color': '34c759'},
    'samsung': {'style': 'bottts', 'color': '1428a0'},
    'playstation': {'style': 'bottts', 'color': '003791'},
    'xbox': {'style': 'bottts', 'color': '107c10'},
    'nintendo': {'style': 'bottts', 'color': 'e60012'},
    'tesla': {'style': 'bottts', 'color': 'e82127'},
    'spacex': {'style': 'bottts', 'color': '005288'},
    'nasa': {'style': 'bottts', 'color': '0b3d91'},
    'bitcoin': {'style': 'identicon', 'color': 'f7931a'},
    'health': {'style': 'adventurer', 'color': '2ecc71'},
    'sport': {'style': 'micah', 'color': 'e67e22'},
    'movie': {'style': 'pixel-art', 'color': '9b59b6'},
    'default': {'style': 'bottts', 'color': '6366f1'}
}

def get_available_models():
    """Возвращает фиксированный список моделей для генерации"""
    print("\n📋 Загружаем список моделей для генерации...")
    
    available_models = []
    api_models = []
    
    try:
        for model in client.models.list():
            if 'generateContent' in str(model.supported_methods):
                model_name = model.name.replace('models/', '')
                api_models.append(model_name)
        
        print(f"   📡 Найдено моделей в API: {len(api_models)}")
        
        for model in FIXED_MODELS:
            if model in api_models:
                available_models.append(model)
                print(f"   ✅ {model} - доступна")
            else:
                print(f"   ⚠️ {model} - не найдена в API, пропускаем")
        
        if not available_models and api_models:
            available_models = api_models[:3]
            print(f"   📌 Используем первые 3 доступные модели: {available_models}")
            
    except Exception as e:
        print(f"   ⚠️ Ошибка проверки API: {e}")
        available_models = FIXED_MODELS.copy()
        print(f"   📌 Используем фиксированный список из {len(available_models)} моделей")
    
    print(f"\n📊 Итоговый список для генерации ({len(available_models)} моделей):")
    for i, model in enumerate(available_models, 1):
        print(f"   {i}. {model}")
    
    return available_models

def get_seo_prompt(topic=None):
    """Генерирует SEO-оптимизированный промпт для новости с текстом 1500-10000 символов"""
    if not topic:
        topic = random.choice(SEO_TOPICS)
    
    # Случайная длина текста от 1500 до 10000 символов
    target_length = random.randint(1500, 10000)
    
    sources = [
        "The Verge", "TechCrunch", "Wired", "VentureBeat", "Ars Technica",
        "MIT Technology Review", "IEEE Spectrum", "Analytics India Magazine",
        "ZDNet", "CNET", "Engadget", "The Information", "Reuters", "BBC News",
        "CNN", "The Guardian", "Forbes", "Bloomberg", "Wall Street Journal"
    ]
    
    seo_keywords = [
        "искусственный интеллект", "AI", "нейросети", "машинное обучение",
        "технологии будущего", "инновации", "цифровая трансформация",
        "прорыв", "открытие", "исследование", "новый стандарт"
    ]
    
    prompt = f"""
Ты — профессиональный журналист, специализирующийся на актуальных новостях. Сгенерируй УНИКАЛЬНУЮ, ИНТЕРЕСНУЮ, ДЕТАЛЬНУЮ новость на тему: {topic}

ВАЖНЫЕ ТРЕБОВАНИЯ:
1. Дата публикации: сегодня или вчера
2. Источник: {random.choice(sources)}
3. Язык: русский (качественный, профессиональный, литературный)
4. Новость должна быть SEO-оптимизирована для поисковых систем
5. Используй естественные ключевые слова: {', '.join(random.sample(seo_keywords, 3))}
6. **ДЛИНА ТЕКСТА: от 1500 до 10000 символов (цель - {target_length} символов)**
7. Добавь цитаты "экспертов" и "аналитиков"
8. Включи конкретные цифры, даты, статистику
9. Разбей текст на логические абзацы (3-6 абзацев)
10. Добавь подзаголовки внутри текста (например: "Что произошло?", "Анализ ситуации", "Мнение экспертов", "Что дальше?")

СТРУКТУРА НОВОСТИ:
- Заголовок: привлекательный, с ключевыми словами (60-100 символов)
- Краткое описание: 2-3 предложения, интригующее, с главной мыслью (до 350 символов)
- Полный текст: ДЕТАЛЬНЫЙ, ОБЪЕМНЫЙ (1500-10000 символов), раскрывающий:
  * Что произошло (факты, хронология)
  * Почему это важно (контекст, значение)
  * Детали события (технические подробности, участники)
  * Мнения экспертов (2-3 цитаты)
  * Прогнозы и последствия (что будет дальше)
- Теги: 5-7 релевантных тегов (включая {topic})

ФОРМАТ ОТВЕТА - ТОЛЬКО JSON (без лишнего текста):
{{
    "title": "Заголовок новости",
    "summary": "Краткое описание с ключевыми выводами (до 350 символов)",
    "content": "Полный текст новости. Здесь должно быть {target_length} символов. Подробно, с цитатами экспертов, цифрами, анализом. Например: 'По словам аналитика IDC, этот прорыв изменит рынок. По данным исследования, 78% компаний планируют внедрение...' Текст должен быть информативным, увлекательным и полезным для читателя.",
    "source": "Название источника",
    "tags": ["тег1", "тег2", "тег3", "тег4", "тег5", "тег6"]
}}

Убедись, что новость звучит АБСОЛЮТНО РЕАЛИСТИЧНО, АКТУАЛЬНО и ПОЛЕЗНО! Текст должен быть ОБЪЕМНЫМ и ИНФОРМАТИВНЫМ (целевая длина {target_length} символов)!
"""
    return prompt, topic

def generate_news_with_model(model_name, prompt, retry_count=0):
    """Генерирует новость с указанной моделью"""
    try:
        print(f"   🧠 Пробуем модель: {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        text = response.text
        # Очистка от markdown
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Находим JSON
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx:end_idx+1]
        
        article = json.loads(text)
        
        # Валидация
        required_fields = ['title', 'summary', 'content', 'source', 'tags']
        if all(field in article for field in required_fields):
            # Проверяем длину текста
            content_length = len(article.get('content', ''))
            print(f"   ✅ УСПЕШНО! Длина текста: {content_length} символов")
            if content_length < 500:
                print(f"   ⚠️ Текст коротковат ({content_length} символов), но сохраняем")
            return article
        else:
            print(f"   ⚠️ Не все поля заполнены")
            return None
            
    except json.JSONDecodeError as e:
        print(f"   ❌ Ошибка парсинга JSON: {e}")
        if retry_count < MAX_RETRIES:
            print(f"   🔄 Повторная попытка ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(5)
            return generate_news_with_model(model_name, prompt, retry_count + 1)
        return None
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            print(f"   ⏳ Превышен лимит, ждём 30 сек...")
            time.sleep(30)
            if retry_count < MAX_RETRIES:
                return generate_news_with_model(model_name, prompt, retry_count + 1)
        elif "404" in error_msg:
            print(f"   ❌ Модель {model_name} не найдена")
        else:
            print(f"   ❌ Ошибка: {error_msg[:100]}")
        return None

def generate_news():
    """Генерирует новость, перебирая все модели из списка"""
    available_models = get_available_models()
    
    if not available_models:
        print("❌ Нет доступных моделей")
        return None
    
    print(f"\n🔄 Начинаем перебор {len(available_models)} моделей...")
    print("=" * 60)
    
    for attempt in range(3):
        print(f"\n🎯 Попытка {attempt + 1}/3 - выбор темы...")
        
        topic = random.choice(SEO_TOPICS)
        prompt, selected_topic = get_seo_prompt(topic)
        print(f"📌 Тема: {selected_topic.upper()}")
        
        for i, model_name in enumerate(available_models, 1):
            print(f"\n[{i}/{len(available_models)}] Тестируем модель {model_name}...")
            
            article = generate_news_with_model(model_name, prompt)
            
            if article:
                article['seo_topic'] = selected_topic
                article['used_model'] = model_name
                article['generation_time'] = datetime.now().isoformat()
                print(f"\n🎉 Успех! Новость сгенерирована моделью {model_name}")
                print(f"📰 Тема: {selected_topic}")
                print(f"📏 Длина текста: {len(article.get('content', ''))} символов")
                return article
            
            if i < len(available_models):
                wait_time = random.randint(3, 7)
                print(f"   ⏳ Ждём {wait_time} сек перед следующей моделью...")
                time.sleep(wait_time)
        
        if attempt < 2:
            print(f"\n⏰ Пауза 20 сек перед сменой темы...")
            time.sleep(20)
    
    print("\n❌ Не удалось сгенерировать новость ни одной моделью")
    return None

def generate_image_url(title, tags):
    """Генерирует изображение под тему новости"""
    import hashlib
    
    title_lower = title.lower()
    tags_lower = [t.lower() for t in tags]
    
    theme = 'default'
    for key, config in IMAGE_THEMES.items():
        if key in title_lower or any(key in tag for tag in tags_lower):
            theme = key
            break
    
    config = IMAGE_THEMES[theme]
    seed = hashlib.md5(f"{title}{datetime.now().strftime('%Y%m%d')}".encode()).hexdigest()[:10]
    
    return f"https://api.dicebear.com/7.x/{config['style']}/svg?seed={seed}&backgroundColor={config['color']}&radius=50"

def generate_seo_metadata(article):
    """Генерирует SEO-метаданные"""
    return {
        "meta_title": f"{article['title']} | Cognify AI News",
        "meta_description": article['summary'][:160],
        "meta_keywords": ", ".join(article.get('tags', []) + [article.get('seo_topic', 'news')]),
        "og_title": article['title'],
        "og_description": article['summary'][:200],
        "twitter_card": "summary_large_image"
    }

def generate_news_html(article):
    """Генерирует отдельную HTML-страницу для новости"""
    os.makedirs('news', exist_ok=True)
    
    # Обработка контента (перенос строк в HTML)
    content_html = article.get('content', '').replace('\n', '<br>')
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article.get('title', 'Новость')} | Cognify AI News</title>
    <meta name="description" content="{article.get('summary', '')[:160]}">
    <meta name="keywords" content="{', '.join(article.get('tags', []))}">
    
    <meta property="og:title" content="{article.get('title', '')}">
    <meta property="og:description" content="{article.get('summary', '')[:200]}">
    <meta property="og:image" content="{article.get('image_url', '')}">
    <meta property="og:url" content="https://cognify-ui.github.io/news/{article.get('id', '')}.html">
    <meta property="og:type" content="article">
    
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{article.get('title', '')}">
    <meta name="twitter:description" content="{article.get('summary', '')[:200]}">
    <meta name="twitter:image" content="{article.get('image_url', '')}">
    
    <link rel="canonical" href="https://cognify-ui.github.io/news/{article.get('id', '')}.html">
    <link rel="icon" type="image/png" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>">
    
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
            background: #f0f0f0;
        }}
        .article-content {{ padding: 40px; }}
        h1 {{ font-size: 32px; color: #1a1a2e; margin-bottom: 20px; line-height: 1.3; }}
        .meta {{
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
            flex-wrap: wrap;
        }}
        .content {{ font-size: 18px; line-height: 1.8; color: #333; margin-bottom: 30px; }}
        .content p {{ margin-bottom: 20px; }}
        .tags {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 30px 0;
        }}
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
            font-weight: 500;
        }}
        .back-link:hover {{ text-decoration: underline; }}
        @media (max-width: 768px) {{
            .article-content {{ padding: 20px; }}
            h1 {{ font-size: 24px; }}
            .article-image {{ height: 250px; }}
            .content {{ font-size: 16px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {f'<img class="article-image" src="{article.get("image_url", "")}" alt="{article.get("title", "")}">' if article.get('image_url') else ''}
        <div class="article-content">
            <h1>{article.get('title', '')}</h1>
            <div class="meta">
                <span>📅 {article.get('published_at', '').split('T')[0] if article.get('published_at') else 'Дата неизвестна'}</span>
                <span>🔗 {article.get('source', 'Cognify AI')}</span>
                <span>📖 {len(article.get('content', ''))} символов</span>
            </div>
            <div class="content">
                {content_html}
            </div>
            <div class="tags">
                {''.join([f'<a href="/?tag={tag}" class="tag">#{tag}</a>' for tag in article.get('tags', [])[:5]])}
            </div>
            <a href="/" class="back-link">← Назад к новостям</a>
        </div>
    </div>
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": "{article.get('title', '').replace('"', '\\"')}",
        "description": "{article.get('summary', '').replace('"', '\\"')[:200]}",
        "datePublished": "{article.get('published_at', '')}",
        "author": {{ "@type": "Organization", "name": "Cognify AI" }},
        "publisher": {{ "@type": "Organization", "name": "Cognify AI" }}
    }}
    </script>
</body>
</html>'''
    
    html_path = f"news/{article['id']}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"   ✅ Создана страница: {html_path}")
    return html_path

def generate_sitemap():
    """Генерирует sitemap.xml для всех страниц"""
    existing = {"articles": []}
    
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    articles = existing.get('articles', [])
    today = datetime.now().strftime("%Y-%m-%d")
    
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Главная страница
    sitemap += f'''  <url>
    <loc>https://cognify-ui.github.io/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
'''
    
    # Страницы новостей
    for article in articles:
        pub_date = article.get('published_at', today)[:10]
        sitemap += f'''  <url>
    <loc>https://cognify-ui.github.io/news/{article['id']}.html</loc>
    <lastmod>{pub_date}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
'''
    
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

def generate_all_news_pages():
    """Генерирует HTML страницы для всех существующих новостей"""
    if not os.path.exists(NEWS_FILE):
        print("❌ news.json не найден")
        return
    
    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    print(f"\n📄 Генерация HTML страниц для {len(articles)} новостей...")
    
    for article in articles:
        generate_news_html(article)
    
    generate_sitemap()
    generate_robots_txt()
    print(f"✅ Создано {len(articles)} HTML страниц")

def save_news_article(article):
    """Сохраняет новость и генерирует HTML страницу"""
    existing = {"last_updated": "", "articles": []}
    
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                print(f"\n📖 Загружено {len(existing.get('articles', []))} новостей")
        except Exception as e:
            print(f"⚠️ Ошибка чтения: {e}")
    
    # Создаём ID
    article_id = hashlib.md5(f"{article['title']}{datetime.now()}".encode()).hexdigest()[:12]
    
    # Генерируем изображение
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
        "seo_metadata": generate_seo_metadata(article)
    }
    
    # Проверка на дубликат
    existing_titles = [a.get('title') for a in existing.get('articles', [])]
    if new_article['title'] in existing_titles:
        print("⚠️ Такая новость уже существует, пропускаем...")
        return False
    
    # Добавляем в начало
    existing['articles'].insert(0, new_article)
    existing['articles'] = existing['articles'][:MAX_ARTICLES]
    existing['last_updated'] = datetime.now().isoformat()
    existing['total_articles'] = len(existing['articles'])
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    # Генерируем HTML страницу для новой новости
    generate_news_html(new_article)
    
    # Обновляем sitemap и robots.txt
    generate_sitemap()
    generate_robots_txt()
    
    print(f"\n✅ Сохранено. Всего новостей: {len(existing['articles'])}")
    print(f"🖼️  Изображение: {image_url[:80]}...")
    print(f"🤖 Модель: {article.get('used_model', 'unknown')}")
    print(f"📏 Длина текста: {len(article.get('content', ''))} символов")
    return True

def create_seo_demo_news():
    """Создаёт демо-новость"""
    demo_article = {
        "title": "Cognify AI: Бесплатный доступ к 4 мощным AI моделям для всех пользователей",
        "summary": "Откройте мир искусственного интеллекта бесплатно! Cognify AI предоставляет доступ к Groq, Cerebras, Cloudflare AI и Google Gemini без ограничений. Присоединяйтесь к тысячам пользователей уже сегодня.",
        "content": """Cognify AI — это инновационная платформа, объединяющая 4 передовые AI модели в одном месте. Пользователи могут общаться с Groq (молниеносная скорость), Cerebras (рекордная производительность), Cloudflare AI (глобальная доступность) и Google Gemini (передовые возможности) абсолютно бесплатно.

Сервис предлагает историю чатов, систему аккаунтов, экспорт диалогов и интуитивный интерфейс. По словам основателя проекта, 'Cognify AI создан для демократизации доступа к современным AI технологиям'.

Присоединяйтесь к сообществу, которое уже использует Cognify AI для работы, учёбы и творчества! Платформа постоянно обновляется, добавляются новые функции и модели.

Особенности сервиса:
- 4 AI модели в одном месте
- Полностью бесплатно, без лимитов
- Сохранение истории чатов
- Система аккаунтов
- Экспорт диалогов
- Мобильная адаптация

Cognify AI — ваш личный помощник в мире искусственного интеллекта!""",
        "source": "Cognify AI Official",
        "tags": ["cognify", "бесплатный ai", "groq", "cerebras", "cloudflare", "google gemini", "нейросети"],
        "seo_topic": "free ai",
        "used_model": "demo"
    }
    print("📝 Создаём SEO-демо новость...")
    return save_news_article(demo_article)

def main():
    print("=" * 60)
    print(f"🚀 ЗАПУСК ГЕНЕРАТОРА НОВОСТЕЙ")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Моделей в очереди: {len(FIXED_MODELS)}")
    print(f"🎨 Всего тем: {len(SEO_TOPICS)}")
    print(f"📏 Длина текста: 1500-10000 символов")
    print("=" * 60)
    
    # Генерируем новость
    article = generate_news()
    
    if article:
        success = save_news_article(article)
        if success:
            print("\n" + "=" * 60)
            print("📰 СГЕНЕРИРОВАННАЯ НОВОСТЬ:")
            print(f"   📌 Заголовок: {article.get('title')}")
            print(f"   📰 Источник: {article.get('source')}")
            print(f"   🏷️  Тема: {article.get('seo_topic')}")
            print(f"   🤖 Модель: {article.get('used_model')}")
            print(f"   🔖 Теги: {', '.join(article.get('tags', []))}")
            print(f"   📏 Длина текста: {len(article.get('content', ''))} символов")
            print("=" * 60)
        else:
            print("⚠️ Новость не сохранена (дубликат)")
    else:
        print("\n❌ Не удалось сгенерировать новость через API")
        
        # Создаём демо-новость если файла нет или он пустой
        if not os.path.exists(NEWS_FILE) or os.path.getsize(NEWS_FILE) < 100:
            create_seo_demo_news()
        else:
            # Пробуем сгенерировать HTML для существующих новостей
            generate_all_news_pages()
            print("📁 Обновлены HTML страницы существующих новостей")
    
    print("\n" + "=" * 60)
    print("✅ РАБОТА ЗАВЕРШЕНА!")
    print("=" * 60)

if __name__ == "__main__":
    main()
