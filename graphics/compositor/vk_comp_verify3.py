#!/usr/bin/env python3
"""vk_comp: verify all slots + dump first VBO vertex"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

old = '''    if (getenv("VK_COMP_VERIFY")) {
        struct frame *f = &fr[onscreen];
        struct drm_mode_map_dumb md = { .handle = f->dumb_handle };

        if (ioctl(d.fd, DRM_IOCTL_MODE_MAP_DUMB, &md) == 0) {'''
new = '''    if (getenv("VK_COMP_VERIFY")) {
        const float *fv = v.vbo_ptr;

        printf("verify: vbo[0..8] = %.3f %.3f %.3f | %.3f %.3f | %.3f %.3f %.3f\\n",
               fv[0], fv[1], fv[2], fv[3], fv[4], fv[5], fv[6], fv[7], fv[8]);
        for (int sl = 0; sl < NSLOT; sl++) {
        struct frame *f = &fr[sl];
        struct drm_mode_map_dumb md = { .handle = f->dumb_handle };

        if (ioctl(d.fd, DRM_IOCTL_MODE_MAP_DUMB, &md) == 0) {'''
assert s.count(old) == 1, 'verify head'
s = s.replace(old, new, 1)

old = '''                printf("verify: diff=%u/%u (e.g. %08x at %d,%d)\\n", diff, total,
                       (unsigned)sw, sx, sy);
                munmap(p, sz);
            }
        }
    }'''
new = '''                printf("verify: slot=%d diff=%u/%u (e.g. %08x at %d,%d)\\n", sl,
                       diff, total, (unsigned)sw, sx, sy);
                munmap(p, sz);
            }
        }
        }
    }'''
assert s.count(old) == 1, 'verify tail'
s = s.replace(old, new, 1)

p.write_text(s)
print('verify: all slots + vbo dump')
