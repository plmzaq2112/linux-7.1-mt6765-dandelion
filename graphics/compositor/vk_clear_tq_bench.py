#!/usr/bin/env python3
"""vk_clear_tq: VK_TQ_LOOP=N benchmark of the TQ clear path"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_clear_tq.c')
s = p.read_text()

old = '''    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);

    void *ptr = NULL;'''
new = '''    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);

    if (getenv("VK_TQ_LOOP")) {
        int loop = atoi(getenv("VK_TQ_LOOP"));
        struct timespec a, b;
        double tot = 0.0;

        for (int i = 0; i < loop; i++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
            if (r != VK_SUCCESS) break;
            r = vkQueueWaitIdle(q);
            clock_gettime(CLOCK_MONOTONIC, &b);
            if (r != VK_SUCCESS) break;
            tot += (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("tq bench %dx%d: %d frames, %.2f ms/frame\\n", W, H, loop,
               1000.0 * tot / loop);
    }

    void *ptr = NULL;'''
assert s.count(old) == 1, 'submit anchor'
s = s.replace(old, new, 1)

if '#include <time.h>' not in s:
    s = s.replace('#include <stdint.h>', '#include <stdint.h>\n#include <time.h>', 1)

p.write_text(s)
print('tq loop bench added')
