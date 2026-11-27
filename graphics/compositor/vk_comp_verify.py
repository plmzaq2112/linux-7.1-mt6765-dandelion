#!/usr/bin/env python3
"""vk_comp: VK_COMP_VERIFY=1 samples the last frame from the scanout buffer"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

old = '''    if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\\n",'''
new = '''    if (getenv("VK_COMP_VERIFY")) {
        struct frame *f = &fr[onscreen];
        struct drm_mode_map_dumb md = { .handle = f->dumb_handle };

        if (ioctl(d.fd, DRM_IOCTL_MODE_MAP_DUMB, &md) == 0) {
            size_t sz = (size_t)f->dumb_pitch * h;
            void *p = mmap(NULL, sz, PROT_READ, MAP_SHARED, d.fd, md.offset);

            if (p != MAP_FAILED) {
                const uint32_t *px = p;
                uint32_t stride = f->dumb_pitch / 4;
                uint32_t corner = px[0];
                uint32_t diff = 0, total = 0;
                int sw = 0, sx = 0, sy = 0;

                for (uint32_t y = 0; y < h; y += 5) {
                    for (uint32_t x = 0; x < w; x += 5) {
                        total++;
                        if (px[(size_t)y * stride + x] != corner) {
                            diff++;
                            sw = (int)px[(size_t)y * stride + x];
                            sx = (int)x;
                            sy = (int)y;
                        }
                    }
                }
                printf("verify: corner=%08x diff=%u/%u (e.g. %08x at %d,%d)\\n",
                       corner, diff, total, (unsigned)sw, sx, sy);
                munmap(p, sz);
            }
        }
    }

    if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\\n",'''
assert s.count(old) == 1, 'summary anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('verify added')
