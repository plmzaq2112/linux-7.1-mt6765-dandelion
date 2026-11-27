#!/usr/bin/env python3
"""vk_kms2: pipeline submits (render frame N+1 while frame N is being flipped)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

# --- NSLOT define -----------------------------------------------------------
old = '#define CHECK_VK(x)'
new = '''#ifndef NSLOT
#define NSLOT 3
#endif

#define CHECK_VK(x)'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

# --- frames array -----------------------------------------------------------
old = '    struct frame fr[2];'
new = '    struct frame fr[NSLOT];'
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = '        for (int i = 0; i < 2 && ok; i++) {'
new = '        for (int i = 0; i < NSLOT && ok; i++) {'
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = '''        } else {
            for (int i = 0; i < 2; i++) {
                frame_fini(&v, &fr[i]);'''
new = '''        } else {
            for (int i = 0; i < NSLOT; i++) {
                frame_fini(&v, &fr[i]);'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = '''        printf("fallback: PVR image + CPU copy\\n");
        for (int i = 0; i < 2; i++) {'''
new = '''        printf("fallback: PVR image + CPU copy\\n");
        for (int i = 0; i < NSLOT; i++) {'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

# --- pipeline state, just before the initial render -------------------------
old = '    /* First frame: render before the initial modeset. */'
new = '''    VkFence fences[NSLOT];
    fences[0] = v.fence;
    for (int i = 1; i < NSLOT; i++) {
        VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
        CHECK_VK(vkCreateFence(v.dev, &fci, NULL, &fences[i]));
    }

    int busy[NSLOT] = { 1, 0, 0 };
    int onscreen = 0;
    int pending = -1;
    int next_slot = 1;

    /* First frame: render before the initial modeset. */'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

# --- the render/present loop ------------------------------------------------
start = s.index('    while (1) {')
end = s.index('    struct timespec t1;')

loop = r'''    while (1) {
        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);
        double elapsed = (now.tv_sec - t0.tv_sec) +
                         (now.tv_nsec - t0.tv_nsec) / 1e9;
        if (elapsed >= seconds)
            break;

        /* Pick a buffer that is neither on screen nor awaiting a flip. */
        int i = -1;
        for (int k = 0; k < NSLOT; k++) {
            int idx = (next_slot + k) % NSLOT;
            if (!busy[idx]) {
                i = idx;
                break;
            }
        }
        if (i < 0)
            break;
        next_slot = (i + 1) % NSLOT;

        struct frame *f = &fr[i];
        build_scene(&v, (float)elapsed * 0.8f);

        VkCommandBufferBeginInfo bi = {
            .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        };
        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));
        VkClearValue cv = { .color = { { 0.05f, 0.05f, 0.1f, 1.0f } } };
        VkRenderPassBeginInfo rbi = {
            .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
            .renderPass = v.rp,
            .framebuffer = f->fb,
            .renderArea = { { 0, 0 }, { w, h } },
            .clearValueCount = 1,
            .pClearValues = &cv,
        };
        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        vkCmdSetScissor(v.cmd, 0, 1, &sc);
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        for (int d = 0; d < (clear_only ? 0 : draws_per_frame); d++) {
            VkViewport dvp = { (float)(d * 4), (float)(d * 4),
                               (float)(w / 2), (float)(h / 2), 0, 1 };
            VkRect2D dsc = { { d * 4, d * 4 }, { w / 2, h / 2 } };
            vkCmdSetViewport(v.cmd, 0, 1, &dvp);
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdDraw(v.cmd, 6, 1, 0, 0);
        }
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));

        VkSubmitInfo si = {
            .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
            .commandBufferCount = 1,
            .pCommandBuffers = &v.cmd,
        };
        struct timespec ts0, ts1;
        clock_gettime(CLOCK_MONOTONIC, &ts0);
        CHECK_VK(vkResetFences(v.dev, 1, &fences[i]));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, fences[i]));
        clock_gettime(CLOCK_MONOTONIC, &ts1);
        t_queue += (ts1.tv_sec - ts0.tv_sec) + (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
        busy[i] = 1;

        /* Present the previous frame: its render had a whole flip period. */
        if (pending >= 0) {
            struct frame *pf = &fr[pending];

            clock_gettime(CLOCK_MONOTONIC, &ts0);
            CHECK_VK(vkWaitForFences(v.dev, 1, &fences[pending], VK_TRUE,
                                     2000000000ull));
            clock_gettime(CLOCK_MONOTONIC, &ts1);
            t_fence += (ts1.tv_sec - ts0.tv_sec) +
                       (ts1.tv_nsec - ts0.tv_nsec) / 1e9;

            if (!zero_copy) {
                for (uint32_t y = 0; y < h; y++)
                    memcpy((char *)pf->dumb_ptr + (size_t)y * pf->dumb_pitch,
                           (const char *)pf->host + (size_t)y * pf->pitch,
                           (size_t)w * 4);
            }

            if (no_present) {
                busy[pending] = 0;
                frames++;
            } else {
                clock_gettime(CLOCK_MONOTONIC, &ts0);
                g_flip_done = 0;
                if (drmModePageFlip(d.fd, d.crtc_id, pf->drm_fb,
                                    DRM_MODE_PAGE_FLIP_EVENT, NULL)) {
                    fprintf(stderr, "page flip failed: %s\n", strerror(errno));
                    break;
                }
                if (wait_flip(d.fd))
                    break;
                clock_gettime(CLOCK_MONOTONIC, &ts1);
                t_flip += (ts1.tv_sec - ts0.tv_sec) +
                          (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
                busy[onscreen] = 0;
                onscreen = pending;
                frames++;
            }
        }

        pending = i;
    }

'''
s = s[:start] + loop + s[end:]

p.write_text(s)
print('pipelined loop installed')
