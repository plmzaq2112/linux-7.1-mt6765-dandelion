#!/usr/bin/env python3
"""Convert an animated GIF/WebP to the KMSA frame format used by kms-loop.

Format (little endian):
  magic  "KMSA"
  u32    width
  u32    height
  u32    nframes
  then per frame:
    u16  delay_ms
    u32  rle_bytes
    u8[] rle data: repeated (u16 count, u16 rgb565) pairs
"""
import sys, struct
from PIL import Image, ImageSequence

W, H = 720, 1600


def to565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def rle_encode(vals):
    out = bytearray()
    n = len(vals)
    i = 0
    while i < n:
        v = vals[i]
        j = i + 1
        while j < n and vals[j] == v and (j - i) < 65535:
            j += 1
        out += struct.pack("<HH", j - i, v)
        i = j
    return bytes(out)


def convert(src, dst, max_frames=600):
    im = Image.open(src)
    frames = []
    delays = []
    for fr in ImageSequence.Iterator(im):
        d = fr.info.get("duration", 100) or 100
        frames.append(fr.convert("RGB"))
        delays.append(max(20, min(2000, int(d))))
        if len(frames) >= max_frames:
            break

    n = len(frames)
    print("frames:", n, "delays(ms):", delays[:8], "..." if n > 8 else "")

    blob = bytearray()
    meta = []
    for idx, img in enumerate(frames):
        # letterbox into W x H
        iw, ih = img.size
        scale = min(W / iw, H / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        img = img.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), (0, 0, 0))
        canvas.paste(img, ((W - nw) // 2, (H - nh) // 2))

        px = canvas.load()
        vals = []
        for y in range(H):
            row = []
            for x in range(W):
                r, g, b = px[x, y]
                row.append(to565(r, g, b))
            vals.extend(row)

        enc = rle_encode(vals)
        meta.append((delays[idx], len(enc)))
        blob += enc
        if idx % 20 == 0:
            print("  frame", idx, "rle", len(enc), "bytes")

    with open(dst, "wb") as f:
        f.write(b"KMSA")
        f.write(struct.pack("<III", W, H, n))
        for d, sz in meta:
            f.write(struct.pack("<HI", d, sz))
        f.write(blob)
    print("wrote", dst, "size", len(blob) + 12 + 6 * n)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: convert-gif.py input.gif output.kmsa")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
