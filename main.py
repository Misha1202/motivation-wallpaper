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
RESAMPLE_FILTER = Image.Resampling.BILINEAR

# Кэш для цитат
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
    "Бог есть любовь\n(1 Иоанна 4:8)",
    "Свет во тьме светит\n(Иоанна 1:5)",
    "Просите, и дано будет вам\n(Матфея 7:7)",
    "Блаженны чистые сердцем\n(Матфея 5:8)",
    "Вера без дел мертва\n(Иакова 2:26)",
    "Идите за Мной\n(Матфея 4:19)",
    "Мир оставляю вам\n(Иоанна 14:27)",
    "Радость моя в вас пребудет\n(Иоанна 15:11)"
]

def get_biblical_quote():
    """
    Получает библейскую цитату от DeepSeek API
    """
    global quote_cache
    
    current_time = time.time()
    if quote_cache["quote"] and (current_time - quote_cache["timestamp"] < CACHE_DURATION):
        print(f"Возвращаем из кэша: {quote_cache['quote']}")
        return quote_cache["quote"]
    
    # Если нет ключа API, возвращаем случайную цитату
    if not DEEPSEEK_API_KEY:
        quote = random.choice(FALLBACK_QUOTES)
        print(f"Нет API ключа, запасная: {quote}")
        return quote
    
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
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        quote = data["choices"][0]["message"]["content"].strip()
        quote = quote.strip('"').strip('„').strip('“')
        
        print(f"Получена цитата: {quote}")
        
        # Сохраняем в кэш
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        
        return quote
        
    except Exception as e:
        print(f"Ошибка DeepSeek API: {e}")
        # При ошибке возвращаем случайную цитату
        quote = random.choice(FALLBACK_QUOTES)
        print(f"Используем запасную: {quote}")
        return quote

def get_unsplash_image(keyword=None):
    """
    Получает изображение с Unsplash API
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
    """Создает простой градиент"""
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    color1 = (180, 150, 100)
    color2 = (100, 80, 150)
    
    for y in range(0, MOBILE_HEIGHT, 10):
        ratio = y / MOBILE_HEIGHT
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        
        for i in range(10):
            if y + i < MOBILE_HEIGHT:
                draw.line([(0, y + i), (MOBILE_WIDTH, y + i)], fill=(r, g, b))
    
    return img

def wrap_text(text, font, max_width, draw):
    """Разбивает текст на строки"""
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
    """Накладывает текст"""
    img_with_text = image.copy()
    draw = ImageDraw.Draw(img_with_text)
    
    try:
        font = ImageFont.load_default()
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
    
    max_width = MOBILE_WIDTH - 160
    target_y = int(MOBILE_HEIGHT * 0.65)
    
    lines = wrap_text(text, font, max_width, draw)
    
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h + 10
    total_height -= 10
    
    start_y = target_y - total_height // 2
    padding = 40
    
    max_line_width = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        max_line_width = max(max_line_width, bbox[2] - bbox[0])
    
    left = (MOBILE_WIDTH - max_line_width) // 2 - padding
    right = (MOBILE_WIDTH + max_line_width) // 2 + padding
    top = start_y - padding
    bottom = start_y + total_height + padding
    
    overlay = Image.new('RGBA', (right-left, bottom-top), (0, 0, 0, 180))
    img_with_text.paste(overlay, (left, top), overlay)
    
    draw = ImageDraw.Draw(img_with_text)
    
    current_y = start_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (MOBILE_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, current_y), line, font=font, fill=(255, 255, 255))
        current_y += line_heights[i] + 10
    
    return img_with_text

@app.get("/")
@app.get("/wallpaper")
async def generate_wallpaper():
    """Генерирует обои"""
    try:
        quote = get_biblical_quote()
        print(f"Используем цитату: {quote}")
        
        background = get_unsplash_image()
        
        if background is None:
            background = create_gradient_background()
        
        final_image = add_text_to_image(background, quote)
        
        img_byte_arr = io.BytesIO()
        final_image.save(
            img_byte_arr, 
            format='JPEG', 
            quality=JPEG_QUALITY, 
            optimize=True
        )
        img_byte_arr.seek(0)
        
        del background
        del final_image
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        print(f"Ошибка: {e}")
        img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT), (100, 80, 150))
        img = add_text_to_image(img, random.choice(FALLBACK_QUOTES))
        
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
