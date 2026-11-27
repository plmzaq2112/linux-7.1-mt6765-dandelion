#!/usr/bin/env python3
"""vk_comp: multi-layer compositor (per-layer scissor + alpha blend)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

# 1. shaders
s = s.replace('#include "color_vert_spv.h"', '#include "ds_vert_spv.h"', 1)
s = s.replace('#include "color_frag_spv.h"', '#include "ds_frag_spv.h"', 1)
s = s.replace('v->vs = make_shader(v->dev, color_vert_spv, color_vert_spv_len);',
              'v->vs = make_shader(v->dev, ds_vert_spv, ds_vert_spv_len);', 1)
s = s.replace('v->fs = make_shader(v->dev, color_frag_spv, color_frag_spv_len);',
              'v->fs = make_shader(v->dev, ds_frag_spv, ds_frag_spv_len);', 1)

# 2. vertex layout: vec3 pos + vec4 colour
old = '''    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 5 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[2] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32_SFLOAT,
          .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32B32_SFLOAT,
          .offset = 2 * sizeof(float) },
    };'''
new = '''    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 7 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[2] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32B32_SFLOAT,
          .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32B32A32_SFLOAT,
          .offset = 3 * sizeof(float) },
    };'''
assert s.count(old) == 1, 'vertex input'
s = s.replace(old, new, 1)

# 3. alpha blending
old = '''    VkPipelineColorBlendAttachmentState cba = {
        .blendEnable = VK_FALSE,
        .colorWriteMask = 0xf,
    };'''
new = '''    VkPipelineColorBlendAttachmentState cba = {
        .blendEnable = VK_TRUE,
        .srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA,
        .dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        .colorBlendOp = VK_BLEND_OP_ADD,
        .srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE,
        .dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        .alphaBlendOp = VK_BLEND_OP_ADD,
        .colorWriteMask = 0xf,
    };'''
assert s.count(old) == 1, 'blend state'
s = s.replace(old, new, 1)

# 4. VBO size for MAX_LAYERS
s = s.replace('#ifndef NSLOT\n#define NSLOT 3\n#endif',
              '#ifndef NSLOT\n#define NSLOT 3\n#endif\n\n#define MAX_LAYERS 16', 1)
old = '        .size = 6 * 5 * sizeof(float),'
new = '        .size = MAX_LAYERS * 6 * 7 * sizeof(float),'
assert s.count(old) == 1, 'vbo size'
s = s.replace(old, new, 1)

# 5. replace build_scene with the layer model
start = s.index('static void build_scene(struct vk_state *v, float t)')
end = s.index('int main(void)')
layers = r'''#define MAX_LAYERS 16

struct layer {
    float x, y, w, h;   /* pixel rect */
    float vx, vy;       /* pixels / second */
    float r, g, b, a;
};

static struct layer g_layers[MAX_LAYERS];
static int g_nlayers = 8;

static void layers_init(uint32_t w, uint32_t h, int n)
{
    if (n < 1)
        n = 1;
    if (n > MAX_LAYERS)
        n = MAX_LAYERS;
    g_nlayers = n;

    for (int i = 0; i < n; i++) {
        struct layer *l = &g_layers[i];

        l->w = (float)(w / 4);
        l->h = (float)(h / 8);
        l->x = (float)((i % 3) * (w / 4) + 8);
        l->y = (float)((i / 3) * (h / 8) + 8);
        l->vx = 30.0f + 7.0f * i;
        l->vy = 20.0f + 5.0f * i;
        l->r = (i % 3) == 0 ? 1.0f : 0.15f;
        l->g = (i % 3) == 1 ? 1.0f : 0.25f;
        l->b = (i % 3) == 2 ? 1.0f : 0.85f;
        l->a = 0.7f;
    }
}

static void layers_step(uint32_t w, uint32_t h, float dt)
{
    for (int i = 0; i < g_nlayers; i++) {
        struct layer *l = &g_layers[i];

        l->x += l->vx * dt;
        l->y += l->vy * dt;
        if (l->x < 0.0f) {
            l->x = 0.0f;
            l->vx = -l->vx;
        }
        if (l->y < 0.0f) {
            l->y = 0.0f;
            l->vy = -l->vy;
        }
        if (l->x + l->w > (float)w) {
            l->x = (float)w - l->w;
            l->vx = -l->vx;
        }
        if (l->y + l->h > (float)h) {
            l->y = (float)h - l->h;
            l->vy = -l->vy;
        }
    }
}

/* 6 vertices per layer, pos(vec3) + colour(vec4). */
static void layers_upload(struct vk_state *v, uint32_t w, uint32_t h)
{
    float *dst = v->vbo_ptr;

    for (int i = 0; i < g_nlayers; i++) {
        const struct layer *l = &g_layers[i];
        float x0 = l->x / (float)w * 2.0f - 1.0f;
        float x1 = (l->x + l->w) / (float)w * 2.0f - 1.0f;
        float y0 = 1.0f - l->y / (float)h * 2.0f;
        float y1 = 1.0f - (l->y + l->h) / (float)h * 2.0f;
        const float q[6][2] = {
            { x0, y0 }, { x1, y0 }, { x0, y1 },
            { x1, y0 }, { x1, y1 }, { x0, y1 },
        };

        for (int k = 0; k < 6; k++) {
            dst[0] = q[k][0];
            dst[1] = q[k][1];
            dst[2] = 0.0f;
            dst[3] = l->r;
            dst[4] = l->g;
            dst[5] = l->b;
            dst[6] = l->a;
            dst += 7;
        }
    }
}

/* Scissor rect (top-left origin) of layer i, clamped to the screen. */
static VkRect2D layer_scissor(int i, uint32_t w, uint32_t h)
{
    const struct layer *l = &g_layers[i];
    int32_t x = (int32_t)l->x;
    int32_t y = (int32_t)l->y;
    int32_t x1 = (int32_t)(l->x + l->w);
    int32_t y1 = (int32_t)(l->y + l->h);

    if (x < 0)
        x = 0;
    if (y < 0)
        y = 0;
    if (x1 > (int32_t)w)
        x1 = (int32_t)w;
    if (y1 > (int32_t)h)
        y1 = (int32_t)h;
    return (VkRect2D){
        { x, y },
        { (uint32_t)(x1 > x ? x1 - x : 0), (uint32_t)(y1 > y ? y1 - y : 0) },
    };
}

'''
s = s[:start] + layers + s[end:]

# 6. calls: init after w/h known, step/upload in the loop
s = s.replace('        build_scene(&v, 0.0f);',
              '        layers_init(w, h, getenv("VK_COMP_LAYERS") ? atoi(getenv("VK_COMP_LAYERS")) : 8);\n'
              '        layers_upload(&v, w, h);', 1)

old = '''        build_scene(&v, (float)elapsed * 0.8f);'''
new = '''        {
            static double last_t;
            float dt = (float)(elapsed - last_t);

            if (dt > 0.1f)
                dt = 0.1f;
            last_t = elapsed;
            layers_step(w, h, dt);
            layers_upload(&v, w, h);
        }'''
assert s.count(old) == 1, 'scene call'
s = s.replace(old, new, 1)

# 7. per-layer draw with its own scissor (render loop)
old = '''        for (int d = 0; d < (clear_only ? 0 : draws_per_frame); d++) {
            VkViewport dvp = { (float)(d * 4), (float)(d * 4),
                               (float)(w / 2), (float)(h / 2), 0, 1 };
            VkRect2D dsc = { { d * 4, d * 4 }, { w / 2, h / 2 } };
            vkCmdSetViewport(v.cmd, 0, 1, &dvp);
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdDraw(v.cmd, 6, 1, 0, 0);
        }'''
new = '''        for (int d = 0; d < (clear_only ? 0 : g_nlayers); d++) {
            VkRect2D dsc = layer_scissor(d, w, h);

            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetViewport(v.cmd, 0, 1, &vp);
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdDraw(v.cmd, 6, 1, (uint32_t)d * 6, 0);
        }'''
assert s.count(old) == 1, 'layer draw loop'
s = s.replace(old, new, 1)

# 8. initial frame: draw all layers
old = '''        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        vkCmdSetScissor(v.cmd, 0, 1, &sc);
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        vkCmdDraw(v.cmd, 6, 1, 0, 0);'''
new = '''        vkCmdSetViewport(v.cmd, 0, 1, &vp);
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        for (int d = 0; d < g_nlayers; d++) {
            VkRect2D dsc = layer_scissor(d, w, h);

            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdDraw(v.cmd, 6, 1, (uint32_t)d * 6, 0);
        }'''
assert s.count(old) == 1, 'initial draw'
s = s.replace(old, new, 1)

# 9. report layer count
old = '''    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\\n",'''
new = '''    printf("layers=%d\\n", g_nlayers);
    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\\n",'''
assert s.count(old) == 1, 'summary'
s = s.replace(old, new, 1)

p.write_text(s)
print('vk_comp patched into a multi-layer compositor')
