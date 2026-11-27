#!/usr/bin/env python3
"""vk_ds: VK_DS_D32=1 uses D32_SFLOAT depth (vendor uses F32Z)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_ds.c')
s = p.read_text()

old = '''    VkImage depth = make_image(dev, pd, W, H, VK_FORMAT_D16_UNORM,'''
new = '''    const int depth32 = getenv("VK_DS_D32") != NULL;
    const VkFormat depth_fmt = depth32 ? VK_FORMAT_D32_SFLOAT
                                       : VK_FORMAT_D16_UNORM;
    VkImage depth = make_image(dev, pd, W, H, depth_fmt,'''
assert s.count(old) == 1, 'depth image anchor'
s = s.replace(old, new, 1)

old = '''    dvci.format = VK_FORMAT_D16_UNORM;'''
new = '''    dvci.format = depth_fmt;'''
assert s.count(old) == 1, 'depth view anchor'
s = s.replace(old, new, 1)

old = '''        { .format = VK_FORMAT_D16_UNORM,'''
new = '''        { .format = depth_fmt,'''
assert s.count(old) == 1, 'attachment anchor'
s = s.replace(old, new, 1)

old = '''    printf("depth: center=%u corner=%u (D16 raw)\\n",
           d[(H / 2) * W + W / 2], d[0]);'''
new = '''    if (depth32) {
        const float *df = (const float *)d;

        printf("depth32: center=%.4f corner=%.4f (expect ~0.1 / ~0.9)\\n",
               df[(H / 2) * W + W / 2], df[0]);
    } else {
        printf("depth: center=%u corner=%u (D16 raw)\\n",
               d[(H / 2) * W + W / 2], d[0]);
    }'''
assert s.count(old) == 1, 'depth print anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('vk_ds depth32 option added')
