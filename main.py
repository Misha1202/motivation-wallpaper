"""
Сервис для генерации мотивационных обоев для телефона
Оптимизировано для Render (512 MB RAM)
Использует Unsplash API для фоновых изображений
"""

import os
import io
import requests
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from functools import lru_cache

# Конфигурация
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

# URL API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

# Создаем FastAPI приложение
app = FastAPI()

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Размеры для iPhone 12 Pro
MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532

# Уменьшенное качество для экономии памяти
JPEG_QUALITY = 85
RESAMPLE_FILTER = Image.Resampling.BILINEAR  # менее требовательный чем LANCZOS

# Кэш для цитат (чтобы реже дергать DeepSeek)
quote_cache = {
    "quote": "",
    "timestamp": 0
}
CACHE_DURATION = 3600  # 1 час

# Запасные цитаты
FALLBACK_QUOTES = [
    "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)",
    "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Блаженны милостивые, ибо они помилованы будут\n(Матфея 5:7)",
    "Господь — Пастырь мой; я ни в чем не буду нуждаться\n(Псалом 22:1)",
    "Все могу в укрепляющем меня Иисусе Христе\n(Филиппийцам 4:13)",
    "Не бойся, только веруй\n(Марка 5:36)",
    "Верь в себя и свои мечты",
    "Каждый день - новое начало"
]

@lru_cache(maxsize=1)
def get_cached_quote():
    """Кэширование запасных цитат"""
    return random.choice(FALLBACK_QUOTES)

def get_biblical_quote():
    """
    Получает библейскую цитату от DeepSeek API с кэшированием
    """
    global quote_cache
    
    current_time = time.time()
    if quote_cache["quote"] and (current_time - quote_cache["timestamp"] < CACHE_DURATION):
        return quote_cache["quote"]
    
    if not DEEPSEEK_API_KEY:
        return get_cached_quote()
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    is_biblical = random.random() < 0.8
    
    if is_biblical:
        prompt_text = """Сгенерируй библейскую цитату для обоев. Формат: цитата, потом с новой строки (Источник). Коротко, 3-5 строк."""
    else:
        prompt_text = """Сгенерируй мотивационную цитату для обоев. Формат: цитата, потом с новой строки (Автор). Коротко, 3-5 строк."""
    
    prompt = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты генератор цитат. Отвечай только цитатой."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.9,
        "max_tokens": 100  # Уменьшено для экономии
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=prompt, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        quote = data["choices"][0]["message"]["content"].strip()
        quote = quote.strip('"').strip('„').strip('“')
        
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        
        return quote
        
    except Exception as e:
        print(f"Ошибка DeepSeek API: {e}")
        return get_cached_quote()

def get_unsplash_image(keyword=None):
    """
    Получает изображение с Unsplash API (оптимизировано)
    """
    if not keyword:
        keywords = ["nature", "mountain", "ocean", "forest", "sky", "spiritual"]
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
        
        if data and len(data) > 0:
            # Используем regular размер (меньше чем raw/original)
            img_url = data[0]["urls"]["regular"]
            
            # Скачиваем с таймаутом
            img_response = requests.get(img_url, timeout=15)
            img_response.raise_for_status()
            
            # Открываем изображение
            img_bytes = io.BytesIO(img_response.content)
            background = Image.open(img_bytes)
            
            # Быстрое изменение размера
            background = background.resize(
                (MOBILE_WIDTH, MOBILE_HEIGHT), 
                RESAMPLE_FILTER
            )
            
            # Конвертируем в RGB если нужно
            if background.mode != 'RGB':
                background = background.convert('RGB')
            
            # Легкое затемнение
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.8)
            
            return background
            
    except Exception as e:
        print(f"Ошибка Unsplash: {e}")
    
    return None

def create_gradient_background():
    """
    Создает простой градиент (быстро и экономично)
    """
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Простая цветовая схема
    color1 = (180, 150, 100)  # золотой
    color2 = (100, 80, 150)   # фиолетовый
    
    # Упрощенный градиент (каждая 10-я строка для скорости)
    for y in range(0, MOBILE_HEIGHT, 10):
        ratio = y / MOBILE_HEIGHT
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        
        # Рисуем полосу высотой 10 пикселей
        for i in range(10):
            if y + i < MOBILE_HEIGHT:
                draw.line([(0, y + i), (MOBILE_WIDTH, y + i)], fill=(r, g, b))
    
    return img

def wrap_text(text, font, max_width, draw):
    """
    Разбивает текст на строки (оптимизировано)
    """
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
    """
    Накладывает текст (оптимизированная версия)
    """
    # Работаем напрямую с RGB для экономии памяти
    img_with_text = image.copy()
    draw = ImageDraw.Draw(img_with_text)
    
    # Загружаем шрифт (один раз)
    try:
        font = ImageFont.load_default()
        # Пытаемся найти шрифт побольше
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
        ]
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 90)
                break
    except:
        font = ImageFont.load_default()
    
    # Параметры
    max_width = MOBILE_WIDTH - 160  # отступы
    target_y = int(MOBILE_HEIGHT * 0.65)  # ниже центра
    
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
    
    # Рисуем подложку (простой прямоугольник)
    padding = 40
    
    # Получаем максимальную ширину строки
    max_line_width = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        max_line_width = max(max_line_width, bbox[2] - bbox[0])
    
    # Координаты подложки
    left = (MOBILE_WIDTH - max_line_width) // 2 - padding
    right = (MOBILE_WIDTH + max_line_width) // 2 + padding
    top = start_y - padding
    bottom = start_y + total_height + padding
    
    # Рисуем черную подложку
    overlay = Image.new('RGBA', (right-left, bottom-top), (0, 0, 0, 180))
    img_with_text.paste(overlay, (left, top), overlay)
    
    # Создаем новый Draw объект после вставки
    draw = ImageDraw.Draw(img_with_text)
    
    # Рисуем текст
    current_y = start_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (MOBILE_WIDTH - (bbox[2] - bbox[0])) // 2
        
        # Текст
        draw.text((x, current_y), line, font=font, fill=(255, 255, 255))
        
        current_y += line_heights[i] + 10
    
    return img_with_text

@app.get("/")
@app.get("/wallpaper")
async def generate_wallpaper():
    """
    Генерирует обои (оптимизированная версия)
    """
    try:
        # Получаем цитату
        quote = get_biblical_quote()
        
        # Пытаемся получить фото с Unsplash
        background = get_unsplash_image()
        
        # Если не получилось - градиент
        if background is None:
            background = create_gradient_background()
        
        # Добавляем текст
        final_image = add_text_to_image(background, quote)
        
        # Сохраняем с оптимизацией
        img_byte_arr = io.BytesIO()
        final_image.save(
            img_byte_arr, 
            format='JPEG', 
            quality=JPEG_QUALITY, 
            optimize=True
        )
        img_byte_arr.seek(0)
        
        # Очищаем память
        del background
        del final_image
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        print(f"Ошибка: {e}")
        # Простейший запасной вариант
        img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT), (100, 80, 150))
        img = add_text_to_image(img, get_cached_quote())
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")

@app.get("/health")
async def health_check():
    return {"status": "ok", "time": time.time()}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
