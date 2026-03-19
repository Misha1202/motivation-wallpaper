"""
Максимально простой сервер для генерации обоев
При каждом обновлении страницы - новая картинка
"""

import os
import io
import random
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
UNSPLASH_ACCESS_KEY = "t9SeuIi4nAnCIb2vIPnA9hAYx4CbIbrbgdTHrBSDjZc"
UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532
JPEG_QUALITY = 95

# Загрузка ID цитат из файла
QUOTE_IDS = []
try:
    with open('ЦИТАТЫ.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() and '\t' in line:
                quote_id = line.split('\t')[0].strip()
                if quote_id.isdigit():
                    QUOTE_IDS.append(quote_id)
    print(f"✅ Загружено {len(QUOTE_IDS)} ID цитат")
except Exception as e:
    print(f"⚠️ Ошибка загрузки ID: {e}")
    QUOTE_IDS = ['162', '15', '28', '39', '51', '95', '121', '155', '188', '217']

# Запасные цитаты
FALLBACK_QUOTES = [
    "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)",
    "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Господь — Пастырь мой; я ни в чем не буду нуждаться\n(Псалом 22:1)",
    "Все могу в укрепляющем меня Иисусе Христе\n(Филиппийцам 4:13)",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ПРОСТЕЙШИЙ HTML - ТОЛЬКО КАРТИНКА
# ============================================
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Библейские обои</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        img {
            width: 100%;
            max-width: 430px;
            height: auto;
            display: block;
            border: none;
        }
    </style>
</head>
<body>
    <!-- При каждом обновлении страницы - новая картинка -->
    <img src="/image" alt="Библейские обои">
</body>
</html>
"""

# ============================================
# ПОЛУЧЕНИЕ ЦИТАТЫ (исправленная версия)
# ============================================
def get_quote_from_azbyka(quote_id):
    """Получает одну случайную цитату с azbyka.ru по ID"""
    try:
        url = f"https://azbyka.ru/otechnik/Biblia/tsitaty-iz-biblii/{quote_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим все параграфы с классом txt
            quote_paragraphs = soup.find_all('p', class_='txt')
            
            if quote_paragraphs:
                # Выбираем случайный параграф
                random_paragraph = random.choice(quote_paragraphs)
                
                # Получаем текст, убираем HTML теги
                text = random_paragraph.get_text().strip()
                
                # Очищаем от лишних пробелов
                text = ' '.join(text.split())
                
                print(f"✅ Выбрана случайная цитата {len(quote_paragraphs)} из {len(quote_paragraphs)}")
                return text
            
            # Если нет p.txt, ищем другой текст
            content = soup.find('div', class_='content')
            if content:
                text = content.get_text().strip()
                return ' '.join(text.split())
                    
    except Exception as e:
        print(f"❌ Ошибка получения цитаты {quote_id}: {e}")
    
    return None

# ============================================
# ПОЛУЧЕНИЕ ФОНА
# ============================================
def get_unsplash_image():
    """Получает изображение с Unsplash API"""
    keywords = ["nature", "mountain", "ocean", "forest", "sky", "spiritual", "light", "clouds", "peaceful"]
    keyword = random.choice(keywords)
    
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
            background = background.resize((MOBILE_WIDTH, MOBILE_HEIGHT), Image.Resampling.LANCZOS)
            
            if background.mode != 'RGB':
                background = background.convert('RGB')
            
            # Затемняем фон для лучшей читаемости
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.6)
            
            return background
            
    except Exception as e:
        print(f"Ошибка Unsplash: {e}")
    
    return None

def create_gradient_background():
    """Создает градиентный фон"""
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    colors = [
        ((180, 150, 100), (100, 80, 150)),  # золотой-фиолетовый
        ((200, 180, 150), (80, 100, 180)),  # песочный-синий
        ((140, 170, 200), (70, 70, 120)),   # небесный-синий
    ]
    
    color1, color2 = random.choice(colors)
    
    for y in range(MOBILE_HEIGHT):
        ratio = y / MOBILE_HEIGHT
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, y), (MOBILE_WIDTH, y)], fill=(r, g, b))
    
    return img

# ============================================
# КРАСИВЫЙ ТЕКСТ
# ============================================
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

def add_beautiful_text(image, text):
    """Накладывает красивый текст на изображение - смещен вниз"""
    img = image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Загружаем красивый шрифт
    try:
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
        ]
        
        title_font = None
        for path in font_paths:
            if os.path.exists(path):
                title_font = ImageFont.truetype(path, 110)
                break
        
        if title_font is None:
            title_font = ImageFont.load_default()
            
    except:
        title_font = ImageFont.load_default()
    
    # Параметры текста
    max_width = MOBILE_WIDTH - 200
    
    # СМЕЩАЕМ ТЕКСТ НИЖЕ (было center_y = MOBILE_HEIGHT // 2)
    # Теперь текст начинается на 60% высоты экрана (ниже центра)
    text_start_y = int(MOBILE_HEIGHT * 0.6)  # 60% от верхнего края
    
    # Разбиваем текст
    lines = wrap_text(text, title_font, max_width, draw)
    
    # Вычисляем высоту текста
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h + 15
    total_height -= 15
    
    # Позиция начала (текст центрирован относительно точки text_start_y)
    start_y = text_start_y - total_height // 2
    current_y = start_y
    
    # Рисуем каждую строку
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = bbox[2] - bbox[0]
        x = (MOBILE_WIDTH - line_width) // 2
        
        # Тень
        shadow_offset = 4
        draw.text((x + shadow_offset, current_y + shadow_offset), line, 
                 font=title_font, fill=(0, 0, 0, 180))
        
        # Легкое свечение
        for offset in range(1, 3):
            draw.text((x - offset, current_y), line, font=title_font, fill=(255, 255, 255, 30))
            draw.text((x + offset, current_y), line, font=title_font, fill=(255, 255, 255, 30))
            draw.text((x, current_y - offset), line, font=title_font, fill=(255, 255, 255, 30))
            draw.text((x, current_y + offset), line, font=title_font, fill=(255, 255, 255, 30))
        
        # Основной текст
        draw.text((x, current_y), line, font=title_font, fill=(255, 255, 255, 255))
        
        current_y += line_heights[i] + 15
    
    return img.convert('RGB')

# ============================================
# ЭНДПОИНТЫ
# ============================================
@app.get("/", response_class=HTMLResponse)
async def root():
    """Страница с картинкой - при обновлении новая"""
    return HTMLResponse(SIMPLE_HTML)

@app.get("/image")
async def get_image():
    """Генерирует случайную картинку"""
    try:
        # Случайная цитата
        quote_id = random.choice(QUOTE_IDS)
        quote = get_quote_from_azbyka(quote_id)
        
        if not quote:
            quote = random.choice(FALLBACK_QUOTES)
        
        # Случайный фон
        background = get_unsplash_image()
        if not background:
            background = create_gradient_background()
        
        # Добавляем текст
        final_image = add_beautiful_text(background, quote)
        
        # Отдаем картинку
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        print(f"Ошибка: {e}")
        # Запасной вариант
        img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT), (100, 80, 150))
        img = add_beautiful_text(img, random.choice(FALLBACK_QUOTES))
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
