#!/usr/bin/env python3
"""vk_kms2: frame_init_import must not wipe the DRM fb fields"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_kms2.c')
s = p.read_text()

old = '''static int frame_init_import(struct vk_state *v, struct frame *f, uint32_t w,
                             uint32_t h, VkFormat fmt, int fd)
{
    memset(f, 0, sizeof(*f));
    f->dmabuf_fd = fd;'''
new = '''static int frame_init_import(struct vk_state *v, struct frame *f, uint32_t w,
                             uint32_t h, VkFormat fmt, int fd)
{
    f->dmabuf_fd = fd;'''
assert s.count(old) == 1
p.write_text(s.replace(old, new, 1))
print('frame_init_import keeps drm_fb')
