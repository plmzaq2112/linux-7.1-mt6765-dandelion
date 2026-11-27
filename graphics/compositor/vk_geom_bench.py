#!/usr/bin/env python3
"""vk_geom: VK_GEOM_LOOP=N benchmark of submit+fence per frame"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_geom.c')
s = p.read_text()

# find the submit + wait idle block
old = '''    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);
'''
new = '''    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);

    if (getenv("VK_GEOM_LOOP")) {
        int loop = atoi(getenv("VK_GEOM_LOOP"));
        struct timespec a, b;
        double tot = 0.0;
        for (int k = 0; k < loop; k++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
            if (r != VK_SUCCESS) {
                fprintf(stderr, "loop submit %d\\n", r);
                break;
            }
            r = vkQueueWaitIdle(q);
            clock_gettime(CLOCK_MONOTONIC, &b);
            if (r != VK_SUCCESS) {
                fprintf(stderr, "loop wait %d\\n", r);
                break;
            }
            tot += (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("bench %dx%d: %d frames, %.2f ms/frame\\n", W, H, loop,
               1000.0 * tot / loop);
    }
'''
assert s.count(old) == 1, 'submit anchor'
s = s.replace(old, new, 1)

if '#include <time.h>' not in s:
    s = s.replace('#include <stdint.h>', '#include <stdint.h>\n#include <time.h>', 1)

p.write_text(s)
print('geom loop bench added')
