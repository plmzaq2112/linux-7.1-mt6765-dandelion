#!/usr/bin/env python3
"""vk_comp: static viewport + dynamic scissor only (no invalid vkCmdSetViewport)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

# 1. dynamic scissor only
old = '''    VkDynamicState dyn[1] = { 0 };'''
new = '''    VkDynamicState dyn[1] = { VK_DYNAMIC_STATE_SCISSOR };'''
assert s.count(old) == 1, 'dyn array'
s = s.replace(old, new, 1)

old = '''        .dynamicStateCount = 0,'''
new = '''        .dynamicStateCount = 1,'''
assert s.count(old) == 1, 'dyn count'
s = s.replace(old, new, 1)

# 2. drop the (invalid) vkCmdSetViewport calls
old = '''        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        VkDeviceSize off = 0;'''
new = '''        VkDeviceSize off = 0;'''
assert s.count(old) == 2, 'viewport calls %d' % s.count(old)
s = s.replace(old, new)

old = '''            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetViewport(v.cmd, 0, 1, &vp);
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);'''
new = '''            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);'''
assert s.count(old) == 1, 'loop viewport'
s = s.replace(old, new, 1)

# 3. re-add the per-layer scissor in the initial block
old = '''            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdBindDescriptorSets('''
new = '''            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets('''
assert s.count(old) == 2, 'bind sites %d' % s.count(old)
s = s.replace(old, new)

p.write_text(s)
print('static viewport + dynamic scissor (clean)')
