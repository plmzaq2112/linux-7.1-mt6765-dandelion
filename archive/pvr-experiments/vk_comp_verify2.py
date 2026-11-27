#!/usr/bin/env python3
"""vk_comp: richer verify diagnostics (layer rect + sampled pixels)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

old = '''                printf("verify: corner=%08x diff=%u/%u (e.g. %08x at %d,%d)\\n",
                       corner, diff, total, (unsigned)sw, sx, sy);'''
new = '''                printf("verify: onscreen=%d layers=%d corner=%08x\\n",
                       onscreen, g_nlayers, corner);
                printf("verify: layer0 rect=(%.0f,%.0f %.0fx%.0f)\\n",
                       g_layers[0].x, g_layers[0].y, g_layers[0].w,
                       g_layers[0].h);
                {
                    int cx = (int)(g_layers[0].x + g_layers[0].w / 2);
                    int cy = (int)(g_layers[0].y + g_layers[0].h / 2);

                    if (cx < 0) cx = 0;
                    if (cy < 0) cy = 0;
                    if (cx >= (int)w) cx = (int)w - 1;
                    if (cy >= (int)h) cy = (int)h - 1;
                    printf("verify: layer0 centre (%d,%d) = %08x, (0,0)=%08x\\n",
                           cx, cy, px[(size_t)cy * stride + cx],
                           px[0]);
                }
                printf("verify: diff=%u/%u (e.g. %08x at %d,%d)\\n", diff, total,
                       (unsigned)sw, sx, sy);'''
assert s.count(old) == 1, 'verify print anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('verify diagnostics added')
