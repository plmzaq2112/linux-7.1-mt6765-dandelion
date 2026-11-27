#!/usr/bin/env python3
"""vk_comp: static viewport + dynamic scissor only (precise edits)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

# dynamic scissor only
s = s.replace('    VkDynamicState dyn[1] = { 0 };',
              '    VkDynamicState dyn[1] = { VK_DYNAMIC_STATE_SCISSOR };', 1)
s = s.replace('        .dynamicStateCount = 0,',
              '        .dynamicStateCount = 1,', 1)

# site 1 (initial block): drop viewport + scissor set
old = '''        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        VkDeviceSize off = 0;'''
new = '''        VkDeviceSize off = 0;'''
assert s.count(old) == 1, 'site1'
s = s.replace(old, new, 1)

# site 2 (loop): drop the full-screen viewport/scissor pair
old = '''        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        vkCmdSetScissor(v.cmd, 0, 1, &sc);
        VkDeviceSize off = 0;'''
new = '''        VkDeviceSize off = 0;'''
assert s.count(old) == 1, 'site2'
s = s.replace(old, new, 1)

# per-layer: keep scissor, drop viewport
old = '''            vkCmdSetViewport(v.cmd, 0, 1, &vp);
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);'''
new = '''            vkCmdSetScissor(v.cmd, 0, 1, &dsc);'''
assert s.count(old) == 1, 'per-layer'
s = s.replace(old, new, 1)

# initial block needs a per-layer scissor too (it lost its only scissor set)
old = '''            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdBindDescriptorSets('''
cnt = s.count(old)
assert cnt == 2, 'bind sites %d' % cnt
s = s.replace(old, '''            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets(''')

p.write_text(s)
print('static viewport + dynamic scissor (clean)')
