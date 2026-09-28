#!/usr/bin/env python3
"""生成全屏时钟的 PWA 图标（纯标准库，无第三方依赖）。

设计：不透明纯黑底 + 白色圆环与指针，与 App 默认主题一致；
图形控制在中心 80% 安全区内，可直接用作 maskable 图标。
"""
import math
import os
import struct
import zlib

OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_png(path, w, h, rgb_alpha_rows):
    """rgb_alpha_rows: bytes，每像素 4 字节 RGBA，长度 w*h*4。"""
    raw = b"".join(
        b"\x00" + rgb_alpha_rows[y * w * 4:(y + 1) * w * 4] for y in range(h)
    )

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(blob)


def seg_dist(px, py, ax, ay, bx, by):
    """点到线段的距离。"""
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L2))
    dx, dy = px - (ax + t * vx), py - (ay + t * vy)
    return math.hypot(dx, dy)


def cov(d):
    """距离 -> 覆盖率，d 为负表示在形状内部；带 1px 抗锯齿。"""
    return max(0.0, min(1.0, 0.5 - d))


def polar(cx, cy, angle_deg, r):
    a = math.radians(angle_deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def build(size):
    S = float(size)
    cx = cy = S / 2.0
    ring_r = S * 0.325
    ring_w = S * 0.042
    hand_w = S * 0.040
    hour_len = S * 0.170
    min_len = S * 0.245

    hx, hy = polar(cx, cy, 300.0, hour_len)   # 时针指向 10 点
    mx, my = polar(cx, cy, 60.0, min_len)     # 分针指向 2 点
    hw = hand_w / 2.0
    rw = ring_w / 2.0

    buf = bytearray()
    for y in range(size):
        py = y + 0.5
        for x in range(size):
            px = x + 0.5
            d = math.hypot(px - cx, py - cy)

            a = cov(abs(d - ring_r) - rw)                 # 圆环
            if a < 1.0:
                dh = seg_dist(px, py, cx, cy, hx, hy) - hw
                a = max(a, cov(dh))                       # 时针
            if a < 1.0:
                dm = seg_dist(px, py, cx, cy, mx, my) - hw
                a = max(a, cov(dm))                       # 分针
            if a < 1.0:
                a = max(a, cov(d - S * 0.030))            # 中心轴点

            v = int(round(255 * a))
            buf += bytes((v, v, v, 255))
    return bytes(buf)


def main():
    for size in (180, 192, 512):
        name = "icon-%d.png" % size
        path = os.path.join(OUT_DIR, name)
        write_png(path, size, size, build(size))
        print("wrote %s (%d bytes)" % (name, os.path.getsize(path)))


if __name__ == "__main__":
    main()
