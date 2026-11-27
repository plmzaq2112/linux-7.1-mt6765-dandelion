#!/usr/bin/env python3
"""vk_comp: test with NO dynamic state at all (static vp+sc)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

old = '''    VkDynamicState dyn[1] = { VK_DYNAMIC_STATE_SCISSOR };'''
new = '''    VkDynamicState dyn[1] = { 0 };'''
assert s.count(old) == 1, 'dyn array'
s = s.replace(old, new, 1)

old = '''        .dynamicStateCount = 1,'''
new = '''        .dynamicStateCount = 0,'''
assert s.count(old) == 1, 'dyn count'
s = s.replace(old, new, 1)

# drop the per-layer scissor calls (keep the draws)
old = '''            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets('''
new = '''            vkCmdBindDescriptorSets('''
assert s.count(old) == 2, 'scissor calls %d' % s.count(old)
s = s.replace(old, new)

p.write_text(s)
print('dynamic state removed (test)')
