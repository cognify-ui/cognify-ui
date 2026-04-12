#!/usr/bin/env python3
import json
import os
import hashlib
import re
from datetime import datetime
from google import genai

NEWS_FILE = "news.json"
MAX_ARTICLES = 50

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ Ошибка: GEMINI_API_KEY не найден")
    exit(1)

print(f"✅ API ключ найден: {GEMINI_API_KEY[:10]}...")

client = genai.Client(api_key=GEMINI_API_KEY)

def list_available_models():
    """Выводит список доступных моделей (для отладки)"""
    print("📋 Доступные модели:")
    try:
        for model in client.models.list():
            if 'generateContent' in str(model.supported_methods):
                print(f"  - {model.name}")
    except Exception as e:
        print(f"  ⚠️ Не удалось получить список: {e}")

def generate_news():
    """Генерирует новость через Gemini"""
    prompt = """
Ты — журналист AI новостей. Сгенерируй ОДНУ свежую новость из мира искусственного интеллекта.

Требования:
1. Новость должна звучать как реальная
2. Дата: сегодня или вчера
3. Источник: The Verge, TechCrunch, Wired или VentureBeat
4. Язык: русский

Ответ должен быть строго в формате JSON:
{
    "title": "Заголовок новости (до 80 символов)",
    "summary": "Краткое описание (2-3 предложения, до 300 символов)",
    "content": "Полный текст новости (3-5 предложений, до 1000 символов)",
    "source": "Название источника",
    "tags": ["тег1", "тег2", "тег3"]
}
"""
    # Список моделей для проб (от самой новой к самой старой)
    models_to_try = [
        "gemini-1.5-flash-002",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-pro",
    ]
    
    for model_name in models_to_try:
        try:
            print(f"🧠 Пробуем модель: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            text = response.text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                article = json.loads(json_match.group())
                print(f"✅ Успешно! Модель: {model_name}")
                print(f"   Заголовок: {article.get('title', 'Без заголовка')[:50]}...")
                return article
            else:
                print(f"   ⚠️ Не найден JSON в ответе")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:100]}")
            continue
    
    print("❌ Все модели не сработали")
    return None

def generate_image_url(title):
    query = title.replace(' ', '+')[:50]
    return f"https://source.unsplash.com/800x400/?{query},ai,technology"

def save_news_article(article):
    existing = {"last_updated": "", "articles": []}
    
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                print(f"📖 Загружено {len(existing.get('articles', []))} существующих новостей")
        except:
            pass
    
    article_id = hashlib.md5(f"{article['title']}{datetime.now()}".encode()).hexdigest()[:12]
    
    new_article = {
        "id": article_id,
        "title": article.get('title', 'AI Новость'),
        "summary": article.get('summary', ''),
        "content": article.get('content', ''),
        "source": article.get('source', 'AI News'),
        "source_url": f"https://cognify-ui.github.io/news/{article_id}",
        "published_at": datetime.now().isoformat(),
        "tags": article.get('tags', ['ai', 'news']),
        "image_url": generate_image_url(article.get('title', 'ai'))
    }
    
    existing['articles'].insert(0, new_article)
    existing['articles'] = existing['articles'][:MAX_ARTICLES]
    existing['last_updated'] = datetime.now().isoformat()
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Сохранено. Всего новостей: {len(existing['articles'])}")
    return True

def main():
    print(f"🚀 Запуск генератора новостей Gemini: {datetime.now()}")
    print("-" * 50)
    
    # Раскомментируйте для отладки:
    # list_available_models()
    
    article = generate_news()
    
    if article:
        save_news_article(article)
        print(f"📰 Заголовок: {article.get('title', 'Без заголовка')}")
        print(f"📝 Кратко: {article.get('summary', '')[:100]}...")
    else:
        print("❌ Не удалось сгенерировать новость")
        
        if not os.path.exists(NEWS_FILE) or os.path.getsize(NEWS_FILE) < 100:
            print("📝 Создаём демо-новость...")
            demo_article = {
                "title": "Добро пожаловать в Cognify AI!",
                "summary": "Бесплатный доступ к 4 AI моделям: Groq, Cerebras, Cloudflare и Gemini",
                "content": "Cognify AI — это бесплатный сервис с 4 мощными AI моделями.",
                "source": "Cognify AI",
                "tags": ["cognify", "ai", "бесплатно"]
            }
            save_news_article(demo_article)
    
    print("✅ Готово!")

if __name__ == "__main__":
    main()
