#!/usr/bin/env python3
"""vk_geom: VK_GEOM_DRAWS=N (per-frame draw count scaling)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_geom.c')
s = p.read_text()

old = '''    if (!getenv("VK_GEOM_NODRAW"))
        vkCmdDraw(cmd, 3, 1, 0, 0);'''
new = '''    {
        int ndraws = getenv("VK_GEOM_DRAWS") ? atoi(getenv("VK_GEOM_DRAWS")) : 1;

        if (ndraws < 1)
            ndraws = 1;
        for (int d = 0; d < (getenv("VK_GEOM_NODRAW") ? 0 : ndraws); d++) {
            VkViewport dvp = { 0, 0, (float)W, (float)H, 0, 1 };
            VkRect2D dsc = { { 0, 0 }, { W, H } };
            vkCmdSetViewport(cmd, 0, 1, &dvp);
            vkCmdSetScissor(cmd, 0, 1, &dsc);
            vkCmdDraw(cmd, 3, 1, 0, 0);
        }
    }'''
assert s.count(old) == 1, 'draw anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('vk_geom draws knob added')
