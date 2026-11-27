#!/usr/bin/env python3
"""vk_geom: draw loop must keep the static (env driven) viewport/scissor"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_geom.c')
s = p.read_text()

old = '''        for (int d = 0; d < (getenv("VK_GEOM_NODRAW") ? 0 : ndraws); d++) {
            VkViewport dvp = { 0, 0, (float)W, (float)H, 0, 1 };
            VkRect2D dsc = { { 0, 0 }, { W, H } };
            vkCmdSetViewport(cmd, 0, 1, &dvp);
            vkCmdSetScissor(cmd, 0, 1, &dsc);
            vkCmdDraw(cmd, 3, 1, 0, 0);
        }'''
new = '''        for (int d = 0; d < (getenv("VK_GEOM_NODRAW") ? 0 : ndraws); d++)
            vkCmdDraw(cmd, 3, 1, 0, 0);'''
assert s.count(old) == 1, 'draw loop anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('draw loop simplified (static vp/sc kept)')
