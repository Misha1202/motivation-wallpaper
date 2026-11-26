# Библейские обои

Генератор обоев для телефона: при каждом обновлении — новая библейская цитата
и новый фон. Работает на GitHub Pages, картинка собирается прямо в браузере
через Canvas, сервер не нужен.

**Сайт:** https://misha1202.github.io/motivation-wallpaper/

## Почему не Render

Старая версия была FastAPI-сервером: на каждый запрос скрапила azbyka.ru,
дёргала Unsplash и рисовала JPEG через Pillow. На бесплатном Render инстанс
засыпал, запросы падали по таймауту, а ключ Unsplash лежал в открытом коде.
Теперь:

- вся отрисовка — в браузере, мгновенно и без cold start;
- 5300+ цитат собраны заранее и лежат в `web/quotes.json`;
- 60 фото приезжают в артефакт при деплое (в git не хранятся);
- если фото не загрузились, включаются процедурные фоны — сайт не ломается;
- ключ Unsplash больше не нужен клиенту.

## Структура

```
web/                     статический сайт (это и есть Pages)
  index.html
  css/style.css          оформление
  css/fonts.css          @font-face (PT Serif, локально)
  js/generator.js        Canvas: фоны, текст, JPEG
  js/quotes.js           колода цитат без повторов
  js/backgrounds.js      фото + процедурные фоны
  js/app.js              UI, скачивание, шеринг, service worker
  quotes.json            5300+ цитат (собирается скриптом)
  backgrounds/           manifest.json + фото (фото — только в артефакте)
  sw.js                  офлайн-кеш
tools/
  fetch_quotes.py        парсер azbyka.ru → quotes.json
  fetch_backgrounds.py   Unsplash → web/backgrounds/*.jpg
  fetch_fonts.py         PT Serif → web/fonts/
  make_icons.py          иконки PWA
.github/workflows/
  pages.yml              сборка и деплой на Pages
  refresh-quotes.yml     еженедельное обновление цитат
main.py, render.yaml     старая версия на Render (легаси, не используется)
```

## Локальный запуск

```bash
cd web
python3 -m http.server 8765
# открыть http://127.0.0.1:8765
```

Без `backgrounds/*.jpg` сайт работает на процедурных фонах — это нормально.

## Обновление контента

```bash
# цитаты (инкрементально, докачивает только новое)
python3 tools/fetch_quotes.py --workers 4

# фото (нужен ключ Unsplash)
UNSPLASH_ACCESS_KEY=... python3 tools/fetch_backgrounds.py --count 60
```

## Деплой

Push в `main` → GitHub Actions собирает `web/` и публикует на Pages.
Раз в неделю workflow сам обновляет цитаты и пересобирает фото.

Секрет `UNSPLASH_ACCESS_KEY` (Settings → Secrets and variables → Actions)
необязателен: без него сайт останется на процедурных фонах.

## Управление

- тап по картинке, свайп влево/вверх или пробел — новые обои;
- кнопка со стрелкой — скачать JPEG 1170×2532;
- кнопка «поделиться» — отправить в мессенджер (где поддерживается);
- на телефоне можно удерживать картинку и сохранить в галерею;
- сайт устанавливается как PWA и работает офлайн (цитаты и шрифты кешируются).
