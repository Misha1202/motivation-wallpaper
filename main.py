"""
Сервис для генерации мотивационных обоев для телефона
Для деплоя на Render.com
"""

import os
import io
import requests
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import hashlib
import time

# Конфигурация
DEEPSEEK_API_KEY = os.getenv("sk-3c2f6de436a14a638a40492e218b17d9", "")

# URL API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"

# Создаем FastAPI приложение
app = FastAPI()

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Размеры для мобильных обоев
MOBILE_WIDTH = 1080
MOBILE_HEIGHT = 1920

# Кэш для мотивационных фраз
quote_cache = {
    "quote": "",
    "timestamp": 0
}
CACHE_DURATION = 3600  # 1 час

def get_motivation_from_deepseek():
    """
    Получает мотивационную фразу от DeepSeek API
    """
    global quote_cache
    
    # Проверяем кэш
    current_time = time.time()
    if quote_cache["quote"] and (current_time - quote_cache["timestamp"] < CACHE_DURATION):
        return quote_cache["quote"]
    
    # Если нет ключа API, сразу возвращаем случайную фразу
    if not DEEPSEEK_API_KEY:
        return random.choice([
            "Верь в себя",
            "Невозможное возможно", 
            "Действуй сегодня",
            "Ты сильнее чем кажется",
            "Каждый день — новый шанс",
            "Мечты сбываются",
            "Будь смелее",
            "Никогда не сдавайся"
        ])
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system", 
                "content": "Ты - генератор вдохновляющих цитат. Создай короткую, мощную мотивационную фразу для обоев на телефон. Фраза должна быть на русском языке, не более 5-7 слов. Отвечай только самой фразой, без пояснений."
            },
            {
                "role": "user",
                "content": "Сгенерируй мотивационную фразу"
            }
        ],
        "temperature": 0.9,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=prompt,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        quote = data["choices"][0]["message"]["content"].strip()
        quote = quote.strip('"').strip('„').strip('“')
        
        # Сохраняем в кэш
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        
        return quote
        
    except Exception as e:
        print(f"Ошибка DeepSeek API: {e}")
        if quote_cache["quote"]:
            return quote_cache["quote"]
        return random.choice([
            "Верь в себя",
            "Невозможное возможно", 
            "Действуй сегодня",
            "Ты сильнее чем кажется"
        ])

def generate_background_prompt():
    """
    Генерирует промпт для создания фонового изображения
    """
    themes = [
        "motivational background mountain landscape sunrise",
        "beautiful ocean sunset motivational wallpaper",
        "inspiring forest with mist nature background",
        "abstract gradient smooth colors calm",
        "starry night sky motivation",
        "minimalist pastel tones abstract",
        "mountain lake reflection peaceful",
        "endless flower field at sunset"
    ]
    
    theme = random.choice(themes)
    return theme

def get_image_from_pollinations(prompt=None):
    """
    Получает изображение от Pollinations.AI
    """
    if not prompt:
        prompt = generate_background_prompt()
    
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 10000)
    image_url = f"{POLLINATIONS_URL}{encoded_prompt}?width={MOBILE_WIDTH}&height={MOBILE_HEIGHT}&nologo=true&safe=false&seed={seed}"
    
    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        
        img_bytes = io.BytesIO(response.content)
        background = Image.open(img_bytes)
        background = background.resize((MOBILE_WIDTH, MOBILE_HEIGHT), Image.Resampling.LANCZOS)
        return background
        
    except Exception as e:
        print(f"Ошибка при получении изображения: {e}")
        return create_gradient_background()

def create_gradient_background():
    """
    Создает градиентный фон
    """
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    color_schemes = [
        ((100, 80, 180), (180, 150, 255)),
        ((255, 200, 100), (255, 100, 100)),
        ((100, 200, 255), (50, 100, 200)),
        ((150, 255, 150), (50, 150, 50)),
    ]
    
    color1, color2 = random.choice(color_schemes)
    
    for i in range(MOBILE_HEIGHT):
        ratio = i / MOBILE_HEIGHT
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, i), (MOBILE_WIDTH, i)], fill=(r, g, b))
    
    img = img.filter(ImageFilter.GaussianBlur(radius=5))
    return img

def add_text_to_image(image, text):
    """
    Накладывает текст на изображение
    """
    img_with_text = image.copy()
    draw = ImageDraw.Draw(img_with_text)
    
    # Пытаемся загрузить шрифт
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        except:
            font = ImageFont.load_default()
    
    # Разбиваем текст на строки
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > 20 or len(current_line) >= 4:
            lines.append(' '.join(current_line))
            current_line = []
    
    if current_line:
        lines.append(' '.join(current_line))
    
    text_to_draw = '\n'.join(lines)
    
    # Получаем размеры текста
    if hasattr(draw, 'multiline_textbbox'):
        bbox = draw.multiline_textbbox((0, 0), text_to_draw, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = MOBILE_WIDTH // 2
        text_height = 200
    
    # Позиция текста (центр)
    x = (MOBILE_WIDTH - text_width) // 2
    y = (MOBILE_HEIGHT - text_height) // 2
    
    # Полупрозрачный фон под текст
    padding = 40
    overlay = Image.new('RGBA', img_with_text.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
        fill=(0, 0, 0, 180)
    )
    
    img_with_text = Image.alpha_composite(img_with_text.convert('RGBA'), overlay)
    img_with_text = img_with_text.convert('RGB')
    draw = ImageDraw.Draw(img_with_text)
    
    # Рисуем текст
    draw.multiline_text((x, y), text_to_draw, font=font, fill=(255, 255, 255), align='center')
    
    return img_with_text

@app.get("/")
@app.get("/wallpaper")
async def generate_wallpaper():
    """
    Генерирует мотивационные обои
    """
    try:
        quote = get_motivation_from_deepseek()
        theme = generate_background_prompt()
        background = get_image_from_pollinations(theme)
        final_image = add_text_to_image(background, quote)
        
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=90)
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Content-Disposition": "inline; filename=wallpaper.jpg"
            }
        )
        
    except Exception as e:
        print(f"Ошибка: {e}")
        img = create_gradient_background()
        img = add_text_to_image(img, "Попробуйте позже")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")

@app.get("/health")
async def health_check():
    return {"status": "ok", "time": time.time()}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
