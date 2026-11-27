#!/usr/bin/env python3
"""vk_kms2: split submit+fence into record / queue / fence-wait"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''    double t_submit = 0.0, t_flip = 0.0;'''
new = '''    double t_submit = 0.0, t_flip = 0.0;
    double t_record = 0.0, t_queue = 0.0, t_fence = 0.0;'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old2 = '''        struct timespec ts0, ts1;
        clock_gettime(CLOCK_MONOTONIC, &ts0);
        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));
        clock_gettime(CLOCK_MONOTONIC, &ts1);'''
new2 = '''        struct timespec ts0, ts1;
        clock_gettime(CLOCK_MONOTONIC, &ts0);
        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        clock_gettime(CLOCK_MONOTONIC, &ts1);
        t_queue += (ts1.tv_sec - ts0.tv_sec) + (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
        clock_gettime(CLOCK_MONOTONIC, &ts0);
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));
        clock_gettime(CLOCK_MONOTONIC, &ts1);
        t_fence += (ts1.tv_sec - ts0.tv_sec) + (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
        clock_gettime(CLOCK_MONOTONIC, &ts0);'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

old3 = '''        if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\\n",
               1000.0 * t_submit / frames, 1000.0 * t_flip / frames);'''
old3 = '''    if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\\n",
               1000.0 * t_submit / frames, 1000.0 * t_flip / frames);'''
new3 = '''    if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\\n",
               1000.0 * t_submit / frames, 1000.0 * t_flip / frames);
    if (frames)
        printf("avg: queue %.2f ms, fence-wait %.2f ms\\n",
               1000.0 * t_queue / frames, 1000.0 * t_fence / frames);'''
assert s.count(old3) == 1
s = s.replace(old3, new3, 1)

p.write_text(s)
print('split timing added')
