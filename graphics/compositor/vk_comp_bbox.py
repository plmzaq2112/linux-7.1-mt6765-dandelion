#!/usr/bin/env python3
"""vk_comp: verify prints the bbox of non-background pixels"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

old = '''                printf("verify: slot=%d diff=%u/%u (e.g. %08x at %d,%d)\\n", sl,
                       diff, total, (unsigned)sw, sx, sy);'''
new = '''                {
                    int minx = (int)w, maxx = -1, miny = (int)h, maxy = -1;

                    for (uint32_t y = 0; y < h; y++) {
                        for (uint32_t x = 0; x < w; x++) {
                            if (px[(size_t)y * stride + x] == corner)
                                continue;
                            if ((int)x < minx) minx = (int)x;
                            if ((int)x > maxx) maxx = (int)x;
                            if ((int)y < miny) miny = (int)y;
                            if ((int)y > maxy) maxy = (int)y;
                        }
                    }
                    printf("verify: slot=%d diff=%u/%u bbox x=%d..%d y=%d..%d\\n",
                           sl, diff, total, minx, maxx, miny, maxy);
                }'''
assert s.count(old) == 1, 'verify print'
s = s.replace(old, new, 1)

p.write_text(s)
print('bbox verify added')
