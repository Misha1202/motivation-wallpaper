"""
Сервис для генерации мотивационных обоев для телефона
С библейскими цитатами и красивым оформлением
Размер под iPhone 12 Pro (1170x2532)
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

# Размеры для iPhone 12 Pro
MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532

# Кэш для цитат
quote_cache = {
    "quote": "",
    "timestamp": 0
}
CACHE_DURATION = 1800  # 30 минут

def get_biblical_quote():
    """
    Получает библейскую цитату от DeepSeek API
    """
    global quote_cache
    
    # Проверяем кэш
    current_time = time.time()
    if quote_cache["quote"] and (current_time - quote_cache["timestamp"] < CACHE_DURATION):
        return quote_cache["quote"]
    
    # Если нет ключа API, используем готовые цитаты
    if not DEEPSEEK_API_KEY:
        return random.choice(FALLBACK_QUOTES)
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Выбираем тип запроса (80% библейские, 20% мотивационные)
    is_biblical = random.random() < 0.8
    
    if is_biblical:
        prompt_text = """Ты - помощник для создания красивых обоев с библейскими цитатами.
Сгенерируй вдохновляющую библейскую цитату или стих из Евангелия.
Важно: 
- Цитата должна быть на русском языке
- Укажи источник (книгу, главу, стих) в скобках после цитаты
- Цитата должна быть не очень длинной (3-7 строк)
- Подбери цитату, которая хорошо смотрится на обоях
- Можно использовать как прямые цитаты, так и перефразированные

Примеры хороших цитат:
"Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного" (Иоанна 3:16)
"Уповай на Господа всем сердцем твоим" (Притчи 3:5)
"Блаженны милостивые, ибо они помилованы будут" (Матфея 5:7)
"Господь — Пастырь мой; я ни в чем не буду нуждаться" (Псалом 22:1)
"Все могу в укрепляющем меня Иисусе Христе" (Филиппийцам 4:13)

Ответ дай только цитатой со ссылкой, без пояснений."""
    else:
        prompt_text = """Сгенерируй короткую мощную мотивационную цитату для обоев на телефон.
Цитата должна быть на русском языке, вдохновляющей.
Если у цитаты есть автор - укажи его в скобках.
Длина: 3-7 строк.

Примеры:
"Верь в себя, и у тебя всё получится"
"Каждый день — новая возможность изменить свою жизнь"
"Счастье не в том, чтобы делать всегда, что хочешь, а в том, чтобы всегда хотеть того, что делаешь" (Лев Толстой)

Ответ дай только цитатой."""
    
    prompt = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system", 
                "content": "Ты генератор красивых цитат для обоев. Отвечаешь только текстом цитаты, без пояснений."
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        "temperature": 0.9,
        "max_tokens": 150
    }
    
    try:
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
        
        # Сохраняем в кэш
        quote_cache["quote"] = quote
        quote_cache["timestamp"] = current_time
        
        return quote
        
    except Exception as e:
        print(f"Ошибка DeepSeek API: {e}")
        if quote_cache["quote"]:
            return quote_cache["quote"]
        return random.choice(FALLBACK_QUOTES)

# Запасные цитаты на случай ошибки API
FALLBACK_QUOTES = [
    "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного\n(Иоанна 3:16)",
    "Уповай на Господа всем сердцем твоим\n(Притчи 3:5)",
    "Блаженны милостивые, ибо они помилованы будут\n(Матфея 5:7)",
    "Господь — Пастырь мой; я ни в чем не буду нуждаться\n(Псалом 22:1)",
    "Все могу в укрепляющем меня Иисусе Христе\n(Филиппийцам 4:13)",
    "Не бойся, только веруй\n(Марка 5:36)",
    "Просите, и дано будет вам; ищите, и найдете; стучите, и отворят вам\n(Матфея 7:7)",
    "Возлюби ближнего твоего, как самого себя\n(Матфея 22:39)"
]

def generate_biblical_prompt(quote):
    """
    Генерирует промпт для изображения на основе цитаты
    """
    quote_lower = quote.lower()
    
    # Определяем тему по ключевым словам
    themes = []
    
    if any(word in quote_lower for word in ["свет", "све", "сия", "заря", "рассвет"]):
        themes = ["divine light", "holy light", "sunlight through clouds", "celestial light"]
    elif any(word in quote_lower for word in ["гор", "вершин", "скал"]):
        themes = ["mountains", "sacred mountain", "mountain peak with light"]
    elif any(word in quote_lower for word in ["мор", "океан", "вод", "рек"]):
        themes = ["calm sea", "ocean waves", "sea of galilee", "water"]
    elif any(word in quote_lower for word in ["неб", "звезд", "облак"]):
        themes = ["starry night sky", "heavenly clouds", "celestial sky"]
    elif any(word in quote_lower for word in ["пут", "дорог", "троп"]):
        themes = ["path through forest", "road to light", "pathway"]
    elif any(word in quote_lower for word in ["сад", "цвет", "поле"]):
        themes = ["garden", "field of flowers", "peaceful meadow"]
    elif any(word in quote_lower for word in ["храм", "церк", "свеч"]):
        themes = ["church interior", "candles", "stained glass"]
    else:
        # Универсальные библейские темы
        themes = [
            "divine light shining through clouds",
            "sacred landscape with ethereal atmosphere",
            "biblical landscape with soft light",
            "heavenly clouds with rays of light",
            "peaceful biblical scene with warm light",
            "holy land landscape at sunrise"
        ]
    
    # Базовый промпт с улучшенным качеством
    base_prompt = random.choice([
        f"beautiful {random.choice(themes)}, masterpiece, highly detailed, inspiring wallpaper, spiritual atmosphere, soft light, ethereal, 8k, highly detailed",
        f"stunning {random.choice(themes)}, divine atmosphere, peaceful, cinematic lighting, artstation, conceptual art, smooth, sharp focus",
        f"magnificent {random.choice(themes)}, holy atmosphere, heavenly, god rays, beautiful composition, award winning photograph"
    ])
    
    # Добавляем модификаторы качества
    quality_modifiers = [
        "masterpiece, highly detailed, 8k",
        "trending on artstation, award winning",
        "photorealistic, breathtaking, professional"
    ]
    
    full_prompt = f"{base_prompt}, {random.choice(quality_modifiers)}"
    return full_prompt

def get_image_from_pollinations(prompt):
    """
    Получает изображение от Pollinations.AI
    """
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 100000)
    
    # Добавляем параметры для лучшего качества
    image_url = f"{POLLINATIONS_URL}{encoded_prompt}?width={MOBILE_WIDTH}&height={MOBILE_HEIGHT}&nologo=true&safe=false&seed={seed}&model=flux"
    
    try:
        response = requests.get(image_url, timeout=20)
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
    Создает красивый градиентный фон как запасной вариант
    """
    img = Image.new('RGB', (MOBILE_WIDTH, MOBILE_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Библейские цвета (золотой, пурпурный, синий)
    color_schemes = [
        ((180, 150, 100), (100, 80, 150)),  # золото-фиолетовый
        ((200, 180, 150), (80, 100, 180)),   # песчано-синий
        ((160, 120, 100), (120, 80, 150)),   # терракотово-пурпурный
        ((140, 170, 200), (70, 70, 120)),    # небесно-синий
    ]
    
    color1, color2 = random.choice(color_schemes)
    
    # Создаем радиальный градиент
    center_x, center_y = MOBILE_WIDTH // 2, MOBILE_HEIGHT // 3
    
    for y in range(MOBILE_HEIGHT):
        for x in range(0, MOBILE_WIDTH, 3):  # оптимизация
            # Расстояние до центра
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
    
    # Добавляем легкое свечение
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)
    
    return img

def add_text_to_image(image, text):
    """
    Накладывает текст на изображение с красивым форматированием
    """
    img_with_text = image.copy().convert('RGBA')
    draw = ImageDraw.Draw(img_with_text)
    
    # Пытаемся загрузить красивый шрифт
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/System/Library/Fonts/Times.ttc",
        "C:\\Windows\\Fonts\\times.ttf",
        "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf"
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 90)
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
    
    # Разбиваем текст на строки
    lines = text.split('\n')
    if len(lines) == 1:
        # Если текст одной строкой, разбиваем по словам
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            # Проверяем длину строки
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > MOBILE_WIDTH * 0.7:
                if len(current_line) > 1:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
                else:
                    lines.append(test_line)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
    
    # Получаем размеры каждой строки
    line_heights = []
    line_widths = []
    total_height = 0
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        line_widths.append(width)
        line_heights.append(height)
        total_height += height + 20
    
    total_height -= 20  # убираем последний отступ
    
    # Позиция текста (центр)
    start_y = (MOBILE_HEIGHT - total_height) // 2
    
    # Создаем полупрозрачный фон под текст
    padding = 60
    max_width = max(line_widths)
    
    # Рисуем элегантную подложку
    overlay = Image.new('RGBA', img_with_text.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Основной прямоугольник с градиентной прозрачностью
    overlay_draw.rectangle(
        [(MOBILE_WIDTH - max_width) // 2 - padding, 
         start_y - padding,
         (MOBILE_WIDTH + max_width) // 2 + padding,
         start_y + total_height + padding],
        fill=(0, 0, 0, 160)
    )
    
    # Добавляем золотую линию сверху и снизу для библейских цитат
    if any(word in text.lower() for word in ["господ", "бог", "христ", "иисус", "свят"]):
        line_color = (255, 215, 0, 200)  # золотой
        line_y1 = start_y - padding - 5
        line_y2 = start_y + total_height + padding + 5
        
        overlay_draw.rectangle(
            [(MOBILE_WIDTH - max_width) // 2 - padding - 5, line_y1,
             (MOBILE_WIDTH - max_width) // 2 - padding, line_y2],
            fill=line_color
        )
        overlay_draw.rectangle(
            [(MOBILE_WIDTH + max_width) // 2 + padding, line_y1,
             (MOBILE_WIDTH + max_width) // 2 + padding + 5, line_y2],
            fill=line_color
        )
    
    # Накладываем фон
    img_with_text = Image.alpha_composite(img_with_text, overlay)
    draw = ImageDraw.Draw(img_with_text)
    
    # Рисуем текст
    current_y = start_y
    
    # Определяем, библейская ли цитата
    is_biblical = any(word in text.lower() for word in [
        "господ", "бог", "христ", "иисус", "свят", "библи", 
        "псалом", "евангелие", "матфея", "марка", "луки", "иоанна"
    ])
    
    text_color = (255, 255, 255, 255)  # белый
    
    # Для библейских цитат делаем легкий золотой оттенок
    if is_biblical:
        text_color = (255, 245, 220, 255)  # теплый белый
    
    for i, line in enumerate(lines):
        # Центрируем каждую строку
        x = (MOBILE_WIDTH - line_widths[i]) // 2
        
        # Тонкая тень для объема
        shadow_offset = 3
        draw.text((x + shadow_offset, current_y + shadow_offset), line, 
                 font=font, fill=(0, 0, 0, 100))
        
        # Основной текст
        draw.text((x, current_y), line, font=font, fill=text_color)
        
        current_y += line_heights[i] + 20
    
    return img_with_text.convert('RGB')

@app.get("/")
@app.get("/wallpaper")
async def generate_wallpaper():
    """
    Генерирует мотивационные обои с библейскими цитатами
    """
    try:
        # Получаем цитату
        quote = get_biblical_quote()
        
        # Генерируем промпт для фона на основе цитаты
        prompt = generate_biblical_prompt(quote)
        
        # Получаем изображение
        background = get_image_from_pollinations(prompt)
        
        # Добавляем текст
        final_image = add_text_to_image(background, quote)
        
        # Сохраняем в байты
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=95, optimize=True)
        img_byte_arr.seek(0)
        
        return StreamingResponse(
            img_byte_arr, 
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache",
                "Content-Disposition": "inline; filename=wallpaper.jpg"
            }
        )
        
    except Exception as e:
        print(f"Ошибка: {e}")
        # В случае ошибки возвращаем простую картинку
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
