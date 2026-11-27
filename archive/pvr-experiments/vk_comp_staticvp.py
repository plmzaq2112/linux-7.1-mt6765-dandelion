#!/usr/bin/env python3
"""vk_comp: static viewport + dynamic scissor (test whether dynamic viewport is broken)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

# vk_init takes the extent so the viewport can be static
old = 'static void vk_init(struct vk_state *v, VkFormat fmt)'
new = 'static void vk_init(struct vk_state *v, VkFormat fmt, uint32_t w, uint32_t h)'
assert s.count(old) == 1, 'vk_init signature'
s = s.replace(old, new, 1)

old = '''    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .scissorCount = 1,
    };'''
new = '''    VkViewport static_vp = { 0, 0, (float)w, (float)h, 0, 1 };
    VkRect2D static_sc = { { 0, 0 }, { w, h } };
    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .pViewports = &static_vp,
        .scissorCount = 1,
        .pScissors = &static_sc,
    };'''
assert s.count(old) == 1, 'viewport state'
s = s.replace(old, new, 1)

old = '''    VkDynamicState dyn[2] = { VK_DYNAMIC_STATE_VIEWPORT,
                              VK_DYNAMIC_STATE_SCISSOR };'''
new = '''    VkDynamicState dyn[1] = { VK_DYNAMIC_STATE_SCISSOR };'''
assert s.count(old) == 1, 'dynamic states'
s = s.replace(old, new, 1)

old = '''        .dynamicStateCount = 2,'''
new = '''        .dynamicStateCount = 1,'''
assert s.count(old) == 1, 'dynamic count'
s = s.replace(old, new, 1)

# call site
old = '    vk_init(&v, fmt);'
new = '    vk_init(&v, fmt, w, h);'
if s.count(old) == 1:
    s = s.replace(old, new, 1)

p.write_text(s)
print('static viewport applied')
