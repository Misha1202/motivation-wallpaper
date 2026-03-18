"""
Сервис для генерации мотивационных обоев для телефона
Оптимизировано для Render (512 MB RAM)
Трехуровневая система получения цитат:
1. DeepSeek API (если есть ключ)
2. Бесплатные библейские API (justbible.ru, azbyka.ru, bible-api.com)
3. Запасной список (50+ цитат)
"""

import os
import io
import requests
import random
import time
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

# Размеры для iPhone 12 Pro
MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532

# Качество изображения
JPEG_QUALITY = 85
RESAMPLE_FILTER = Image.Resampling.BILINEAR

# Кэш для цитат
quote_cache = {
    "quote": "",
    "timestamp": 0
}
CACHE_DURATION = 3600  # 1 час

# ============================================
# РАСШИРЕННЫЙ СПИСОК ЗАПАСНЫХ ЦИТАТ (50+)
# ============================================
FALLBACK_QUOTES = [
    # Евангельские цитаты
    "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)",
    "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Блаженны милостивые, ибо они помилованы будут\n(Матфея 5:7)",
    "Господь — Пастырь мой; я ни в чем не буду нуждаться\n(Псалом 22:1)",
    "Все могу в укрепляющем меня Иисусе Христе\n(Филиппийцам 4:13)",
    "Не бойся, только веруй\n(Марка 5:36)",
    "Бог есть любовь\n(1 Иоанна 4:8)",
    "Свет во тьме светит\n(Иоанна 1:5)",
    "Просите, и дано будет вам\n(Матфея 7:7)",
    "Блаженны чистые сердцем\n(Матфея 5:8)",
    "Вера без дел мертва\n(Иакова 2:26)",
    "Идите за Мной\n(Матфея 4:19)",
    "Мир оставляю вам\n(Иоанна 14:27)",
    "Радость моя в вас пребудет\n(Иоанна 15:11)",
    "Придите ко Мне все труждающиеся\n(Матфея 11:28)",
    "Я свет миру\n(Иоанна 8:12)",
    "Я есмь путь и истина и жизнь\n(Иоанна 14:6)",
    "Блаженны слышащие слово Божие\n(Луки 11:28)",
    "Не собирайте сокровищ на земле\n(Матфея 6:19)",
    "Прощайте, и прощены будете\n(Луки 6:37)",
    
    # Псалмы
    "Милость и истина сретятся\n(Псалом 84:11)",
    "Бог нам прибежище и сила\n(Псалом 45:2)",
    "Сей день сотворил Господь\n(Псалом 117:24)",
    "На Тебя уповал я от утробы\n(Псалом 70:6)",
    "Господь просвещение мое\n(Псалом 26:1)",
    
    # Притчи
    "Надейся на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Господь дает мудрость\n(Притчи 2:6)",
    "Доброе имя лучше большого богатства\n(Притчи 22:1)",
    
    # Пророки
    "Я Господь, Бог твой, держу тебя за правую руку\n(Исаия 41:13)",
    "Вот Я с вами во все дни\n(Матфея 28:20)",
    "Мужайтесь, и да укрепляется сердце ваше\n(Псалом 30:25)",
    "Будьте тверды, непоколебимы\n(1 Коринфянам 15:58)",
    "Все испытывайте, хорошего держитесь\n(1 Фессалоникийцам 5:21)",
    
    # Мотивационные
    "Верь в себя и свои мечты\n(Народная мудрость)",
    "Каждый день - новая возможность\n(Народная мудрость)",
    "Ты сильнее, чем думаешь\n(Народная мудрость)",
    "Никогда не сдавайся\n(Народная мудрость)",
    "Всё будет хорошо\n(Народная мудрость)",
    "Делай сегодня лучше, чем вчера\n(Народная мудрость)",
    "Счастье в простых вещах\n(Народная мудрость)",
    "Мечты сбываются\n(Народная мудрость)",
    "Будь благодарен за каждый день\n(Народная мудрость)"
]

# ============================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ЦИТАТ ИЗ РАЗНЫХ ИСТОЧНИКОВ
# ============================================

def get_quote_from_deepseek():
    """Уровень 1: Получение цитаты от DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    is_biblical = random.random() < 0.8
    
    if is_biblical:
        prompt_text = """Сгенерируй вдохновляющую библейскую цитату для обоев на телефон.
Формат: сама цитата, затем с новой строки (Книга глава:стих)
Цитата должна быть на русском языке, красивая, вдохновляющая.
Примеры:
Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного
(Иоанна 3:16)

Уповай на Господа всем сердцем твоим
(Притчи 3:5)

Господь — Пастырь мой; я ни в чем не буду нуждаться
(Псалом 22:1)"""
    else:
        prompt_text = """Сгенерируй короткую мощную мотивационную цитату для обоев на телефон.
Формат: сама цитата, затем с новой строки (Автор)
Цитата должна быть на русском языке, вдохновляющей.
Примеры:
Верь в себя и свои мечты
(Народная мудрость)

Каждый день — новая возможность
(Народная мудрость)"""
    
    prompt = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты генератор красивых цитат. Отвечай ТОЛЬКО текстом цитаты, без пояснений, без кавычек."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.9,
        "max_tokens": 150
    }
    
    try:
        print("Запрашиваем цитату у DeepSeek...")
        response = requests.post(
            DEEPSEEK_API_URL, 
            headers=headers, 
            json=prompt, 
            timeout=10
        )
        
        if response.status_code == 402:
            print("DeepSeek: Требуется оплата")
            return None
            
        response.raise_for_status()
        
        data = response.json()
        quote = data["choices"][0]["message"]["content"].strip()
        quote = quote.strip('"').strip('„').strip('“')
        
        print(f"DeepSeek успешно: {quote[:50]}...")
        return quote
        
    except Exception as e:
        print(f"Ошибка DeepSeek API: {e}")
        return None


def get_quote_from_justbible():
    """Уровень 2: Получение случайного стиха с justbible.ru"""
    try:
        url = "https://justbible.ru/api/rnd?translation=rst&type=object"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            text = data.get("text", "").strip()
            reference = data.get("reference", "").strip()
            
            if text and reference:
                # Очищаем текст от лишних пробелов
                text = ' '.join(text.split())
                quote = f"{text}\n({reference})"
                print(f"justbible.ru успешно: {reference}")
                return quote
    except Exception as e:
        print(f"justbible.ru error: {e}")
    
    return None


def get_quote_from_azbyka():
    """Уровень 3: Получение цитаты дня с azbyka.ru"""
    try:
        url = "https://azbyka.ru/wp-json/az/v1/bquote-of-day"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quote_text = data.get("quote", "")
            
            if quote_text:
                # Убираем HTML теги
                import re
                quote_text = re.sub(r'<[^>]+>', '', quote_text)
                quote_text = quote_text.strip()
                
                print(f"azbyka.ru успешно: {quote_text[:50]}...")
                return quote_text
    except Exception as e:
        print(f"azbyka.ru error: {e}")
    
    return None


def get_quote_from_bible_api():
    """Уровень 4: Получение стиха с bible-api.com"""
    try:
        books = ["Иоанна", "Матфея", "Псалтирь", "Притчи", "Римлянам", "Коринфянам"]
        book = random.choice(books)
        
        if book == "Псалтирь":
            chapter = random.randint(1, 50)
            verse = random.randint(1, 10)
        else:
            chapter = random.randint(1, 15)
            verse = random.randint(1, 10)
        
        url = f"https://bible-api.com/{book}%20{chapter}:{verse}?translation=rst"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            verses = data.get("verses", [])
            if verses:
                text = verses[0].get("text", "").strip()
                book_name = data.get("reference", "").split()[0]
                quote = f"{text}\n({book_name} {chapter}:{verse})"
                print(f"bible-api.com успешно: {book} {chapter}:{verse}")
                return quote
    except Exception as e:
        print(f"bible-api.com error: {e}")
    
    return None


def get_biblical_quote():
    """
    УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ПОЛУЧЕНИЯ ЦИТАТ
    Пытается получить цитату из разных источников по порядку
    """
    global quote_cache
    
    # Проверяем кэш
    current_time = time.time()
    if quote_cache["quote"] and (current_time - quote_cache["timestamp"] < CACHE_DURATION):
        print(f"Возвращаем из кэша")
        return quote_cache["quote"]
    
    quote = None
    
    # Уровень 1: DeepSeek (если есть ключ)
    if DEEPSEEK_API_KEY:
        quote = get_quote_from_deepseek()
        if quote:
            quote_cache["quote"] = quote
            quote_cache["timestamp"] = current_time
            return quote
    
    # Уровень 2: justbible.ru (самый надежный русский источник)
    quote = get_quote_from_justbible()
    if quote:
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        return quote
    
    # Уровень 3: azbyka.ru
    quote = get_quote_from_azbyka()
    if quote:
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        return quote
    
    # Уровень 4: bible-api.com
    quote = get_quote_from_bible_api()
    if quote:
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        return quote
    
    # Уровень 5: Запасной список
    print("Используем запасной список")
    quote = random.choice(FALLBACK_QUOTES)
    quote_cache["quote"] = quote
    quote_cache["timestamp"] = current_time
    return quote


# ============================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ИЗОБРАЖЕНИЙ
# ============================================

def get_unsplash_image(keyword=None):
    """Получает изображение с Unsplash API"""
    if not keyword:
        keywords = ["nature", "mountain", "ocean", "forest", "sky", "spiritual", "peaceful", "light", "clouds"]
        keyword = random.choice(keywords)
    
    if not UNSPLASH_ACCESS_KEY:
        return None
    
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {
        "query": keyword,
        "orientation": "portrait",
        "count": 1,
        "content_filter": "high"
    }
    
    try:
        response = requests.get(UNSPLASH_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            img_url = data[0]["urls"]["regular"]
            
            img_response = requests.get(img_url, timeout=15)
            img_response.raise_for_status()
            
            img_bytes = io.BytesIO(img_response.content)
            background = Image.open(img_bytes)
            
            background = background.resize(
                (MOBILE_WIDTH, MOBILE_HEIGHT), 
                RESAMPLE_FILTER
            )
            
            if background.mode != 'RGB':
                background = background.convert('RGB')
            
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.8)
            
            return background
            
    except Exception as e:
        print(f"Ошибка Unsplash: {e}")
    
    return None


def create_gradient_background():
    """Создает красивый градиентный фон"""
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    color_schemes = [
        ((180, 150, 100), (100, 80, 150)),  # золотой-фиолетовый
        ((200, 180, 150), (80, 100, 180)),   # песочный-синий
        ((140, 170, 200), (70, 70, 120)),    # небесный-синий
        ((160, 120, 100), (120, 80, 150)),   # терракотовый-пурпурный
    ]
    
    color1, color2 = random.choice(color_schemes)
    
    for y in range(0, MOBILE_HEIGHT, 5):
        ratio = y / MOBILE_HEIGHT
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        
        for i in range(5):
            if y + i < MOBILE_HEIGHT:
                draw.line([(0, y + i), (MOBILE_WIDTH, y + i)], fill=(r, g, b))
    
    return img


def get_background_image():
    """Универсальная функция получения фона"""
    # Пробуем Unsplash
    if UNSPLASH_ACCESS_KEY:
        img = get_unsplash_image()
        if img:
            return img
    
    # Если не сработало - градиент
    print("Используем градиентный фон")
    return create_gradient_background()


# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ТЕКСТОМ
# ============================================

def wrap_text(text, font, max_width, draw):
    """Разбивает текст на строки по ширине"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def add_text_to_image(image, text):
    """Накладывает текст на изображение"""
    img_with_text = image.copy()
    draw = ImageDraw.Draw(img_with_text)
    
    # Загружаем шрифт
    try:
        font = ImageFont.load_default()
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
            "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 90)
                break
    except:
        font = ImageFont.load_default()
    
    # Параметры текста
    max_width = MOBILE_WIDTH - 160
    target_y = int(MOBILE_HEIGHT * 0.65)  # 65% от верха (ниже центра)
    
    # Разбиваем текст
    lines = wrap_text(text, font, max_width, draw)
    
    # Вычисляем высоту текста
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h + 10
    total_height -= 10
    
    # Позиция начала
    start_y = target_y - total_height // 2
    padding = 40
    
    # Максимальная ширина строки
    max_line_width = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        max_line_width = max(max_line_width, bbox[2] - bbox[0])
    
    # Координаты подложки
    left = (MOBILE_WIDTH - max_line_width) // 2 - padding
    right = (MOBILE_WIDTH + max_line_width) // 2 + padding
    top = start_y - padding
    bottom = start_y + total_height + padding
    
    # Создаем полупрозрачную подложку
    overlay = Image.new('RGBA', (right-left, bottom-top), (0, 0, 0, 180))
    img_with_text = img_with_text.convert('RGBA')
    img_with_text.paste(overlay, (left, top), overlay)
    
    # Рисуем текст
    draw = ImageDraw.Draw(img_with_text)
    current_y = start_y
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (MOBILE_WIDTH - (bbox[2] - bbox[0])) // 2
        
        # Тень
        draw.text((x + 2, current_y + 2), line, font=font, fill=(0, 0, 0, 150))
        # Основной текст
        draw.text((x, current_y), line, font=font, fill=(255, 255, 255))
        
        current_y += line_heights[i] + 10
    
    return img_with_text.convert('RGB')


# ============================================
# ЭНДПОИНТЫ FASTAPI
# ============================================

@app.get("/")
@app.get("/wallpaper")
async def generate_wallpaper():
    """Генерирует обои"""
    try:
        # Получаем цитату
        quote = get_biblical_quote()
        print(f"Итоговая цитата: {quote[:100]}...")
        
        # Получаем фон
        background = get_background_image()
        
        # Добавляем текст
        final_image = add_text_to_image(background, quote)
        
        # Сохраняем
        img_byte_arr = io.BytesIO()
        final_image.save(
            img_byte_arr, 
            format='JPEG', 
            quality=JPEG_QUALITY, 
            optimize=True
        )
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        # Абсолютный запасной вариант
        img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT), (100, 80, 150))
        img = add_text_to_image(img, random.choice(FALLBACK_QUOTES))
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "ok", 
        "time": time.time(),
        "deepseek_key": bool(DEEPSEEK_API_KEY),
        "unsplash_key": bool(UNSPLASH_ACCESS_KEY)
    }


@app.get("/test")
async def test_api():
    """Тестирование всех API источников"""
    results = {}
    
    # Тест DeepSeek
    if DEEPSEEK_API_KEY:
        results["deepseek"] = bool(get_quote_from_deepseek())
    
    # Тест justbible
    results["justbible"] = bool(get_quote_from_justbible())
    
    # Тест azbyka
    results["azbyka"] = bool(get_quote_from_azbyka())
    
    # Тест bible-api
    results["bible_api"] = bool(get_quote_from_bible_api())
    
    return results


# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
