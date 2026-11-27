#!/usr/bin/env python3
"""vk_kms2: VK_KMS_DRAWS=N to separate per-submit from per-draw cost"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''    int no_present = getenv("VK_KMS_NOPRESENT") != NULL;'''
new = '''    int no_present = getenv("VK_KMS_NOPRESENT") != NULL;
    int draws_per_frame = getenv("VK_KMS_DRAWS") ? atoi(getenv("VK_KMS_DRAWS")) : 1;
    if (draws_per_frame < 1)
        draws_per_frame = 1;'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

# render loop: one draw -> N draws with different offsets
old2 = '''        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        vkCmdDraw(v.cmd, 6, 1, 0, 0);
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));

        VkSubmitInfo si = {'''
new2 = '''        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        for (int d = 0; d < draws_per_frame; d++) {
            VkViewport dvp = { (float)(d * 4), (float)(d * 4),
                               (float)(w / 2), (float)(h / 2), 0, 1 };
            VkRect2D dsc = { { d * 4, d * 4 }, { w / 2, h / 2 } };
            vkCmdSetViewport(v.cmd, 0, 1, &dvp);
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdDraw(v.cmd, 6, 1, 0, 0);
        }
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));

        VkSubmitInfo si = {'''
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)

old3 = '''    if (frames)
        printf("avg: queue %.2f ms, fence-wait %.2f ms\\n",
               1000.0 * t_queue / frames, 1000.0 * t_fence / frames);'''
new3 = '''    if (frames)
        printf("avg: queue %.2f ms, fence-wait %.2f ms (draws/frame=%d)\\n",
               1000.0 * t_queue / frames, 1000.0 * t_fence / frames,
               draws_per_frame);'''
assert s.count(old3) == 1
s = s.replace(old3, new3, 1)

p.write_text(s)
print('draws knob added')
