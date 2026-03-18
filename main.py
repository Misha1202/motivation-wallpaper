"""
Сервис для генерации мотивационных обоев для телефона
С реальными изображениями и правильным позиционированием текста
Размер под iPhone 12 Pro (1170x2532)
"""

import os
import io
import requests
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time

# Конфигурация
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")  # Получите на pexels.com

# URL API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
PEXELS_API_URL = "https://api.pexels.com/v1/search"
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

# Кэш для цитат
quote_cache = {
    "quote": "",
    "timestamp": 0
}
CACHE_DURATION = 1800  # 30 минут

# Запасные цитаты
FALLBACK_QUOTES = [
    "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)",
    "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Блаженны милостивые, ибо они помилованы будут\n(Матфея 5:7)",
    "Господь — Пастырь мой; я ни в чем не буду нуждаться\n(Псалом 22:1)",
    "Все могу в укрепляющем меня Иисусе Христе\n(Филиппийцам 4:13)",
    "Не бойся, только веруй\n(Марка 5:36)"
]

def get_biblical_quote():
    """
    Получает библейскую цитату от DeepSeek API
    """
    global quote_cache
    
    current_time = time.time()
    if quote_cache["quote"] and (current_time - quote_cache["timestamp"] < CACHE_DURATION):
        return quote_cache["quote"]
    
    if not DEEPSEEK_API_KEY:
        return random.choice(FALLBACK_QUOTES)
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    is_biblical = random.random() < 0.8
    
    if is_biblical:
        prompt_text = """Сгенерируй вдохновляющую библейскую цитату для обоев.
Формат: сама цитата, потом с новой строки (Источник)
Цитата должна быть на русском, 3-7 строк.
Пример:
Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного
(Иоанна 3:16)"""
    else:
        prompt_text = """Сгенерируй мощную мотивационную цитату для обоев.
Формат: сама цитата, потом с новой строки (Автор)
3-7 строк.
Пример:
Верь в себя, и у тебя всё получится
(Народная мудрость)"""
    
    prompt = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты генератор цитат. Отвечай только цитатой."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.9,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=prompt, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        quote = data["choices"][0]["message"]["content"].strip()
        quote = quote.strip('"').strip('„').strip('“')
        
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        
        return quote
        
    except Exception as e:
        print(f"Ошибка DeepSeek API: {e}")
        return random.choice(FALLBACK_QUOTES)

def get_image_from_pexels(keyword=None):
    """
    Получает реальное изображение с Pexels API
    """
    if not keyword:
        keywords = [
            "nature", "mountains", "sunset", "ocean", "forest",
            "sky", "stars", "clouds", "landscape", "peaceful",
            "church", "cathedral", "light", "heaven", "spiritual"
        ]
        keyword = random.choice(keywords)
    
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": keyword,
        "per_page": 1,
        "orientation": "portrait",
        "size": "large"
    }
    
    try:
        response = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["photos"]:
            # Берем фото с хорошим разрешением
            photo = data["photos"][0]
            img_url = photo["src"]["portrait"]  # или original для макс качества
            
            # Скачиваем изображение
            img_response = requests.get(img_url, timeout=15)
            img_response.raise_for_status()
            
            img_bytes = io.BytesIO(img_response.content)
            background = Image.open(img_bytes)
            
            # Обрезаем/масштабируем под наш размер
            background = background.resize((MOBILE_WIDTH, MOBILE_HEIGHT), Image.Resampling.LANCZOS)
            
            # Добавляем легкое затемнение для читаемости текста
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.8)  # затемняем на 20%
            
            return background
    except Exception as e:
        print(f"Ошибка Pexels: {e}")
    
    # Если Pexels не сработал - пробуем Unsplash
    return get_image_from_unsplash()

def get_image_from_unsplash(keyword=None):
    """
    Запасной вариант - Unsplash API
    """
    if not keyword:
        keyword = random.choice(["nature", "spiritual", "landscape", "sky"])
    
    # Unsplash требует Client-ID
    # Для демо используем публичный Access Key (нужно зарегистрироваться)
    # Пока заフォールбэк на градиент
    
    # Временно возвращаем градиент
    return create_gradient_background()

def create_gradient_background():
    """
    Создает красивый градиентный фон как запасной вариант
    """
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Библейские цвета
    color_schemes = [
        ((180, 150, 100), (100, 80, 150)),  # золото-фиолетовый
        ((200, 180, 150), (80, 100, 180)),  # песчано-синий
        ((140, 170, 200), (70, 70, 120)),   # небесно-синий
    ]
    
    color1, color2 = random.choice(color_schemes)
    
    # Радиальный градиент от центра
    center_x, center_y = MOBILE_WIDTH // 2, MOBILE_HEIGHT // 3
    
    for y in range(MOBILE_HEIGHT):
        for x in range(0, MOBILE_WIDTH, 3):
            dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            max_dist = max(MOBILE_WIDTH, MOBILE_HEIGHT)
            ratio = min(1.0, dist / max_dist * 1.5)
            
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            
            draw.point((x, y), fill=(r, g, b))
            if x + 1 < MOBILE_WIDTH:
                draw.point((x + 1, y), fill=(r, g, b))
            if x + 2 < MOBILE_WIDTH:
                draw.point((x + 2, y), fill=(r, g, b))
    
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    return img

def wrap_text_to_fit(text, font, max_width, draw):
    """
    Разбивает текст на строки с учетом ширины
    """
    # Сначала разбиваем по существующим переносам строк
    paragraphs = text.split('\n')
    all_lines = []
    
    for para in paragraphs:
        if not para.strip():
            continue
            
        words = para.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Проверяем ширину
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        all_lines.extend(lines)
    
    return all_lines

def add_text_to_image(image, text):
    """
    Накладывает текст с авто-подгоном размера и смещением ниже центра
    """
    img_with_text = image.copy().convert('RGBA')
    draw = ImageDraw.Draw(img_with_text)
    
    # Параметры текста
    max_width = MOBILE_WIDTH - 200  # отступы по бокам
    target_y_position = MOBILE_HEIGHT * 0.65  # 65% от верхнего края (ниже центра)
    
    # Пробуем разные размеры шрифта
    font_sizes = [140, 130, 120, 110, 100, 90, 80, 70, 60]
    selected_font = None
    selected_lines = []
    selected_font_size = 60
    
    # Пытаемся найти шрифт
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/System/Library/Fonts/Times.ttc",
        "C:\\Windows\\Fonts\\times.ttf",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 140)
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
    
    # Подбираем оптимальный размер шрифта
    for size in font_sizes:
        try:
            current_font = ImageFont.truetype(font.path, size) if hasattr(font, 'path') else font
        except:
            current_font = font
        
        # Разбиваем текст
        lines = wrap_text_to_fit(text, current_font, max_width, draw)
        
        if len(lines) <= 6:  # Не больше 6 строк
            selected_font = current_font
            selected_lines = lines
            selected_font_size = size
            break
    
    if not selected_font:
        # Если ничего не подошло - используем базовый
        selected_font = font
        selected_lines = text.split('\n')[:4]
    
    # Рассчитываем высоту текстового блока
    line_heights = []
    total_height = 0
    
    for line in selected_lines:
        bbox = draw.textbbox((0, 0), line, font=selected_font)
        height = bbox[3] - bbox[1]
        line_heights.append(height)
        total_height += height + 15
    
    total_height -= 15
    
    # Позиция текста (смещена ниже центра)
    start_y = int(target_y_position - total_height / 2)
    
    # Создаем подложку под текст
    # Сначала находим максимальную ширину строки
    max_line_width = 0
    for line in selected_lines:
        bbox = draw.textbbox((0, 0), line, font=selected_font)
        max_line_width = max(max_line_width, bbox[2] - bbox[0])
    
    padding = 60
    overlay = Image.new('RGBA', img_with_text.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Рисуем полупрозрачный прямоугольник
    overlay_draw.rectangle(
        [(MOBILE_WIDTH - max_line_width) // 2 - padding,
         start_y - padding,
         (MOBILE_WIDTH + max_line_width) // 2 + padding,
         start_y + total_height + padding],
        fill=(0, 0, 0, 180)
    )
    
    # Добавляем декоративные элементы для библейских цитат
    if any(word in text.lower() for word in ["господ", "бог", "христ", "иисус", "свят"]):
        # Золотая линия слева
        overlay_draw.rectangle(
            [(MOBILE_WIDTH - max_line_width) // 2 - padding - 5,
             start_y - padding - 10,
             (MOBILE_WIDTH - max_line_width) // 2 - padding,
             start_y + total_height + padding + 10],
            fill=(255, 215, 0, 200)
        )
        # Золотая линия справа
        overlay_draw.rectangle(
            [(MOBILE_WIDTH + max_line_width) // 2 + padding,
             start_y - padding - 10,
             (MOBILE_WIDTH + max_line_width) // 2 + padding + 5,
             start_y + total_height + padding + 10],
            fill=(255, 215, 0, 200)
        )
    
    # Накладываем подложку
    img_with_text = Image.alpha_composite(img_with_text, overlay)
    draw = ImageDraw.Draw(img_with_text)
    
    # Рисуем текст
    current_y = start_y
    
    for i, line in enumerate(selected_lines):
        # Центрируем строку
        bbox = draw.textbbox((0, 0), line, font=selected_font)
        line_width = bbox[2] - bbox[0]
        x = (MOBILE_WIDTH - line_width) // 2
        
        # Тень
        draw.text((x + 3, current_y + 3), line, font=selected_font, fill=(0, 0, 0, 150))
        
        # Текст
        if any(word in text.lower() for word in ["господ", "бог", "христ", "иисус", "свят"]):
            # Теплый белый для библейских
            draw.text((x, current_y), line, font=selected_font, fill=(255, 245, 220))
        else:
            draw.text((x, current_y), line, font=selected_font, fill=(255, 255, 255))
        
        current_y += line_heights[i] + 15
    
    return img_with_text.convert('RGB')

@app.get("/")
@app.get("/wallpaper")
async def generate_wallpaper():
    """
    Генерирует обои с реальными изображениями и правильным текстом
    """
    try:
        # Получаем цитату
        quote = get_biblical_quote()
        
        # Пытаемся получить реальное изображение
        if PEXELS_API_KEY:
            # Определяем ключевое слово из цитаты
            keywords = {
                "гор": "mountains",
                "мор": "ocean",
                "неб": "sky",
                "звезд": "stars",
                "свет": "light",
                "храм": "church",
                "пут": "path",
                "сад": "garden",
                "цвет": "flowers"
            }
            
            keyword = "spiritual"
            for ru, en in keywords.items():
                if ru in quote.lower():
                    keyword = en
                    break
            
            background = get_image_from_pexels(keyword)
        else:
            background = create_gradient_background()
        
        # Добавляем текст
        final_image = add_text_to_image(background, quote)
        
        # Сохраняем
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=95, optimize=True)
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        print(f"Ошибка: {e}")
        # Временное решение при ошибке
        img = create_gradient_background()
        img = add_text_to_image(img, random.choice(FALLBACK_QUOTES))
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
