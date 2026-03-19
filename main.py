"""
Генератор обоев с библейскими цитатами для GitHub Pages
Берет цитаты с azbyka.ru по ID из файла ЦИТАТЫ.txt
"""

import os
import random
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
import base64
from datetime import datetime

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
UNSPLASH_ACCESS_KEY = "t9SeuIi4nAnCIb2vIPnA9hAYx4CbIbrbgdTHrBSDjZc"
UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532
JPEG_QUALITY = 85
RESAMPLE_FILTER = Image.Resampling.BILINEAR

# Читаем ID цитат из файла
QUOTE_IDS = []
try:
    with open('ЦИТАТЫ.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() and '\t' in line:
                quote_id = line.split('\t')[0].strip()
                if quote_id.isdigit():
                    QUOTE_IDS.append(quote_id)
    print(f"Загружено {len(QUOTE_IDS)} ID цитат")
except Exception as e:
    print(f"Ошибка загрузки ID: {e}")
    # Запасные ID на случай ошибки
    QUOTE_IDS = ['162', '15', '28', '39', '51', '95', '121', '155', '188', '217']

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
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем все параграфы с классом txt
            quote_paragraphs = soup.find_all('p', class_='txt')
            
            if quote_paragraphs:
                # Собираем все параграфы в одну цитату
                quote_parts = []
                for p in quote_paragraphs:
                    text = p.get_text().strip()
                    if text:
                        quote_parts.append(text)
                
                if quote_parts:
                    full_quote = '\n'.join(quote_parts)
                    print(f"Получена цитата ID {quote_id}: {full_quote[:100]}...")
                    return full_quote
            else:
                # Если нет p.txt, ищем другой текст
                content = soup.find('div', class_='content')
                if content:
                    text = content.get_text().strip()
                    if text:
                        print(f"Получена цитата ID {quote_id} (из content)")
                        return text
                        
    except Exception as e:
        print(f"Ошибка получения цитаты {quote_id}: {e}")
    
    return None

def get_random_quote():
    """Получает случайную цитату из списка ID"""
    if not QUOTE_IDS:
        return "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)"
    
    # Пробуем разные ID пока не получим цитату
    random.shuffle(QUOTE_IDS)
    for quote_id in QUOTE_IDS[:10]:  # Пробуем максимум 10 ID
        quote = get_quote_from_azbyka(quote_id)
        if quote:
            return quote
    
    # Если ничего не получилось, возвращаем запасную
    return "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)"

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
        font = ImageFont.load_default()
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
            "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
            "C:\\Windows\\Fonts\\times.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 90)
                break
    except:
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
# ГЕНЕРАЦИЯ HTML ДЛЯ GITHUB PAGES
# ============================================

def generate_html():
    """Генерирует HTML страницу с обоями"""
    
    # Получаем цитату
    quote = get_random_quote()
    print(f"Итоговая цитата: {quote[:100]}...")
    
    # Получаем фон и добавляем текст
    background = get_background_image()
    final_image = add_text_to_image(background, quote)
    
    # Конвертируем в base64
    img_byte_arr = io.BytesIO()
    final_image.save(img_byte_arr, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    img_byte_arr.seek(0)
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    
    # Создаем HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Библейские обои</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #1a1a1a;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .wallpaper-container {{
            width: 100%;
            max-width: 430px; /* Ширина iPhone */
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border-radius: 20px;
            overflow: hidden;
        }}
        .wallpaper-image {{
            display: block;
            width: 100%;
            height: auto;
            aspect-ratio: 1170/2532;
            background: #000;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .footer a {{
            color: #888;
            text-decoration: none;
        }}
        .footer a:hover {{
            color: #aaa;
        }}
        @media (max-width: 480px) {{
            .wallpaper-container {{
                max-width: 100%;
                border-radius: 0;
            }}
        }}
    </style>
</head>
<body>
    <div style="width: 100%; padding: 10px;">
        <div class="wallpaper-container">
            <img class="wallpaper-image" src="data:image/jpeg;base64,{img_base64}" alt="Библейские обои">
        </div>
        <div class="footer">
            <p>Случайная библейская цитата • <a href="?refresh={random.randint(1, 999999)}">Обновить</a></p>
            <p style="font-size: 10px; margin-top: 5px;">Создано {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html

# ============================================
# ГЕНЕРАЦИЯ ФАЙЛОВ ДЛЯ GITHUB PAGES
# ============================================

def main():
    """Генерирует HTML файл для GitHub Pages"""
    
    # Создаем папку docs если её нет
    if not os.path.exists('docs'):
        os.makedirs('docs')
    
    # Генерируем HTML
    html_content = generate_html()
    
    # Сохраняем в docs/index.html
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML файл создан: docs/index.html")
    
    # Создаем простой README
    readme = """# Библейские обои для телефона

Генератор обоев с библейскими цитатами для мобильных устройств.

## Как использовать

1. Откройте [https://ваш-логин.github.io/репозиторий/](https://ваш-логин.github.io/репозиторий/)
2. Сохраните изображение на телефон (долгое нажатие → "Сохранить изображение")
3. Нажмите "Обновить" для новой цитаты

## Источник цитат

Цитаты берутся с https://azbyka.ru/otechnik/Biblia/tsitaty-iz-biblii/

Формат обоев: iPhone 12 Pro (1170x2532)
"""
    
    with open('docs/README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print("✅ README создан")

if __name__ == "__main__":
    main()
