// Генерация обоев 1170×2532 полностью в браузере.
// Никакого сервера: цитата + фон -> canvas -> JPEG.

export const WIDTH = 1170;
export const HEIGHT = 2532;

const FONT_STACK = '"PT Serif", "Liberation Serif", "DejaVu Serif", Georgia, serif';
const GOLD = "rgba(231, 200, 145, 0.92)";

// ---------------------------------------------------------------- утилиты

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function random() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = (rng, min, max) => min + rng() * (max - min);
const pick = (rng, items) => items[Math.min(items.length - 1, Math.floor(rng() * items.length))];

function gradient(ctx, x0, y0, x1, y1, stops) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  for (const [offset, color] of stops) g.addColorStop(offset, color);
  return g;
}

function radial(ctx, x, y, r0, r1, stops) {
  const g = ctx.createRadialGradient(x, y, r0, x, y, r1);
  for (const [offset, color] of stops) g.addColorStop(offset, color);
  return g;
}

function ridge(ctx, baseY, amplitude, phase, step = 12) {
  ctx.beginPath();
  ctx.moveTo(0, HEIGHT);
  for (let x = 0; x <= WIDTH + step; x += step) {
    const wave =
      Math.sin(x / 260 + phase) * amplitude +
      Math.sin(x / 97 + phase * 2.3) * amplitude * 0.35 +
      Math.sin(x / 41 + phase * 0.7) * amplitude * 0.12;
    ctx.lineTo(x, baseY + wave);
  }
  ctx.lineTo(WIDTH, HEIGHT);
  ctx.closePath();
}

// ---------------------------------------------------------------- фон: фото

const TONES = ["#1c2b4a", "#3a2a1c", "#0f3034", "#2b2040", "#3b2226", "#1f3340"];

function drawPhoto(ctx, image, rng) {
  const naturalWidth = image.naturalWidth || image.width;
  const naturalHeight = image.naturalHeight || image.height;
  if (!naturalWidth || !naturalHeight) return false;

  const cover = Math.max(WIDTH / naturalWidth, HEIGHT / naturalHeight);
  const scale = cover * rand(rng, 1.02, 1.2);
  const width = naturalWidth * scale;
  const height = naturalHeight * scale;
  const x = (WIDTH - width) * rand(rng, 0.25, 0.75);
  const y = (HEIGHT - height) * rand(rng, 0.2, 0.8);
  const flipped = rng() < 0.5;

  ctx.save();
  if (flipped) {
    ctx.translate(WIDTH, 0);
    ctx.scale(-1, 1);
  }
  ctx.drawImage(image, x, y, width, height);
  ctx.restore();

  // Мягкая цветокоррекция и затемнение под текст.
  ctx.save();
  ctx.globalCompositeOperation = "soft-light";
  ctx.globalAlpha = rand(rng, 0.45, 0.8);
  ctx.fillStyle = pick(rng, TONES);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.restore();

  ctx.save();
  ctx.fillStyle = `rgba(5, 7, 13, ${rand(rng, 0.22, 0.4).toFixed(3)})`;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.restore();
  return true;
}

// ---------------------------------------------------------------- фон: процедурный

const STYLES = ["night", "aurora", "dusk", "ocean", "forest", "bokeh"];

function drawStars(ctx, rng, count, region = [0, 0, WIDTH, HEIGHT * 0.9]) {
  const [rx, ry, rw, rh] = region;
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  for (let i = 0; i < count; i += 1) {
    const x = rand(rng, rx, rx + rw);
    const y = rand(rng, ry, ry + rh);
    const radius = rand(rng, 0.6, 2.1);
    const alpha = rand(rng, 0.18, 0.85);
    ctx.fillStyle = `rgba(255, 250, 235, ${alpha.toFixed(3)})`;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawNight(ctx, rng) {
  ctx.fillStyle = gradient(ctx, 0, 0, 0, HEIGHT, [
    [0, "#05070f"],
    [0.45, "#0b1428"],
    [0.72, "#15223c"],
    [1, "#060a14"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  // Млечный путь — полоса мягких пятен.
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  ctx.translate(WIDTH * 0.5, HEIGHT * 0.4);
  ctx.rotate(-0.42);
  for (let i = 0; i < 16; i += 1) {
    const x = rand(rng, -320, 320);
    const y = rand(rng, -WIDTH * 0.55, WIDTH * 0.55);
    const r = rand(rng, 180, 460);
    ctx.fillStyle = radial(ctx, x, y, 0, r, [
      [0, `rgba(150, 170, 235, ${rand(rng, 0.04, 0.1).toFixed(3)})`],
      [1, "rgba(150, 170, 235, 0)"],
    ]);
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();

  drawStars(ctx, rng, 520, [0, 0, WIDTH, HEIGHT * 0.82]);

  // Луна с ореолом.
  const moonX = rand(rng, WIDTH * 0.2, WIDTH * 0.8);
  const moonY = rand(rng, HEIGHT * 0.12, HEIGHT * 0.3);
  const moonR = rand(rng, 46, 74);
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  ctx.fillStyle = radial(ctx, moonX, moonY, moonR * 0.6, moonR * 5.2, [
    [0, "rgba(255, 246, 220, 0.32)"],
    [0.35, "rgba(255, 240, 205, 0.08)"],
    [1, "rgba(255, 240, 205, 0)"],
  ]);
  ctx.fillRect(moonX - moonR * 6, moonY - moonR * 6, moonR * 12, moonR * 12);
  ctx.fillStyle = "rgba(255, 249, 232, 0.93)";
  ctx.beginPath();
  ctx.arc(moonX, moonY, moonR, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // Дальние горы.
  ctx.fillStyle = "rgba(4, 7, 13, 0.82)";
  ridge(ctx, HEIGHT * 0.86, 46, rand(rng, 0, Math.PI * 2));
  ctx.fill();
  ctx.fillStyle = "rgba(2, 4, 9, 0.95)";
  ridge(ctx, HEIGHT * 0.93, 70, rand(rng, 0, Math.PI * 2));
  ctx.fill();
}

function drawAurora(ctx, rng) {
  ctx.fillStyle = gradient(ctx, 0, 0, 0, HEIGHT, [
    [0, "#04060d"],
    [0.5, "#081121"],
    [0.8, "#0a1a24"],
    [1, "#03050a"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const colors = ["94, 234, 212", "129, 140, 248", "244, 114, 182", "52, 211, 153", "167, 139, 250"];
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  for (let i = 0; i < 11; i += 1) {
    const x = rand(rng, -WIDTH * 0.15, WIDTH * 1.15);
    const y = rand(rng, HEIGHT * 0.08, HEIGHT * 0.62);
    const r = rand(rng, 360, 920);
    const color = pick(rng, colors);
    ctx.fillStyle = radial(ctx, x, y, 0, r, [
      [0, `rgba(${color}, ${rand(rng, 0.1, 0.22).toFixed(3)})`],
      [0.55, `rgba(${color}, ${rand(rng, 0.03, 0.08).toFixed(3)})`],
      [1, `rgba(${color}, 0)`],
    ]);
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();

  drawStars(ctx, rng, 300, [0, 0, WIDTH, HEIGHT * 0.55]);

  ctx.fillStyle = gradient(ctx, 0, HEIGHT * 0.72, 0, HEIGHT, [
    [0, "rgba(3, 5, 10, 0)"],
    [1, "rgba(3, 5, 10, 0.85)"],
  ]);
  ctx.fillRect(0, HEIGHT * 0.72, WIDTH, HEIGHT * 0.28);
}

function drawMountainLayers(ctx, rng, horizon) {
  const layers = [
    { y: horizon + 40, amp: 55, color: "rgba(24, 26, 48, 0.85)" },
    { y: horizon + 130, amp: 80, color: "rgba(15, 16, 32, 0.92)" },
    { y: horizon + 250, amp: 110, color: "rgba(8, 9, 18, 0.97)" },
    { y: horizon + 430, amp: 140, color: "#04050a" },
  ];
  for (const layer of layers) {
    ctx.fillStyle = layer.color;
    ridge(ctx, layer.y, layer.amp, rand(rng, 0, Math.PI * 2));
    ctx.fill();
  }
}

function drawDusk(ctx, rng) {
  const horizon = HEIGHT * 0.7;
  ctx.fillStyle = gradient(ctx, 0, 0, 0, horizon + 40, [
    [0, "#050710"],
    [0.32, "#141a38"],
    [0.58, "#4b2b4d"],
    [0.8, "#a85a43"],
    [1, "#e9a562"],
  ]);
  ctx.fillRect(0, 0, WIDTH, horizon + 40);

  const sunX = rand(rng, WIDTH * 0.3, WIDTH * 0.7);
  const sunY = horizon - rand(rng, 40, 120);
  const sunR = rand(rng, 70, 110);
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  ctx.fillStyle = radial(ctx, sunX, sunY, sunR * 0.4, sunR * 6.5, [
    [0, "rgba(255, 226, 178, 0.55)"],
    [0.3, "rgba(255, 180, 120, 0.18)"],
    [1, "rgba(255, 170, 110, 0)"],
  ]);
  ctx.fillRect(sunX - sunR * 7, sunY - sunR * 7, sunR * 14, sunR * 14);
  ctx.fillStyle = radial(ctx, sunX, sunY, 0, sunR, [
    [0, "rgba(255, 245, 220, 1)"],
    [0.7, "rgba(255, 220, 165, 0.98)"],
    [1, "rgba(255, 205, 140, 0.9)"],
  ]);
  ctx.beginPath();
  ctx.arc(sunX, sunY, sunR, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // Дымка у горизонта.
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  ctx.fillStyle = gradient(ctx, 0, horizon - 220, 0, horizon + 80, [
    [0, "rgba(255, 190, 140, 0)"],
    [0.65, "rgba(255, 190, 140, 0.12)"],
    [1, "rgba(255, 200, 150, 0)"],
  ]);
  ctx.fillRect(0, horizon - 220, WIDTH, 300);
  ctx.restore();

  drawMountainLayers(ctx, rng, horizon);
}

function drawOcean(ctx, rng) {
  const horizon = HEIGHT * 0.62;
  ctx.fillStyle = gradient(ctx, 0, 0, 0, horizon, [
    [0, "#060a16"],
    [0.42, "#182744"],
    [0.75, "#4c556e"],
    [1, "#a4787a"],
  ]);
  ctx.fillRect(0, 0, WIDTH, horizon);

  const sunX = rand(rng, WIDTH * 0.3, WIDTH * 0.7);
  const sunY = horizon - rand(rng, 30, 90);
  const sunR = rand(rng, 58, 90);
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  ctx.fillStyle = radial(ctx, sunX, sunY, sunR * 0.3, sunR * 5.5, [
    [0, "rgba(255, 226, 180, 0.5)"],
    [0.4, "rgba(255, 190, 140, 0.12)"],
    [1, "rgba(255, 190, 140, 0)"],
  ]);
  ctx.fillRect(sunX - sunR * 6, sunY - sunR * 6, sunR * 12, sunR * 12);
  ctx.fillStyle = "rgba(255, 244, 218, 0.95)";
  ctx.beginPath();
  ctx.arc(sunX, sunY, sunR, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // Море.
  ctx.fillStyle = gradient(ctx, 0, horizon, 0, HEIGHT, [
    [0, "#101b30"],
    [0.35, "#0a1220"],
    [1, "#04070d"],
  ]);
  ctx.fillRect(0, horizon, WIDTH, HEIGHT - horizon);

  // Лунная/солнечная дорожка.
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  for (let i = 0; i < 70; i += 1) {
    const t = i / 70;
    const y = horizon + t * (HEIGHT - horizon) * 0.9 + rand(rng, 0, 4);
    const spread = 30 + t * 260;
    const w = rand(rng, 18, 90) * (1 - t * 0.55);
    ctx.fillStyle = `rgba(255, 215, 170, ${(0.3 * (1 - t)).toFixed(3)})`;
    ctx.beginPath();
    ctx.ellipse(sunX + rand(rng, -spread, spread), y, w, rand(rng, 1, 4), 0, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();

  // Волны.
  ctx.save();
  ctx.strokeStyle = "rgba(190, 210, 240, 0.06)";
  ctx.lineWidth = 2;
  for (let i = 0; i < 24; i += 1) {
    const y = horizon + rand(rng, 20, HEIGHT - horizon - 40);
    const w = rand(rng, 120, 420);
    const x = rand(rng, 0, WIDTH - w);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + w / 2, y - rand(rng, 3, 8), x + w, y);
    ctx.stroke();
  }
  ctx.restore();
}

function drawForest(ctx, rng) {
  ctx.fillStyle = gradient(ctx, 0, 0, 0, HEIGHT, [
    [0, "#071410"],
    [0.38, "#0d241d"],
    [0.7, "#123128"],
    [1, "#050b09"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  // Светящийся туман.
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  const lightX = rand(rng, WIDTH * 0.25, WIDTH * 0.75);
  ctx.fillStyle = radial(ctx, lightX, HEIGHT * 0.3, 0, WIDTH * 0.9, [
    [0, "rgba(210, 235, 200, 0.2)"],
    [0.5, "rgba(180, 220, 190, 0.05)"],
    [1, "rgba(180, 220, 190, 0)"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.restore();

  // Лучи.
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  for (let i = 0; i < 5; i += 1) {
    const x = lightX + rand(rng, -260, 260);
    const width = rand(rng, 70, 200);
    ctx.fillStyle = gradient(ctx, 0, 0, 0, HEIGHT, [
      [0, `rgba(220, 240, 200, ${rand(rng, 0.04, 0.1).toFixed(3)})`],
      [0.75, "rgba(220, 240, 200, 0)"],
    ]);
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x + width, 0);
    ctx.lineTo(x + width + rand(rng, 180, 420), HEIGHT);
    ctx.lineTo(x + rand(rng, 120, 360), HEIGHT);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();

  // Слои тумана.
  for (const [offset, alpha] of [[0.5, 0.05], [0.62, 0.07], [0.74, 0.05]]) {
    ctx.fillStyle = gradient(ctx, 0, HEIGHT * offset - 120, 0, HEIGHT * offset + 120, [
      [0, "rgba(190, 220, 205, 0)"],
      [0.5, `rgba(190, 220, 205, ${alpha})`],
      [1, "rgba(190, 220, 205, 0)"],
    ]);
    ctx.fillRect(0, HEIGHT * offset - 120, WIDTH, 240);
  }

  // Холмы.
  const layers = [
    { y: HEIGHT * 0.72, amp: 50, color: "rgba(14, 40, 32, 0.8)" },
    { y: HEIGHT * 0.8, amp: 70, color: "rgba(9, 28, 23, 0.9)" },
    { y: HEIGHT * 0.89, amp: 90, color: "rgba(5, 17, 14, 0.96)" },
    { y: HEIGHT * 0.97, amp: 120, color: "#020705" },
  ];
  for (const layer of layers) {
    ctx.fillStyle = layer.color;
    ridge(ctx, layer.y, layer.amp, rand(rng, 0, Math.PI * 2));
    ctx.fill();
  }

  // Ели на ближнем слое.
  ctx.fillStyle = "rgba(2, 8, 6, 0.9)";
  for (let i = 0; i < 42; i += 1) {
    const x = rand(rng, -40, WIDTH + 40);
    const baseY = HEIGHT * rand(rng, 0.9, 1.02);
    const height = rand(rng, 120, 420);
    const width = height * rand(rng, 0.22, 0.34);
    ctx.beginPath();
    ctx.moveTo(x, baseY - height);
    ctx.lineTo(x + width / 2, baseY);
    ctx.lineTo(x - width / 2, baseY);
    ctx.closePath();
    ctx.fill();
  }
}

function drawBokeh(ctx, rng) {
  ctx.fillStyle = gradient(ctx, 0, 0, 0, HEIGHT, [
    [0, "#0a0812"],
    [0.5, "#151024"],
    [1, "#05040a"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const colors = ["232, 197, 145", "180, 160, 240", "150, 210, 210", "230, 150, 160"];
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  for (let i = 0; i < 26; i += 1) {
    const x = rand(rng, 0, WIDTH);
    const y = rand(rng, HEIGHT * 0.05, HEIGHT * 0.8);
    const r = rand(rng, 50, 300);
    const color = pick(rng, colors);
    ctx.fillStyle = radial(ctx, x, y, r * 0.1, r, [
      [0, `rgba(${color}, ${rand(rng, 0.12, 0.3).toFixed(3)})`],
      [0.6, `rgba(${color}, ${rand(rng, 0.04, 0.1).toFixed(3)})`],
      [1, `rgba(${color}, 0)`],
    ]);
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();
}

function drawProcedural(ctx, style, rng) {
  switch (style) {
    case "aurora":
      drawAurora(ctx, rng);
      break;
    case "dusk":
      drawDusk(ctx, rng);
      break;
    case "ocean":
      drawOcean(ctx, rng);
      break;
    case "forest":
      drawForest(ctx, rng);
      break;
    case "bokeh":
      drawBokeh(ctx, rng);
      break;
    default:
      drawNight(ctx, rng);
  }
}

// ---------------------------------------------------------------- атмосфера

function drawAtmosphere(ctx, rng) {
  // Мягкий щит под текстом: держит контраст на светлых фонах.
  ctx.save();
  ctx.fillStyle = radial(ctx, WIDTH * 0.5, HEIGHT * 0.6, HEIGHT * 0.02, HEIGHT * 0.36, [
    [0, "rgba(3, 4, 8, 0.42)"],
    [0.55, "rgba(3, 4, 8, 0.28)"],
    [1, "rgba(3, 4, 8, 0)"],
  ]);
  ctx.fillRect(0, HEIGHT * 0.2, WIDTH, HEIGHT * 0.8);
  ctx.restore();

  // Лёгкая виньетка.
  ctx.save();
  ctx.fillStyle = radial(ctx, WIDTH * 0.5, HEIGHT * 0.42, HEIGHT * 0.12, HEIGHT * 0.78, [
    [0, "rgba(0, 0, 0, 0)"],
    [0.62, "rgba(0, 0, 0, 0.12)"],
    [1, "rgba(0, 0, 0, 0.55)"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.restore();

  // Затемнение сверху (статус-бар) и снизу (текст).
  ctx.save();
  ctx.fillStyle = gradient(ctx, 0, 0, 0, HEIGHT * 0.16, [
    [0, "rgba(0, 0, 0, 0.4)"],
    [1, "rgba(0, 0, 0, 0)"],
  ]);
  ctx.fillRect(0, 0, WIDTH, HEIGHT * 0.16);
  ctx.fillStyle = gradient(ctx, 0, HEIGHT * 0.42, 0, HEIGHT, [
    [0, "rgba(0, 0, 0, 0)"],
    [0.45, "rgba(0, 0, 0, 0.18)"],
    [1, "rgba(0, 0, 0, 0.52)"],
  ]);
  ctx.fillRect(0, HEIGHT * 0.42, WIDTH, HEIGHT * 0.58);
  ctx.restore();
}

let grainTile = null;
function getGrainTile() {
  if (grainTile) return grainTile;
  const size = 140;
  const tile = document.createElement("canvas");
  tile.width = size;
  tile.height = size;
  const ctx = tile.getContext("2d");
  const data = ctx.createImageData(size, size);
  for (let i = 0; i < data.data.length; i += 4) {
    const value = 90 + Math.random() * 120;
    data.data[i] = value;
    data.data[i + 1] = value;
    data.data[i + 2] = value;
    data.data[i + 3] = 255;
  }
  ctx.putImageData(data, 0, 0);
  grainTile = tile;
  return tile;
}

function drawGrain(ctx) {
  ctx.save();
  ctx.globalAlpha = 0.05;
  ctx.globalCompositeOperation = "overlay";
  ctx.fillStyle = ctx.createPattern(getGrainTile(), "repeat");
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.restore();
}

// ---------------------------------------------------------------- текст

function wrapLines(ctx, text, maxWidth) {
  const lines = [];
  for (const paragraph of text.split(/\n+/)) {
    const words = paragraph.split(/\s+/).filter(Boolean);
    let line = "";
    for (const word of words) {
      const candidate = line ? `${line} ${word}` : word;
      if (ctx.measureText(candidate).width <= maxWidth) {
        line = candidate;
        continue;
      }
      if (line) {
        lines.push(line);
        line = "";
      }
      if (ctx.measureText(word).width > maxWidth) {
        let chunk = "";
        for (const char of Array.from(word)) {
          if (chunk && ctx.measureText(chunk + char).width > maxWidth) {
            lines.push(chunk);
            chunk = char;
          } else {
            chunk += char;
          }
        }
        line = chunk;
      } else {
        line = word;
      }
    }
    if (line) lines.push(line);
  }
  return lines;
}

function layoutQuote(ctx, text, hasRef) {
  const maxWidth = WIDTH - 210;
  const maxBlock = HEIGHT * 0.5;
  let size = 112;
  const minSize = 54;
  let lines = [];
  let lineHeight = 0;
  let refSize = 0;
  let gap = 0;
  let blockHeight = 0;

  for (;;) {
    ctx.font = `700 ${size}px ${FONT_STACK}`;
    lines = wrapLines(ctx, text, maxWidth);
    lineHeight = Math.round(size * 1.27);
    refSize = Math.round(Math.max(38, size * 0.4));
    gap = Math.round(size * 0.6);
    blockHeight = lines.length * lineHeight + (hasRef ? gap + refSize : 0);
    if (blockHeight <= maxBlock || size <= minSize) break;
    size -= 2;
  }

  return { size, lines, lineHeight, refSize, gap, blockHeight };
}

function capitalizeFirst(text) {
  const index = text.search(/[a-zа-яё]/i);
  if (index === -1) return text;
  const char = text[index];
  if (char !== char.toLowerCase()) return text;
  return text.slice(0, index) + char.toUpperCase() + text.slice(index + 1);
}

function drawQuote(ctx, quote, rng) {
  const text = capitalizeFirst((quote.text || "").trim());
  if (!text) return;
  const ref = (quote.ref || "").trim();

  const layout = layoutQuote(ctx, text, Boolean(ref));
  const centerY = HEIGHT * (quote.centerY || 0.605);
  const startY = centerY - layout.blockHeight / 2;

  // Тонкая золотая линия над цитатой.
  ctx.save();
  ctx.fillStyle = GOLD;
  ctx.fillRect(WIDTH / 2 - 34, startY - 58, 68, 3);
  ctx.restore();

  ctx.save();
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.font = `700 ${layout.size}px ${FONT_STACK}`;
  ctx.fillStyle = "rgba(255, 253, 247, 0.97)";
  ctx.shadowColor = "rgba(0, 0, 0, 0.55)";
  ctx.shadowBlur = 24;
  ctx.shadowOffsetY = 5;

  let y = startY;
  for (const line of layout.lines) {
    ctx.fillText(line, WIDTH / 2, y);
    y += layout.lineHeight;
  }
  ctx.restore();

  if (ref) {
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.font = `400 ${layout.refSize}px ${FONT_STACK}`;
    ctx.fillStyle = "rgba(236, 226, 206, 0.8)";
    ctx.shadowColor = "rgba(0, 0, 0, 0.5)";
    ctx.shadowBlur = 14;
    ctx.shadowOffsetY = 3;
    try {
      ctx.letterSpacing = "1.5px";
    } catch (error) {
      /* не во всех браузерах */
    }
    ctx.fillText(`— ${ref}`, WIDTH / 2, y + Math.round(layout.gap * 0.45));
    ctx.restore();
  }
}

// ---------------------------------------------------------------- сборка

export function renderWallpaper({ quote, background, seed = Date.now() }) {
  const rng = mulberry32(seed);
  const canvas = document.createElement("canvas");
  canvas.width = WIDTH;
  canvas.height = HEIGHT;
  const ctx = canvas.getContext("2d", { alpha: false });

  ctx.fillStyle = "#07070b";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  let drawn = false;
  if (background && background.kind === "photo" && background.image) {
    drawn = drawPhoto(ctx, background.image, rng);
  }
  if (!drawn) {
    drawProcedural(ctx, (background && background.style) || pick(rng, STYLES), rng);
  }

  drawAtmosphere(ctx, rng);
  drawQuote(ctx, quote, rng);
  drawGrain(ctx);
  return canvas;
}
