#!/usr/bin/env python3
"""vk_geom: VK_GEOM_DYNSC=1 uses dynamic viewport/scissor (to dump the PPP state)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_geom.c')
s = p.read_text()

old = '''    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .pViewports = &vp,
        .scissorCount = 1,
        .pScissors = &sc,
    };'''
new = '''    const int dyn_sc = getenv("VK_GEOM_DYNSC") != NULL;
    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .pViewports = dyn_sc ? NULL : &vp,
        .scissorCount = 1,
        .pScissors = dyn_sc ? NULL : &sc,
    };
    VkDynamicState dyn_states[2] = { VK_DYNAMIC_STATE_VIEWPORT,
                                     VK_DYNAMIC_STATE_SCISSOR };
    VkPipelineDynamicStateCreateInfo dyn_ci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO,
        .dynamicStateCount = dyn_sc ? 2 : 0,
        .pDynamicStates = dyn_states,
    };'''
assert s.count(old) == 1, 'viewport state'
s = s.replace(old, new, 1)

old = '''        .pColorBlendState = &cb,
        .layout = pl,
        .renderPass = rp,
        .subpass = 0,
    };'''
new = '''        .pColorBlendState = &cb,
        .pDynamicState = dyn_sc ? &dyn_ci : NULL,
        .layout = pl,
        .renderPass = rp,
        .subpass = 0,
    };'''
assert s.count(old) == 1, 'pipeline create'
s = s.replace(old, new, 1)

old = '''    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe);'''
new = '''    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe);
    if (dyn_sc) {
        vkCmdSetViewport(cmd, 0, 1, &vp);
        vkCmdSetScissor(cmd, 0, 1, &sc);
    }'''
assert s.count(old) == 1, 'bind pipeline'
s = s.replace(old, new, 1)

p.write_text(s)
print('vk_geom dynamic-scissor knob added')
