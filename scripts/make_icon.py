#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成源图标 icons/com.ruizi.floatinglyric.png（128×128，纯标准库，无 Pillow 依赖）。

画的是「悬浮歌词」的意象：深紫圆角方块 + 三条歌词行，中间一条高亮（代表正在唱的那句）。
"""
import zlib, struct, os, math

SS = 4                    # 超采样倍数
SIZE = 128
W = SIZE * SS
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "scripts" else HERE
OUT = os.path.join(ROOT, "icons", "com.ruizi.floatinglyric.png")


def lerp(a, b, t):
    return a + (b - a) * t


def rounded_rect_alpha(x, y, x0, y0, x1, y1, r):
    """点 (x,y) 在圆角矩形内的覆盖率（0..1，边界做 1px 软过渡）"""
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    d = math.hypot(x - cx, y - cy)
    return max(0.0, min(1.0, (r - d) + 0.5)) if (x0 <= x <= x1 and y0 <= y <= y1) else 0.0


def build():
    px = [[(0, 0, 0, 0) for _ in range(W)] for _ in range(W)]

    # 背景：圆角方块 + 斜向渐变
    pad, rad = 4 * SS, 28 * SS
    for y in range(W):
        for x in range(W):
            a = rounded_rect_alpha(x + .5, y + .5, pad, pad, W - pad, W - pad, rad)
            if a <= 0:
                continue
            t = (x / W * 0.45 + y / W * 0.55)
            r = lerp(96, 168, t)
            g = lerp(74, 92, t)
            b = lerp(232, 255, t)
            # 左上角提亮，做出玻璃质感
            glow = max(0.0, 1.0 - math.hypot(x - W * .28, y - W * .22) / (W * .72))
            r, g, b = r + 26 * glow, g + 22 * glow, b + 12 * glow
            px[y][x] = (int(min(255, r)), int(min(255, g)), int(min(255, b)), int(255 * a))

    # 三条歌词行：中间亮、上下暗
    bars = [
        (0.30, 0.115, 0.46, (255, 255, 255), 0.42),   # (y比例, 高度比例, 宽度比例, 颜色, 不透明度)
        (0.465, 0.150, 0.70, (255, 255, 255), 1.00),
        (0.635, 0.115, 0.54, (255, 255, 255), 0.42),
    ]
    for yfrac, hfrac, wfrac, col, alpha in bars:
        bh = hfrac * W
        bw = wfrac * W
        x0 = (W - bw) / 2
        y0 = yfrac * W
        y1 = y0 + bh
        rr = bh / 2
        for y in range(int(y0) - 2, int(y1) + 2):
            for x in range(int(x0) - 2, int(x0 + bw) + 2):
                if not (0 <= x < W and 0 <= y < W):
                    continue
                cov = rounded_rect_alpha(x + .5, y + .5, x0, y0, x0 + bw, y1, rr)
                if cov <= 0:
                    continue
                src = col + (int(255 * alpha * cov),)
                dst = px[y][x]
                sa, da = src[3] / 255.0, dst[3] / 255.0
                oa = sa + da * (1 - sa)
                if oa <= 0:
                    continue
                px[y][x] = tuple(
                    int((src[i] * sa + dst[i] * da * (1 - sa)) / oa) for i in range(3)
                ) + (int(oa * 255),)

    # 降采样到 128
    out = bytearray()
    for y in range(SIZE):
        out.append(0)  # filter type 0
        for x in range(SIZE):
            rs = gs = bs = as_ = 0
            for dy in range(SS):
                for dx in range(SS):
                    p = px[y * SS + dy][x * SS + dx]
                    a = p[3]
                    rs += p[0] * a
                    gs += p[1] * a
                    bs += p[2] * a
                    as_ += a
            if as_ == 0:
                out += bytes((0, 0, 0, 0))
            else:
                out += bytes((rs // as_, gs // as_, bs // as_, as_ // (SS * SS)))
    return bytes(out)


def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path, raw, size):
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(png)
    return len(png)


if __name__ == "__main__":
    n = write_png(OUT, build(), SIZE)
    print(f"✅ 图标已生成：{OUT}（{n} 字节）")
