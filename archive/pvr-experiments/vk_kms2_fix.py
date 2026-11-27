#!/usr/bin/env python3
"""vk_kms2 compile fixes"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''        r = v->get_fd_props(v->pd,
                           VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd,
                           &fp);'''
new = '''        r = v->get_fd_props(v->dev,
                           VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd,
                           &fp);'''
assert s.count(old) == 1
s = s.replace(old, new, 1)

old2 = '            fr[i].dumb_size = cd.size;\n'
assert s.count(old2) == 1
s = s.replace(old2, '', 1)

p.write_text(s)
print('fixed')
