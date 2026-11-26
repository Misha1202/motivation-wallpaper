import { renderWallpaper } from "./generator.js";
import { Quotes } from "./quotes.js";
import { Backgrounds } from "./backgrounds.js";

const wallpaper = document.getElementById("wallpaper");
const stage = document.getElementById("stage");
const skeleton = document.getElementById("skeleton");
const refreshButton = document.getElementById("refresh");
const downloadButton = document.getElementById("download");
const shareButton = document.getElementById("share");
const toastElement = document.getElementById("toast");

const quotes = new Quotes();
const backgrounds = new Backgrounds();

let currentBlob = null;
let currentQuote = null;
let busy = false;
let toastTimer = 0;

function toast(message) {
  toastElement.textContent = message;
  toastElement.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastElement.classList.remove("is-visible"), 2600);
}

function fileName() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
  return `bible-wallpaper-${stamp}.jpg`;
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))), "image/jpeg", 0.92);
  });
}

async function refresh({ first = false } = {}) {
  if (busy) return;
  busy = true;
  refreshButton.disabled = true;
  stage.classList.add("is-updating");

  try {
    const quote = quotes.next();
    const prepared = await backgrounds.prepare(backgrounds.next());
    const canvas = renderWallpaper({ quote, background: prepared });
    const blob = await canvasToBlob(canvas);

    const url = URL.createObjectURL(blob);
    const image = new Image();
    image.src = url;
    try {
      await image.decode();
    } catch (error) {
      /* Safari иногда не поддерживает decode() — не критично */
    }

    const previous = wallpaper.src;
    wallpaper.src = url;
    wallpaper.alt = `${quote.text}${quote.ref ? ` — ${quote.ref}` : ""}`;
    if (previous.startsWith("blob:")) setTimeout(() => URL.revokeObjectURL(previous), 4000);

    currentBlob = blob;
    currentQuote = quote;
    shareButton.disabled = !navigator.share;
    backgrounds.warmUp();
  } catch (error) {
    console.error(error);
    toast("Не получилось создать обои — попробуй ещё раз");
  } finally {
    busy = false;
    refreshButton.disabled = false;
    stage.classList.remove("is-updating");
    skeleton.classList.add("is-hidden");
    if (first) document.body.classList.add("is-ready");
  }
}

function download() {
  if (!currentBlob) return;
  const url = URL.createObjectURL(currentBlob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName();
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
  toast("Обои сохранены в загрузки");
}

async function share() {
  if (!currentBlob) return;
  const file = new File([currentBlob], fileName(), { type: "image/jpeg" });
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({
        files: [file],
        title: "Библейские обои",
        text: currentQuote ? `${currentQuote.text}${currentQuote.ref ? ` (${currentQuote.ref})` : ""}` : "",
      });
    } catch (error) {
      if (error.name !== "AbortError") toast("Не удалось поделиться");
    }
  } else {
    toast("Скачай картинку и отправь из галереи");
  }
}

function bindEvents() {
  refreshButton.addEventListener("click", () => refresh());
  downloadButton.addEventListener("click", download);
  shareButton.addEventListener("click", share);

  // Долгое нажатие на картинку = сохранение в галерею, а не смена обоев.
  let pressStartedAt = 0;
  stage.addEventListener("pointerdown", () => {
    pressStartedAt = Date.now();
  });
  stage.addEventListener("click", () => {
    const held = pressStartedAt ? Date.now() - pressStartedAt : 1000;
    pressStartedAt = 0;
    if (held < 650) refresh();
  });

  document.addEventListener("keydown", (event) => {
    if (event.target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(event.target.tagName)) return;
    if ([" ", "Enter", "ArrowRight", "ArrowDown"].includes(event.key)) {
      event.preventDefault();
      refresh();
    }
  });

  let touchStart = null;
  stage.addEventListener(
    "touchstart",
    (event) => {
      if (event.touches.length === 1) {
        touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY, at: Date.now() };
      }
    },
    { passive: true },
  );
  stage.addEventListener(
    "touchend",
    (event) => {
      if (!touchStart) return;
      const touch = event.changedTouches[0];
      const dx = touch.clientX - touchStart.x;
      const dy = touch.clientY - touchStart.y;
      const quick = Date.now() - touchStart.at < 700;
      // Свайп влево/вверх — новые обои; короткий тап обрабатывает click.
      if (quick && (dx < -55 || dy < -55)) {
        event.preventDefault();
        refresh();
      }
      touchStart = null;
    },
    { passive: false },
  );
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  if (location.protocol !== "https:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") return;
  try {
    await navigator.serviceWorker.register("sw.js");
  } catch (error) {
    console.info("Service worker не зарегистрирован", error);
  }
}

async function boot() {
  bindEvents();
  const cyrillic = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя";
  await Promise.allSettled([
    document.fonts.load('700 100px "PT Serif"', cyrillic),
    document.fonts.load('400 50px "PT Serif"', cyrillic),
    document.fonts.ready,
  ]);
  await Promise.allSettled([quotes.load(), backgrounds.load()]);
  await refresh({ first: true });
  registerServiceWorker();
}

boot();
