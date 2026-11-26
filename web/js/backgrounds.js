// Источник фонов: фото из backgrounds/manifest.json + процедурные стили.
// Фото готовятся GitHub Actions, но сайт полностью работает и без них.

const STYLES = ["night", "aurora", "dusk", "ocean", "forest", "bokeh"];
const PHOTO_TIMEOUT = 15000;

function shuffle(items) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

const randomStyle = () => STYLES[Math.floor(Math.random() * STYLES.length)];

export class Backgrounds {
  constructor(base = "backgrounds/") {
    this.base = base;
    this.photos = [];
    this.deck = [];
    this.index = 0;
    this.lastPhoto = null;
    this.ready = false;
    this.loaded = new Set();
  }

  async load() {
    try {
      const response = await fetch(`${this.base}manifest.json`, { cache: "no-cache" });
      if (response.ok) {
        const data = await response.json();
        this.photos = (data.photos || []).filter((photo) => photo && photo.file);
      }
    } catch (error) {
      console.info("Фото недоступны, работаю на процедурных фонах", error);
    }
    this.ready = true;
    this.buildDeck();
    return this.photos.length;
  }

  buildDeck() {
    const items = this.photos.map((photo) => ({ kind: "photo", ...photo }));
    // Разбавляем фотографии процедурными фонами, чтобы набор не приедался.
    const proceduralCount = items.length ? Math.max(3, Math.round(items.length / 3)) : 8;
    for (let i = 0; i < proceduralCount; i += 1) {
      items.push({ kind: "procedural", style: randomStyle() });
    }
    this.deck = shuffle(items);
    this.index = 0;
    if (this.deck.length > 1 && this.deck[0].file && this.deck[0].file === this.lastPhoto) {
      const swapIndex = 1 + Math.floor(Math.random() * (this.deck.length - 1));
      [this.deck[0], this.deck[swapIndex]] = [this.deck[swapIndex], this.deck[0]];
    }
  }

  next() {
    if (!this.ready) return { kind: "procedural", style: randomStyle() };
    if (!this.deck.length || this.index >= this.deck.length) this.buildDeck();
    const item = this.deck[this.index];
    this.index += 1;
    if (item.kind === "photo") this.lastPhoto = item.file;
    return item;
  }

  loadImage(file) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.decoding = "async";
      const timer = setTimeout(() => reject(new Error("timeout")), PHOTO_TIMEOUT);
      image.onload = () => {
        clearTimeout(timer);
        resolve(image);
      };
      image.onerror = () => {
        clearTimeout(timer);
        reject(new Error(`Не загрузилось: ${file}`));
      };
      image.src = `${this.base}${file}`;
    });
  }

  async prepare(item) {
    if (!item || item.kind !== "photo") {
      return { kind: "procedural", style: (item && item.style) || randomStyle() };
    }
    try {
      const image = await this.loadImage(item.file);
      return { kind: "photo", image, meta: item };
    } catch (error) {
      console.info(error.message);
      return { kind: "procedural", style: randomStyle() };
    }
  }

  /** Подгружает следующее фото заранее, чтобы «Новые обои» срабатывали мгновенно. */
  warmUp() {
    const upcoming = this.deck[this.index];
    if (upcoming && upcoming.kind === "photo" && !this.loaded.has(upcoming.file)) {
      this.loaded.add(upcoming.file);
      this.loadImage(upcoming.file).catch(() => {});
    }
  }
}
