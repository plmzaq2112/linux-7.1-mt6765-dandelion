#!/usr/bin/env python3
"""vk_geom: VK_GEOM_NOCLEAR / VK_GEOM_NODRAW to split clear vs draw cost"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_geom.c')
s = p.read_text()

old = '''        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,'''
new = '''        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR, /* see nop_* below */'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

# after the attachment struct is declared, adjust from env
old = '''    VkSubpassDescription sp = {'''
new = '''    if (getenv("VK_GEOM_NOCLEAR"))
        att.loadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;

    VkSubpassDescription sp = {'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = '''    vkCmdDraw(cmd, 3, 1, 0, 0);'''
new = '''    if (!getenv("VK_GEOM_NODRAW"))
        vkCmdDraw(cmd, 3, 1, 0, 0);'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

p.write_text(s)
print('clear/draw split knobs added')
