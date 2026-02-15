#!/usr/bin/env python3
"""
Generate favicon.ico with embedded PNG images (256/128/64/48/32/16).
No external dependencies (no Pillow).
"""

from __future__ import annotations

import os
import struct
import zlib
from typing import Iterable, List, Sequence, Tuple


RGBA = Tuple[int, int, int, int]


def clamp8(x: int) -> int:
    return 0 if x < 0 else 255 if x > 255 else x


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix(c1: RGBA, c2: RGBA, t: float) -> RGBA:
    r = int(lerp(c1[0], c2[0], t))
    g = int(lerp(c1[1], c2[1], t))
    b = int(lerp(c1[2], c2[2], t))
    a = int(lerp(c1[3], c2[3], t))
    return (r, g, b, a)


def over(dst: RGBA, src: RGBA) -> RGBA:
    """Alpha-composite src over dst (both straight alpha)."""
    sr, sg, sb, sa = src
    dr, dg, db, da = dst
    sa_f = sa / 255.0
    da_f = da / 255.0
    out_a = sa_f + da_f * (1.0 - sa_f)
    if out_a <= 1e-9:
        return (0, 0, 0, 0)
    out_r = (sr * sa_f + dr * da_f * (1.0 - sa_f)) / out_a
    out_g = (sg * sa_f + dg * da_f * (1.0 - sa_f)) / out_a
    out_b = (sb * sa_f + db * da_f * (1.0 - sa_f)) / out_a
    return (int(out_r + 0.5), int(out_g + 0.5), int(out_b + 0.5), int(out_a * 255 + 0.5))


def make_canvas(n: int, fill: RGBA = (0, 0, 0, 0)) -> List[int]:
    return [fill[0], fill[1], fill[2], fill[3]] * (n * n)


def set_px(img: List[int], n: int, x: int, y: int, c: RGBA) -> None:
    i = (y * n + x) * 4
    img[i] = c[0]
    img[i + 1] = c[1]
    img[i + 2] = c[2]
    img[i + 3] = c[3]


def get_px(img: Sequence[int], n: int, x: int, y: int) -> RGBA:
    i = (y * n + x) * 4
    return (img[i], img[i + 1], img[i + 2], img[i + 3])


def fill_rect(img: List[int], n: int, x0: int, y0: int, x1: int, y1: int, c: RGBA) -> None:
    x0 = max(0, min(n, x0))
    y0 = max(0, min(n, y0))
    x1 = max(0, min(n, x1))
    y1 = max(0, min(n, y1))
    if x1 <= x0 or y1 <= y0:
        return
    for y in range(y0, y1):
        row = (y * n + x0) * 4
        for _ in range(x0, x1):
            img[row] = c[0]
            img[row + 1] = c[1]
            img[row + 2] = c[2]
            img[row + 3] = c[3]
            row += 4


def fill_rect_over(img: List[int], n: int, x0: int, y0: int, x1: int, y1: int, c: RGBA) -> None:
    x0 = max(0, min(n, x0))
    y0 = max(0, min(n, y0))
    x1 = max(0, min(n, x1))
    y1 = max(0, min(n, y1))
    if x1 <= x0 or y1 <= y0:
        return
    for y in range(y0, y1):
        for x in range(x0, x1):
            dst = get_px(img, n, x, y)
            set_px(img, n, x, y, over(dst, c))


def draw_icon_base(n: int) -> List[int]:
    # Palette tuned to match site feel.
    bg0 = (7, 11, 26, 255)
    bg1 = (11, 18, 48, 255)
    cyan = (105, 255, 226, 255)
    amber = (255, 194, 94, 255)
    periwinkle = (138, 152, 255, 255)

    img = make_canvas(n, bg0)

    # Background gradient with a few radial "glows".
    cx1, cy1 = int(n * 0.22), int(n * 0.20)
    cx2, cy2 = int(n * 0.82), int(n * 0.22)
    cx3, cy3 = int(n * 0.52), int(n * 0.84)
    r1 = n * 0.78
    r2 = n * 0.72
    r3 = n * 0.82

    for y in range(n):
        t = y / max(1, (n - 1))
        base = mix(bg0, bg1, t)
        for x in range(n):
            c = base

            def glow(cx: int, cy: int, rr: float, col: RGBA, strength: float) -> RGBA:
                dx = x - cx
                dy = y - cy
                d = (dx * dx + dy * dy) ** 0.5
                tt = 1.0 - min(1.0, d / rr)
                a = int(255 * (tt * tt) * strength)
                return (col[0], col[1], col[2], a)

            c = over(c, glow(cx1, cy1, r1, cyan, 0.16))
            c = over(c, glow(cx2, cy2, r2, amber, 0.14))
            c = over(c, glow(cx3, cy3, r3, periwinkle, 0.12))
            set_px(img, n, x, y, c)

    # "E" mark (simple geometry) with subtle shadow.
    # Coordinates are relative to size.
    pad = int(n * 0.18)
    stroke = max(2, int(n * 0.08))
    bar_h = max(2, int(n * 0.11))
    gap = max(2, int(n * 0.07))

    x0 = pad
    y0 = pad
    x1 = n - pad
    y1 = n - pad

    # Shadow (soft-ish via two passes).
    shadow = (0, 0, 0, 120)
    shadow2 = (0, 0, 0, 70)
    ox = max(1, int(n * 0.02))
    oy = max(1, int(n * 0.03))

    def draw_E(offset_x: int, offset_y: int, col: RGBA) -> None:
        # Vertical stem.
        fill_rect_over(img, n, x0 + offset_x, y0 + offset_y, x0 + stroke + offset_x, y1 + offset_y, col)
        # Top bar.
        fill_rect_over(img, n, x0 + offset_x, y0 + offset_y, x1 + offset_x, y0 + bar_h + offset_y, col)
        # Middle bar.
        my0 = y0 + bar_h + gap
        fill_rect_over(img, n, x0 + offset_x, my0 + offset_y, x0 + int((x1 - x0) * 0.78) + offset_x, my0 + bar_h + offset_y, col)
        # Bottom bar.
        by1 = y1
        fill_rect_over(img, n, x0 + offset_x, by1 - bar_h + offset_y, x1 + offset_x, by1 + offset_y, col)

    draw_E(ox, oy, shadow)
    draw_E(ox // 2, oy // 2, shadow2)

    # Main "E" with slight top highlight.
    white = (245, 247, 255, 240)
    highlight = (255, 255, 255, 90)
    draw_E(0, 0, white)
    fill_rect_over(img, n, x0, y0, x1, y0 + max(1, bar_h // 3), highlight)

    # Tiny corner cut for a more "tool" vibe.
    cut = max(1, int(n * 0.05))
    for y in range(cut):
        for x in range(cut - y):
            set_px(img, n, n - 1 - x, y, (0, 0, 0, 0))

    return img


def resize_rgba(src: Sequence[int], sw: int, sh: int, dw: int, dh: int) -> List[int]:
    # Simple box filter (area average). Good enough for small icons.
    dst = [0] * (dw * dh * 4)
    for y in range(dh):
        y0 = y * sh / dh
        y1 = (y + 1) * sh / dh
        iy0 = int(y0)
        iy1 = int(y1) if int(y1) > iy0 else iy0 + 1
        for x in range(dw):
            x0 = x * sw / dw
            x1 = (x + 1) * sw / dw
            ix0 = int(x0)
            ix1 = int(x1) if int(x1) > ix0 else ix0 + 1

            acc = [0.0, 0.0, 0.0, 0.0]
            wsum = 0.0
            for sy in range(iy0, min(sh, iy1)):
                wy = 1.0
                for sx in range(ix0, min(sw, ix1)):
                    wx = 1.0
                    w = wx * wy
                    i = (sy * sw + sx) * 4
                    acc[0] += src[i] * w
                    acc[1] += src[i + 1] * w
                    acc[2] += src[i + 2] * w
                    acc[3] += src[i + 3] * w
                    wsum += w
            if wsum == 0:
                wsum = 1.0
            di = (y * dw + x) * 4
            dst[di] = clamp8(int(acc[0] / wsum + 0.5))
            dst[di + 1] = clamp8(int(acc[1] / wsum + 0.5))
            dst[di + 2] = clamp8(int(acc[2] / wsum + 0.5))
            dst[di + 3] = clamp8(int(acc[3] / wsum + 0.5))
    return dst


def png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_png_rgba(img: Sequence[int], w: int, h: int) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 8-bit RGBA

    # Filter type 0 (None) for each row.
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        start = y * stride
        raw.extend(img[start : start + stride])

    comp = zlib.compress(bytes(raw), level=9)
    return sig + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", comp) + png_chunk(b"IEND", b"")


def build_ico(pngs: Sequence[Tuple[int, bytes]]) -> bytes:
    # ICO header
    out = bytearray()
    out.extend(struct.pack("<HHH", 0, 1, len(pngs)))  # reserved, type=icon, count

    # Directory entries (16 bytes each)
    offset = 6 + 16 * len(pngs)
    entries = []
    for size, data in pngs:
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entry = struct.pack(
            "<BBBBHHII",
            w,
            h,
            0,  # color count
            0,  # reserved
            1,  # planes
            32,  # bitcount
            len(data),
            offset,
        )
        entries.append(entry)
        offset += len(data)

    for e in entries:
        out.extend(e)
    for _, data in pngs:
        out.extend(data)
    return bytes(out)


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_path = os.path.join(repo_root, "favicon.ico")

    base_size = 256
    base = draw_icon_base(base_size)
    sizes = [256, 128, 64, 48, 32, 16]

    pngs: List[Tuple[int, bytes]] = []
    for s in sizes:
        if s == base_size:
            img = base
        else:
            img = resize_rgba(base, base_size, base_size, s, s)
        pngs.append((s, encode_png_rgba(img, s, s)))

    ico = build_ico(pngs)
    with open(out_path, "wb") as f:
        f.write(ico)

    print(f"Wrote {out_path} ({len(ico)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

