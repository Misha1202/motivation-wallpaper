#!/usr/bin/env python3
"""Рисует иконки приложения (192/512/180) без внешних зависимостей."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "web" / "icons"


def png(width: int, height: int, pixels: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + pixels[y * width * 3 : (y + 1) * width * 3] for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def mix(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def box_distance(nx: float, ny: float, cx: float, cy: float, half_w: float, half_h: float) -> float:
    dx = max(abs(nx - cx) - half_w, 0.0)
    dy = max(abs(ny - cy) - half_h, 0.0)
    return math.hypot(dx, dy)


def cross_distance(x: float, y: float) -> float:
    """Расстояние до креста в нормированных координатах."""
    vertical = box_distance(x, y, 0.5, 0.51, 0.039, 0.29)
    horizontal = box_distance(x, y, 0.5, 0.385, 0.21, 0.039)
    return min(vertical, horizontal)


def render(size: int) -> bytes:
    data = bytearray()
    for y in range(size):
        ny = y / (size - 1)
        for x in range(size):
            nx = x / (size - 1)
            # Тёмно-синий фон с тёплым свечением сверху.
            radial = min(1.0, math.hypot((nx - 0.5) * 1.05, (ny - 0.3) * 0.9) / 0.85)
            color = mix((24, 31, 52), (7, 7, 11), radial**0.85)
            warm = max(0.0, 1.0 - math.hypot(nx - 0.5, ny - 0.34) / 0.55)
            color = mix(color, (52, 43, 34), 0.35 * warm)

            distance = cross_distance(nx, ny)
            glow = math.exp(-((distance / 0.055) ** 2)) * 0.55
            color = mix(color, (237, 206, 152), min(1.0, glow))
            if distance < 0.0025:
                color = (242, 214, 164)

            # Мягкая виньетка.
            vignette = min(1.0, math.hypot(nx - 0.5, ny - 0.5) / 0.72)
            color = mix(color, (4, 4, 7), 0.35 * vignette**2)

            data.extend(int(max(0, min(255, round(channel)))) for channel in color)
    return bytes(data)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for size in (180, 192, 512):
        target = OUT_DIR / f"icon-{size}.png"
        target.write_bytes(png(size, size, render(size)))
        print(f"✅ {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
