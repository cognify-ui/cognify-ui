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

# SEO-оптимизированные темы для новостей
SEO_TOPICS = [
    "chatgpt", "openai", "google gemini", "microsoft copilot", "claude ai",
    "midjourney", "stable diffusion", "dall-e", "ai art", "neural networks",
    "deep learning", "machine learning", "data science", "nvidia", "amd",
    "ai startup", "ai investment", "ai funding", "ai regulation", "ai safety",
    "china ai", "us ai", "europe ai", "ai ethics", "artificial intelligence",
    "generative ai", "llm", "large language model", "ai agents", "agi",
    "ai chip", "gpu", "ai hardware", "quantum ai", "edge ai", "cloud ai",
    "ai healthcare", "ai medicine", "ai finance", "ai education", "ai robot",
    "self-driving", "autonomous", "computer vision", "nlp", "speech recognition"
]

# Конфигурация изображений по темам
IMAGE_THEMES = {
    'chatgpt': {'style': 'bottts', 'color': '10a37f', 'icon': 'chatgpt', 'keywords': 'chatgpt openai'},
    'openai': {'style': 'bottts', 'color': '10a37f', 'icon': 'openai', 'keywords': 'openai ai'},
    'google': {'style': 'identicon', 'color': '4285f4', 'icon': 'google', 'keywords': 'google ai'},
    'gemini': {'style': 'identicon', 'color': '8e6ced', 'icon': 'gemini', 'keywords': 'google gemini'},
    'microsoft': {'style': 'micah', 'color': '00a4ef', 'icon': 'microsoft', 'keywords': 'microsoft ai'},
    'copilot': {'style': 'micah', 'color': '00a4ef', 'icon': 'copilot', 'keywords': 'github copilot'},
    'claude': {'style': 'adventurer', 'color': 'd97757', 'icon': 'claude', 'keywords': 'anthropic claude'},
    'anthropic': {'style': 'adventurer', 'color': 'd97757', 'icon': 'anthropic', 'keywords': 'anthropic ai'},
    'meta': {'style': 'lorelei', 'color': '0064e1', 'icon': 'meta', 'keywords': 'meta llama'},
    'llama': {'style': 'lorelei', 'color': '0064e1', 'icon': 'llama', 'keywords': 'llama meta'},
    'midjourney': {'style': 'pixel-art', 'color': 'ff6b35', 'icon': 'midjourney', 'keywords': 'midjourney ai art'},
    'stable diffusion': {'style': 'pixel-art', 'color': 'ff6b35', 'icon': 'stable-diffusion', 'keywords': 'stability ai'},
    'dall-e': {'style': 'pixel-art', 'color': '10a37f', 'icon': 'dalle', 'keywords': 'dalle openai'},
    'ai art': {'style': 'pixel-art', 'color': 'ff6b35', 'icon': 'ai-art', 'keywords': 'ai art generation'},
    'nvidia': {'style': 'bottts', 'color': '76b900', 'icon': 'nvidia', 'keywords': 'nvidia gpu ai'},
    'amd': {'style': 'bottts', 'color': 'ed1c24', 'icon': 'amd', 'keywords': 'amd ai chip'},
    'intel': {'style': 'bottts', 'color': '0071c5', 'icon': 'intel', 'keywords': 'intel ai'},
    'startup': {'style': 'adventurer', 'color': 'f59e0b', 'icon': 'startup', 'keywords': 'ai startup'},
    'investment': {'style': 'adventurer', 'color': '10b981', 'icon': 'investment', 'keywords': 'ai funding'},
    'funding': {'style': 'adventurer', 'color': '10b981', 'icon': 'funding', 'keywords': 'ai investment'},
    'regulation': {'style': 'identicon', 'color': 'ef4444', 'icon': 'regulation', 'keywords': 'ai regulation'},
    'ai safety': {'style': 'identicon', 'color': 'ef4444', 'icon': 'safety', 'keywords': 'ai safety'},
    'ethics': {'style': 'identicon', 'color': 'ef4444', 'icon': 'ethics', 'keywords': 'ai ethics'},
    'china': {'style': 'lorelei', 'color': 'de2910', 'icon': 'china', 'keywords': 'china ai'},
    'us ai': {'style': 'lorelei', 'color': '002868', 'icon': 'usa', 'keywords': 'us ai policy'},
    'europe': {'style': 'lorelei', 'color': '003399', 'icon': 'europe', 'keywords': 'eu ai act'},
    'robot': {'style': 'bottts', 'color': '6b7280', 'icon': 'robot', 'keywords': 'ai robot'},
    'neural': {'style': 'identicon', 'color': '8b5cf6', 'icon': 'neural', 'keywords': 'neural network'},
    'deep learning': {'style': 'identicon', 'color': 'ec4899', 'icon': 'deep-learning', 'keywords': 'deep learning'},
    'machine learning': {'style': 'identicon', 'color': 'ec4899', 'icon': 'ml', 'keywords': 'machine learning'},
    'data science': {'style': 'micah', 'color': '3b82f6', 'icon': 'data-science', 'keywords': 'data science'},
    'healthcare': {'style': 'adventurer', 'color': '10b981', 'icon': 'healthcare', 'keywords': 'ai healthcare'},
    'finance': {'style': 'adventurer', 'color': 'f59e0b', 'icon': 'finance', 'keywords': 'ai finance'},
    'education': {'style': 'adventurer', 'color': '3b82f6', 'icon': 'education', 'keywords': 'ai education'},
    'autonomous': {'style': 'bottts', 'color': 'ef4444', 'icon': 'autonomous', 'keywords': 'self driving'},
    'quantum': {'style': 'identicon', 'color': '8b5cf6', 'icon': 'quantum', 'keywords': 'quantum ai'},
    'default': {'style': 'bottts', 'color': '6366f1', 'icon': 'ai', 'keywords': 'artificial intelligence'}
}

def get_available_models():
    """Получает список доступных моделей"""
    available = []
    print("\n📋 Проверка доступных моделей...")
    try:
        for model in client.models.list():
            if 'generateContent' in str(model.supported_methods):
                model_name = model.name.replace('models/', '')
                available.append(model_name)
                print(f"   ✅ {model_name}")
    except Exception as e:
        print(f"   ⚠️ Ошибка: {e}")
        available = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-lite-001",
        ]
        print(f"   📌 Используем стандартный список")
    
    return available

def get_seo_prompt(topic=None):
    """Генерирует SEO-оптимизированный промпт для новости"""
    if not topic:
        topic = random.choice(SEO_TOPICS)
    
    # Случайный источник для разнообразия
    sources = [
        "The Verge", "TechCrunch", "Wired", "VentureBeat", "Ars Technica",
        "MIT Technology Review", "IEEE Spectrum", "AI Magazine", "Analytics India",
        "ZDNet", "CNET", "Engadget", "The Information", "The Gradient"
    ]
    
    # Случайные SEO-ключевые слова
    seo_keywords = [
        "искусственный интеллект", "нейросети", "AI", "машинное обучение",
        "технологии будущего", "цифровая трансформация", "инновации"
    ]
    
    prompt = f"""
Ты — профессиональный журналист, специализирующийся на AI. Сгенерируй УНИКАЛЬНУЮ, ИНТЕРЕСНУЮ новость на тему: {topic}

ВАЖНЫЕ ТРЕБОВАНИЯ:
1. Дата публикации: сегодня или вчера
2. Источник: {random.choice(sources)}
3. Язык: русский (качественный, профессиональный)
4. Новость должна быть SEO-оптимизирована для поисковых систем
5. Используй естественные ключевые слова: {', '.join(random.sample(seo_keywords, 3))}

СТРУКТУРА НОВОСТИ:
- Заголовок: привлекательный, с ключевыми словами (максимум 90 символов)
- Краткое описание: 2-3 предложения, интригующее (максимум 300 символов)
- Полный текст: 4-6 предложений, раскрывающих детали (максимум 1200 символов)
- Теги: 4-5 релевантных тега (включая {topic} и 'AI')

ФОРМАТ ОТВЕТА - ТОЛЬКО JSON:
{{
    "title": "Заголовок новости",
    "summary": "Краткое описание",
    "content": "Полный текст новости с деталями и анализом",
    "source": "Название источника",
    "tags": ["тег1", "тег2", "тег3", "тег4", "тег5"]
}}

Убедись, что новость звучит АБСОЛЮТНО РЕАЛИСТИЧНО и АКТУАЛЬНО!
"""
    return prompt, topic

def generate_news_with_model(model_name, prompt, retry_count=0):
    """Генерирует новость с указанной моделью и повторными попытками"""
    try:
        print(f"   🧠 Пробуем модель: {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        text = response.text
        # Улучшенный парсинг JSON
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            # Пробуем найти полный JSON
            text = text[text.find('{'):text.rfind('}')+1]
        
        article = json.loads(text)
        
        # Валидация полей
        required_fields = ['title', 'summary', 'content', 'source', 'tags']
        if all(field in article for field in required_fields):
            print(f"   ✅ УСПЕШНО! Новость сгенерирована")
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
            print(f"   ❌ Модель не найдена")
        else:
            print(f"   ❌ Ошибка: {error_msg[:100]}")
        return None

def generate_news():
    """Генерирует SEO-оптимизированную новость"""
    available_models = get_available_models()
    
    if not available_models:
        print("❌ Нет доступных моделей")
        return None
    
    print(f"\n📊 Доступно моделей: {len(available_models)}")
    
    # Пробуем разные темы для лучшего SEO
    for attempt in range(3):
        print(f"\n🔄 Попытка {attempt + 1}/3 - генерация новости...")
        
        # Выбираем случайную тему для разнообразия
        topic = random.choice(SEO_TOPICS)
        prompt, selected_topic = get_seo_prompt(topic)
        print(f"📌 Тема: {selected_topic}")
        
        for i, model_name in enumerate(available_models, 1):
            print(f"\n[{i}/{len(available_models)}] Тестируем модель...")
            
            article = generate_news_with_model(model_name, prompt)
            
            if article:
                article['seo_topic'] = selected_topic
                article['seo_keywords'] = [selected_topic] + article.get('tags', [])[:3]
                print(f"\n🎉 Успешно! Тема: {selected_topic}")
                return article
            
            if i < len(available_models):
                wait_time = random.randint(5, 10)
                print(f"   ⏳ Ждём {wait_time} сек...")
                time.sleep(wait_time)
        
        if attempt < 2:
            print(f"\n⏰ Пауза 20 сек перед сменой темы...")
            time.sleep(20)
    
    print("\n❌ Не удалось сгенерировать новость")
    return None

def generate_image_url(title, tags):
    """Генерирует SEO-оптимизированное изображение под тему новости"""
    import hashlib
    
    # Определяем тему новости
    title_lower = title.lower()
    tags_lower = [t.lower() for t in tags]
    
    theme = 'default'
    for key, config in IMAGE_THEMES.items():
        if key in title_lower or any(key in tag for tag in tags_lower):
            theme = key
            break
    
    config = IMAGE_THEMES[theme]
    # Создаём уникальный seed на основе заголовка и тегов
    seed_text = f"{title}{''.join(tags[:3])}"
    seed = hashlib.md5(seed_text.encode()).hexdigest()[:10]
    
    # Генерируем URL с параметрами для SEO
    return f"https://api.dicebear.com/7.x/{config['style']}/svg?seed={seed}&backgroundColor={config['color']}&radius=50"

def generate_seo_metadata(article):
    """Генерирует SEO-метаданные для новости"""
    return {
        "meta_title": f"{article['title']} | Cognify AI News",
        "meta_description": article['summary'][:160],
        "meta_keywords": ", ".join(article.get('tags', []) + [article.get('seo_topic', 'ai')]),
        "og_title": article['title'],
        "og_description": article['summary'][:200],
        "twitter_card": "summary_large_image",
        "canonical_url": f"https://cognify-ui.github.io/news/{article['id']}"
    }

def save_news_article(article):
    """Сохраняет новость с SEO-метаданными"""
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
    article['id'] = article_id
    
    # Генерируем изображение
    image_url = generate_image_url(article['title'], article.get('tags', []))
    
    new_article = {
        "id": article_id,
        "title": article.get('title'),
        "summary": article.get('summary'),
        "content": article.get('content'),
        "source": article.get('source'),
        "source_url": f"https://cognify-ui.github.io/news/{article_id}",
        "published_at": datetime.now().isoformat(),
        "tags": article.get('tags', ['ai', 'news']),
        "seo_topic": article.get('seo_topic', 'ai'),
        "image_url": image_url,
        "seo_metadata": generate_seo_metadata(article)
    }
    
    # Добавляем в начало
    existing['articles'].insert(0, new_article)
    existing['articles'] = existing['articles'][:MAX_ARTICLES]
    existing['last_updated'] = datetime.now().isoformat()
    existing['total_articles'] = len(existing['articles'])
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Сохранено. Всего новостей: {len(existing['articles'])}")
    print(f"🖼️  Изображение: {image_url[:80]}...")
    return True

def create_seo_demo_news():
    """Создаёт SEO-оптимизированную демо-новость"""
    demo_article = {
        "title": "Cognify AI: Бесплатный доступ к 4 мощным AI моделям для всех пользователей",
        "summary": "Откройте мир искусственного интеллекта бесплатно! Cognify AI предоставляет доступ к Groq, Cerebras, Cloudflare и Gemini без ограничений.",
        "content": "Cognify AI — это инновационная платформа, объединяющая 4 передовые AI модели в одном месте. Пользователи могут общаться с Groq, Cerebras, Cloudflare AI и Google Gemini абсолютно бесплатно. Сервис предлагает историю чатов, систему аккаунтов и интуитивный интерфейс. Присоединяйтесь к тысячам пользователей, которые уже используют Cognify AI для работы, учёбы и творчества!",
        "source": "Cognify AI Official",
        "tags": ["cognify", "бесплатный ai", "groq", "cerebras", "cloudflare", "gemini", "нейросети"],
        "seo_topic": "free ai"
    }
    print("📝 Создаём SEO-демо новость...")
    save_news_article(demo_article)

def main():
    print("=" * 60)
    print(f"🚀 ЗАПУСК SEO-ГЕНЕРАТОРА НОВОСТЕЙ")
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Всего тем: {len(SEO_TOPICS)}")
    print("=" * 60)
    
    # Генерируем новость
    article = generate_news()
    
    if article:
        save_news_article(article)
        print("\n" + "=" * 60)
        print("📰 СГЕНЕРИРОВАННАЯ НОВОСТЬ:")
        print(f"   Заголовок: {article.get('title')}")
        print(f"   Источник: {article.get('source')}")
        print(f"   SEO тема: {article.get('seo_topic')}")
        print(f"   Теги: {', '.join(article.get('tags', []))}")
        print(f"   Кратко: {article.get('summary')[:120]}...")
    else:
        print("\n❌ Не удалось сгенерировать новость")
        
        # Создаём демо-новость если файла нет
        if not os.path.exists(NEWS_FILE) or os.path.getsize(NEWS_FILE) < 100:
            create_seo_demo_news()
    
    print("\n" + "=" * 60)
    print("✅ ГОТОВО! Новость добавлена в ленту")
    print("=" * 60)

if __name__ == "__main__":
    main()
