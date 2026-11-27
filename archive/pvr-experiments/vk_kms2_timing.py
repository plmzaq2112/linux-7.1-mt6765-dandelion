#!/usr/bin/env python3
"""vk_kms2: measure submit vs flip time"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t frames = 0;
    int cur = 1;
'''
new = '''    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t frames = 0;
    int cur = 1;
    double t_submit = 0.0, t_flip = 0.0;
'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old2 = '''        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));

'''
new2 = '''        struct timespec ts0, ts1;
        clock_gettime(CLOCK_MONOTONIC, &ts0);
        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));
        clock_gettime(CLOCK_MONOTONIC, &ts1);
        t_submit += (ts1.tv_sec - ts0.tv_sec) +
                    (ts1.tv_nsec - ts0.tv_nsec) / 1e9;

'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

old3 = '''        g_flip_done = 0;
        if (drmModePageFlip(d.fd, d.crtc_id, f->drm_fb,
                            DRM_MODE_PAGE_FLIP_EVENT, NULL)) {
            fprintf(stderr, "page flip failed: %s\\n", strerror(errno));
            break;
        }
        if (wait_flip(d.fd))
            break;
'''
new3 = '''        clock_gettime(CLOCK_MONOTONIC, &ts0);
        g_flip_done = 0;
        if (drmModePageFlip(d.fd, d.crtc_id, f->drm_fb,
                            DRM_MODE_PAGE_FLIP_EVENT, NULL)) {
            fprintf(stderr, "page flip failed: %s\\n", strerror(errno));
            break;
        }
        if (wait_flip(d.fd))
            break;
        clock_gettime(CLOCK_MONOTONIC, &ts1);
        t_flip += (ts1.tv_sec - ts0.tv_sec) +
                  (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
'''
assert s.count(old3) == 1
s = s.replace(old3, new3, 1)

old4 = '''    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\\n",
           (unsigned long long)frames, total, frames / total,
           zero_copy ? "zero-copy" : "cpu-copy");'''
new4 = '''    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\\n",
           (unsigned long long)frames, total, frames / total,
           zero_copy ? "zero-copy" : "cpu-copy");
    if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\\n",
               1000.0 * t_submit / frames, 1000.0 * t_flip / frames);'''
assert s.count(old4) == 1
s = s.replace(old4, new4, 1)

p.write_text(s)
print('timing added')
