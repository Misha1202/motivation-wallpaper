"""
Сервер для генерации обоев с библейскими цитатами
Деплой на Render.com
"""

import os
import io
import random
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
UNSPLASH_ACCESS_KEY = "t9SeuIi4nAnCIb2vIPnA9hAYx4CbIbrbgdTHrBSDjZc"
UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532
JPEG_QUALITY = 85
RESAMPLE_FILTER = Image.Resampling.BILINEAR

# Запасные цитаты на случай ошибок
FALLBACK_QUOTES = [
    "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)",
    "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Господь — Пастырь мой; я ни в чем не буду нуждаться\n(Псалом 22:1)",
    "Все могу в укрепляющем меня Иисусе Христе\n(Филиппийцам 4:13)",
    "Бог есть любовь\n(1 Иоанна 4:8)",
]

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ПОЛУЧЕНИЕ ЦИТАТЫ С AZBYKA.RU
# ============================================

def get_quote_from_azbyka(quote_id):
    """Получает цитату с azbyka.ru по ID"""
    try:
        url = f"https://azbyka.ru/otechnik/Biblia/tsitaty-iz-biblii/{quote_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"Запрашиваем цитату ID: {quote_id}")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем все параграфы с классом txt
            quote_paragraphs = soup.find_all('p', class_='txt')
            
            if quote_paragraphs:
                quote_parts = []
                for p in quote_paragraphs:
                    text = p.get_text().strip()
                    if text:
                        quote_parts.append(text)
                
                if quote_parts:
                    full_quote = '\n'.join(quote_parts)
                    print(f"Найдено {len(quote_parts)} параграфов")
                    return full_quote
            
            # Если не нашли p.txt, ищем другой текст
            content = soup.find('div', class_='content')
            if content:
                text = content.get_text().strip()
                if text:
                    return text
                    
    except Exception as e:
        print(f"Ошибка получения цитаты {quote_id}: {e}")
    
    return None

# ============================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ИЗОБРАЖЕНИЙ
# ============================================

def get_unsplash_image():
    """Получает изображение с Unsplash API"""
    keywords = ["nature", "mountain", "ocean", "forest", "sky", "spiritual", "peaceful", "light", "clouds"]
    keyword = random.choice(keywords)
    
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {
        "query": keyword,
        "orientation": "portrait",
        "count": 1,
        "content_filter": "high"
    }
    
    try:
        print(f"Запрашиваем фото с Unsplash: {keyword}")
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
            
            # Затемняем для лучшей читаемости текста
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.7)
            
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
        ((100, 120, 150), (50, 50, 80)),     # синий-темно-синий
        ((150, 130, 100), (80, 60, 100)),    # бежевый-фиолетовый
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
    img = get_unsplash_image()
    if img:
        return img
    
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
        # Пробуем разные пути для шрифтов
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
            "C:\\Windows\\Fonts\\times.ttf",
            "/app/.fonts/DejaVuSerif-Bold.ttf"
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 90)
                print(f"Загружен шрифт: {path}")
                break
        
        if font is None:
            font = ImageFont.load_default()
            print("Используем шрифт по умолчанию")
    except Exception as e:
        print(f"Ошибка загрузки шрифта: {e}")
        font = ImageFont.load_default()
    
    # Параметры текста
    max_width = MOBILE_WIDTH - 160
    target_y = int(MOBILE_HEIGHT * 0.65)
    
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
# ЭНДПОИНТЫ API
# ============================================

@app.get("/")
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "ok",
        "service": "Bible Wallpaper Generator",
        "version": "1.0"
    }

@app.get("/generate/{quote_id}")
async def generate_wallpaper(quote_id: str):
    """Генерирует обои с цитатой по ID"""
    try:
        print(f"Генерация обоев для ID: {quote_id}")
        
        # Получаем цитату
        quote = get_quote_from_azbyka(quote_id)
        
        if not quote:
            print(f"Цитата не найдена, используем запасную")
            quote = random.choice(FALLBACK_QUOTES)
        
        print(f"Цитата: {quote[:100]}...")
        
        # Получаем фон
        background = get_background_image()
        
        # Добавляем текст
        final_image = add_text_to_image(background, quote)
        
        # Сохраняем в байты
        img_byte_arr = io.BytesIO()
        final_image.save(
            img_byte_arr, 
            format='JPEG', 
            quality=JPEG_QUALITY, 
            optimize=True
        )
        img_byte_arr.seek(0)
        
        # Возвращаем изображение
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        # Возвращаем простое изображение с ошибкой
        img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT), (100, 80, 150))
        img = add_text_to_image(img, random.choice(FALLBACK_QUOTES))
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")

@app.get("/random")
async def random_wallpaper():
    """Генерирует обои со случайной цитатой"""
    # Здесь нужно будет получать случайный ID из файла
    # Но так как на сервере нет файла, используем фиксированные
    random_ids = ["162", "15", "28", "39", "51", "95", "121", "155", "188", "217"]
    quote_id = random.choice(random_ids)
    return await generate_wallpaper(quote_id)

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
