const CACHE = "bible-wallpaper-v4";

const SHELL = [
  "./",
  "./index.html",
  "./css/style.css",
  "./css/fonts.css",
  "./js/app.js",
  "./js/generator.js",
  "./js/quotes.js",
  "./js/backgrounds.js",
  "./manifest.webmanifest",
  "./icons/icon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => Promise.allSettled(SHELL.map((url) => cache.add(url))))
      .then(() => self.skipWaiting()),
  );
});

async function pruneBackgrounds() {
  try {
    const response = await fetch("backgrounds/manifest.json", { cache: "no-store" });
    if (!response.ok) return;
    const data = await response.json();
    const scope = self.registration.scope;
    const keep = new Set((data.photos || []).map((photo) => new URL(`backgrounds/${photo.file}`, scope).href));
    const cache = await caches.open(CACHE);
    const requests = await cache.keys();
    await Promise.all(
      requests
        .filter((request) => request.url.includes("/backgrounds/") && !keep.has(request.url))
        .map((request) => cache.delete(request)),
    );
  } catch (error) {
    /* офлайн — почистим в следующий раз */
  }
}

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => pruneBackgrounds())
      .then(() => self.clients.claim()),
  );
});

async function networkFirst(request, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackUrl) {
      const fallback = await caches.match(fallbackUrl);
      if (fallback) return fallback;
    }
    throw error;
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok) {
    const cache = await caches.open(CACHE);
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, "./index.html"));
    return;
  }

  if (request.destination === "font" || request.destination === "image") {
    event.respondWith(cacheFirst(request));
    return;
  }

  event.respondWith(networkFirst(request));
});
