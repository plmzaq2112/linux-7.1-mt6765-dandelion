#!/usr/bin/env python3
"""Generate src/wayland/vk_wl.c (Wayland compositor) from src/wayland/vk_comp.c.

The Vulkan + KMS scaffolding is kept verbatim; the procedural layer model is
replaced by Wayland surfaces from wl/wl_backend.c.
"""
from pathlib import Path

W = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion')
src = (W / 'src/wayland/vk_comp.c').read_text()
s = src

# --- 1. includes ----------------------------------------------------------
old = '#include "comp_frag_spv.h"\n'
new = '#include "comp_frag_spv.h"\n\n#include <sys/resource.h>\n\n#include "wl/wl_backend.h"\n'
assert s.count(old) == 1
s = s.replace(old, new, 1)

# --- 2. layer model -> wl_draw_surf snapshots -----------------------------
old = """struct layer {
    float x, y, w, h;   /* pixel rect */
    float vx, vy;       /* pixels / second */
    float r, g, b, a;
};

static struct layer g_layers[MAX_LAYERS];
static int g_nlayers = 8;
"""
new = """static struct wl_draw_surf g_draw[MAX_LAYERS];
static int g_ndraw = 0;
"""
assert s.count(old) == 1, 'layer model'
s = s.replace(old, new, 1)

# --- 3. touch: forward to Wayland clients instead of dragging layers ------
start = s.index('/* Shared by the evdev path and the self-test. */')
end = s.index('static void layers_init(uint32_t w, uint32_t h, int n)')
s = s[:start] + """static void input_handle(uint32_t w, uint32_t h)
{
    float px = 0, py = 0;
    int state = input_poll(w, h, &px, &py);

    if (state)
        wl_backend_input(state == 1, px, py);
}

""" + s[end:]

# --- 4. layers_* + layer_scissor -> VBO upload + scissor -------------------
start = s.index('static void layers_init(uint32_t w, uint32_t h, int n)')
end = s.index('/* --- textures')
s = s[:start] + """/* 6 vertices per surface: pos(vec3) + uv(vec2) + colour(vec4). */
static void wl_upload_vbo(struct vk_state *v, uint32_t w, uint32_t h)
{
    float *dst = v->vbo_ptr;

    for (int i = 0; i < g_ndraw; i++) {
        const struct wl_draw_surf *l = &g_draw[i];
        float x0 = l->x / (float)w * 2.0f - 1.0f;
        float x1 = (l->x + l->w) / (float)w * 2.0f - 1.0f;
        /* Vulkan clip space: y = +1 is the *bottom* of the framebuffer. */
        float y0 = l->y / (float)h * 2.0f - 1.0f;
        float y1 = (l->y + l->h) / (float)h * 2.0f - 1.0f;
        const float q[6][4] = {
            { x0, y0, 0.0f, 0.0f }, { x1, y0, 1.0f, 0.0f },
            { x0, y1, 0.0f, 1.0f }, { x1, y0, 1.0f, 0.0f },
            { x1, y1, 1.0f, 1.0f }, { x0, y1, 0.0f, 1.0f },
        };

        for (int k = 0; k < 6; k++) {
            dst[0] = q[k][0];
            dst[1] = q[k][1];
            dst[2] = 0.0f;
            dst[3] = q[k][2];
            dst[4] = q[k][3];
            dst[5] = 1.0f;
            dst[6] = 1.0f;
            dst[7] = 1.0f;
            dst[8] = 1.0f;
            dst += 9;
        }
    }
}

/* Scissor rect (top-left origin) of a surface, clamped to the screen. */
static VkRect2D draw_scissor(const struct wl_draw_surf *l, uint32_t w,
                             uint32_t h)
{
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

""" + s[end:]

# --- 5. create_textures -> sampler + descriptor pool only -----------------
start = s.index('static int create_textures(struct vk_state *v)')
end = s.index('printf("textures: %u x %ux%u\\n", (unsigned)NUM_TEX, size, size);')
end = s.index('\n}', end) + 2
s = s[:start] + """static int create_textures(struct vk_state *v)
{
    VkSamplerCreateInfo sci = {
        .sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
        .magFilter = VK_FILTER_LINEAR,
        .minFilter = VK_FILTER_LINEAR,
        .addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        .addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
    };
    CHECK_VK(vkCreateSampler(v->dev, &sci, NULL, &v->sampler));

    VkDescriptorPoolSize psz = {
        .type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .descriptorCount = MAX_LAYERS,
    };
    VkDescriptorPoolCreateInfo dpci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        .maxSets = MAX_LAYERS,
        .poolSizeCount = 1,
        .pPoolSizes = &psz,
    };
    CHECK_VK(vkCreateDescriptorPool(v->dev, &dpci, NULL, &v->dpool));

    printf("textures: %u surface slots, %ux%u max\\n", (unsigned)MAX_LAYERS,
           4096u, 4096u);
    return 0;
}""" + s[end:]

# --- 6. draw loops -------------------------------------------------------
s = s.replace('for (int d = 0; d < g_nlayers; d++) {',
              'for (int d = 0; d < g_ndraw; d++) {')
s = s.replace('for (int d = 0; d < (clear_only ? 0 : g_nlayers); d++) {',
              'for (int d = 0; d < (clear_only ? 0 : g_ndraw); d++) {')

old = """            VkRect2D dsc = layer_scissor(d, w, h);

            if (!dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets(
                v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.layout, 0, 1,
                &v.tex_set[d % NUM_TEX], 0, NULL);
"""
new = """            const struct wl_draw_surf *l = &g_draw[d];
            VkRect2D dsc = draw_scissor(l, w, h);

            if (!l->tex || !dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets(
                v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.layout, 0, 1,
                &l->tex, 0, NULL);
"""
assert s.count(old) == 2, 'draw bodies'
s = s.replace(old, new)

# --- 7b. LOAD render pass + damage helpers ------------------------------
old = """    VkPipeline pipe;
    VkRenderPass rp;
"""
new = """    VkPipeline pipe;
    VkRenderPass rp;
    VkRenderPass rp_load;
"""
assert s.count(old) == 1, 'vk_state render pass'
s = s.replace(old, new, 1)

old = '    CHECK_VK(vkCreateRenderPass(v->dev, &rpci, NULL, &v->rp));\n'
new = ('    CHECK_VK(vkCreateRenderPass(v->dev, &rpci, NULL, &v->rp));\n'
       '    /* Same pass, but preserve contents so a slot can be redrawn\n'
       '     * partially (damage tracking). */\n'
       '    att.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;\n'
       '    att.initialLayout = VK_IMAGE_LAYOUT_GENERAL;\n'
       '    CHECK_VK(vkCreateRenderPass(v->dev, &rpci, NULL, &v->rp_load));\n')
assert s.count(old) == 1, 'render pass create'
s = s.replace(old, new, 1)

old = 'int main(void)\n{\n'
new = """struct wl_damage {
    int32_t x0, y0, x1, y1;
};

static void dmg_reset(struct wl_damage *d)
{
    d->x0 = 1 << 30;
    d->y0 = 1 << 30;
    d->x1 = -1;
    d->y1 = -1;
}

static void dmg_union(struct wl_damage *d, int32_t x0, int32_t y0, int32_t x1,
                      int32_t y1)
{
    if (x1 <= x0 || y1 <= y0)
        return;
    if (x0 < d->x0) d->x0 = x0;
    if (y0 < d->y0) d->y0 = y0;
    if (x1 > d->x1) d->x1 = x1;
    if (y1 > d->y1) d->y1 = y1;
}

static int dmg_empty(const struct wl_damage *d)
{
    return d->x1 <= d->x0 || d->y1 <= d->y0;
}

static VkRect2D rect_intersect(VkRect2D a, VkRect2D b)
{
    int32_t x0 = a.offset.x > b.offset.x ? a.offset.x : b.offset.x;
    int32_t y0 = a.offset.y > b.offset.y ? a.offset.y : b.offset.y;
    int32_t x1 = (a.offset.x + (int32_t)a.extent.width) <
                         (b.offset.x + (int32_t)b.extent.width)
                     ? (a.offset.x + (int32_t)a.extent.width)
                     : (b.offset.x + (int32_t)b.extent.width);
    int32_t y1 = (a.offset.y + (int32_t)a.extent.height) <
                         (b.offset.y + (int32_t)b.extent.height)
                     ? (a.offset.y + (int32_t)a.extent.height)
                     : (b.offset.y + (int32_t)b.extent.height);

    if (x1 < x0) x1 = x0;
    if (y1 < y0) y1 = y0;
    return (VkRect2D){ { x0, y0 },
                       { (uint32_t)(x1 - x0), (uint32_t)(y1 - y0) } };
}

int main(void)
{
"""
assert s.count(old) == 1, 'main anchor'
s = s.replace(old, new, 1)

# --- 7c. per-slot damage state -------------------------------------------
old = """    int busy[NSLOT] = { 1, 0, 0 };
    int onscreen = 0;
    int pending = -1;
    int next_slot = 1;
"""
new = """    int busy[NSLOT] = { 1, 0, 0 };
    int onscreen = 0;
    int pending = -1;
    int next_slot = 1;
    int slot_valid[NSLOT] = { 0 };
    struct wl_damage slot_dmg[NSLOT];
    VkRenderPass frame_rp = v.rp;
    unsigned long long idle_frames = 0;
    int idle_run = 0;

    for (int k = 0; k < NSLOT; k++)
        dmg_reset(&slot_dmg[k]);
"""
assert s.count(old) == 1, 'slot state'
s = s.replace(old, new, 1)

# --- 7d. all render passes go through frame_rp ---------------------------
old = '            .renderPass = v.rp,\n'
assert s.count(old) == 2, 'render pass refs'
s = s.replace(old, '            .renderPass = frame_rp,\n')

# --- 7e. the initial frame leaves slot 0 valid --------------------------
old = """        if (!zero_copy) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }
    }
"""
new = """        if (!zero_copy) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }
        slot_valid[0] = 1;
    }
"""
assert s.count(old) == 1, 'initial frame end'
s = s.replace(old, new, 1)

old = '        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));\n'
new = ('        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));\n'
       '        wl_backend_prepare(v.cmd);\n')
assert s.count(old) == 2, 'begin command buffer'
s = s.replace(old, new)

# --- 8. startup: bring up the Wayland server ----------------------------
old = """        layers_init(w, h, getenv("VK_COMP_LAYERS") ? atoi(getenv("VK_COMP_LAYERS")) : 8);
        g_frame_w = w;
        g_frame_h = h;
        layers_upload(&v, w, h);

        if (getenv("VK_COMP_AUTODRAG")) {
            float x0 = g_layers[0].x, y0 = g_layers[0].y;

            touch_event(1, x0 + 10.0f, y0 + 10.0f);
            touch_event(1, x0 + 50.0f, y0 + 40.0f);
            touch_event(0, 0.0f, 0.0f);
            printf("autodrag: layer0 (%.0f,%.0f) -> (%.0f,%.0f), expect +40,+30\\n",
                   x0, y0, g_layers[0].x, g_layers[0].y);
        }
"""
new = """        struct wl_backend_cfg wcfg = {
            .fb_width = w,
            .fb_height = h,
            .pd = v.pd,
            .dev = v.dev,
            .dsl = v.dsl,
            .dpool = v.dpool,
            .sampler = v.sampler,
            .get_fd_props = v.get_fd_props,
        };

        if (wl_backend_init(&wcfg))
            return 1;
        g_ndraw = wl_backend_collect(g_draw, MAX_LAYERS);
        wl_upload_vbo(&v, w, h);
"""
assert s.count(old) == 1, 'startup'
s = s.replace(old, new, 1)

# --- 9. per-frame: pump clients, damage, idle, collect, upload ----------
old = """        /* Pick a buffer that is neither on screen nor awaiting a flip. */
        int i = -1;
        for (int k = 0; k < NSLOT; k++) {
            int idx = (next_slot + k) % NSLOT;
            if (!busy[idx]) {
                i = idx;
                break;
            }
        }
        if (i < 0)
            break;
        next_slot = (i + 1) % NSLOT;

        struct frame *f = &fr[i];
        {
            static double last_t;
            float dt = (float)(elapsed - last_t);

            if (dt > 0.1f)
                dt = 0.1f;
            last_t = elapsed;
            input_handle(w, h);
            layers_step(w, h, dt);
            layers_upload(&v, w, h);
        }
"""
new = """        wl_backend_pump();
        input_handle(w, h);
        if (getenv("VK_WL_FAKE_TOUCH") && frames == 240) {
            wl_backend_input(1, 100.0f, 250.0f);
            wl_backend_input(1, 130.0f, 280.0f);
            wl_backend_input(1, 160.0f, 310.0f);
            wl_backend_input(0, 160.0f, 310.0f);
            printf("wl: fake touch drag +60,+60\\n");
        }

        /* Nothing changed and nobody waits for a frame: keep the last
         * frame on screen and sleep in the event loop (vsync-rate power). */
        if (pending < 0 && !wl_backend_needs_frame() &&
            !getenv("VK_WL_NOIDLE")) {
            idle_frames++;
            wl_backend_wait(getenv("VK_WL_IDLE_MS")
                                ? atoi(getenv("VK_WL_IDLE_MS"))
                                : 16);
            continue;
        }
        wl_backend_frame((uint32_t)(elapsed * 1000.0));

        /* Pick a buffer that is neither on screen nor awaiting a flip. */
        int i = -1;
        for (int k = 0; k < NSLOT; k++) {
            int idx = (next_slot + k) % NSLOT;
            if (!busy[idx]) {
                i = idx;
                break;
            }
        }
        if (i < 0)
            break;
        next_slot = (i + 1) % NSLOT;

        struct frame *f = &fr[i];
        struct wl_damage cur, dmg;
        int32_t d4[4];
        int full;

        g_ndraw = wl_backend_collect(g_draw, MAX_LAYERS);
        wl_upload_vbo(&v, w, h);

        dmg_reset(&cur);
        if (wl_backend_take_damage(d4)) {
            dmg_union(&cur, d4[0], d4[1], d4[2], d4[3]);
        }

        dmg = slot_dmg[i];
        dmg_union(&dmg, cur.x0, cur.y0, cur.x1, cur.y1);
        full = !slot_valid[i] || getenv("VK_WL_FULLREDRAW") != NULL;
        if (full) {
            dmg.x0 = 0;
            dmg.y0 = 0;
            dmg.x1 = (int32_t)w;
            dmg.y1 = (int32_t)h;
        }
        if (dmg_empty(&dmg)) {
            /* Keep the vsync cadence while the session is active (the old
             * behaviour), and only go idle after ~1 s without any damage. */
            if (idle_run++ < 60) {
                full = 1;
                dmg.x0 = 0;
                dmg.y0 = 0;
                dmg.x1 = (int32_t)w;
                dmg.y1 = (int32_t)h;
            } else if (pending < 0) {
                continue;
            } else {
                i = -1;
                goto present;
            }
        } else {
            idle_run = 0;
        }
        frame_rp = full ? v.rp : v.rp_load;
"""
assert s.count(old) == 1, 'per-frame'
s = s.replace(old, new, 1)

# --- 9b. partial redraw: clear + clip to the damage rect ----------------
old = """        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        for (int d = 0; d < (clear_only ? 0 : g_ndraw); d++) {
            const struct wl_draw_surf *l = &g_draw[d];
            VkRect2D dsc = draw_scissor(l, w, h);

            if (!l->tex || !dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
"""
new = """        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        VkRect2D drect = { { dmg.x0, dmg.y0 },
                           { (uint32_t)(dmg.x1 - dmg.x0),
                             (uint32_t)(dmg.y1 - dmg.y0) } };
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        if (!full) {
            /* Preserved slot: repaint the background only under damage. */
            VkClearAttachment ca = {
                .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
                .colorAttachment = 0,
                .clearValue = cv,
            };
            VkClearRect cr = { drect, 0, 1 };

            vkCmdSetScissor(v.cmd, 0, 1, &drect);
            vkCmdClearAttachments(v.cmd, 1, &ca, 1, &cr);
        }
        for (int d = 0; d < (clear_only ? 0 : g_ndraw); d++) {
            const struct wl_draw_surf *l = &g_draw[d];
            VkRect2D dsc = draw_scissor(l, w, h);

            dsc = rect_intersect(dsc, drect);
            if (!l->tex || !dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
"""
assert s.count(old) == 1, 'partial redraw'
s = s.replace(old, new, 1)

# --- 9c. per-slot damage bookkeeping ------------------------------------
old = """        busy[i] = 1;
"""
new = """        busy[i] = 1;
        slot_valid[i] = 1;
        dmg_reset(&slot_dmg[i]);
        for (int k = 0; k < NSLOT; k++)
            if (k != i && slot_valid[k])
                dmg_union(&slot_dmg[k], cur.x0, cur.y0, cur.x1, cur.y1);
"""
assert s.count(old) == 1, 'slot bookkeeping'
s = s.replace(old, new, 1)

# --- 9d. presentation is independent of rendering ----------------------
old = '        /* Present the previous frame: its render had a whole flip period. */\n'
new = ('    present:\n'
       '        /* Present the previous frame: its render had a whole flip period. */\n')
assert s.count(old) == 1, 'present label'
s = s.replace(old, new, 1)

assert s.count(old) == 1, 'submit counter'

# --- 9e. frame callbacks after presentation (gives clients a full vblank)
old = '        pending = i;\n'
new = '        pending = i;\n'
assert s.count(old) == 1, 'pending assign'


# --- 10. stats + verify --------------------------------------------------
s = s.replace('printf("layers=%d\\n", g_nlayers);',
              'printf("surfaces=%d\\n", g_ndraw);')
s = s.replace('printf("verify: onscreen=%d layers=%d corner=%08x\\n",\n'
              '                       onscreen, g_nlayers, corner);',
              'printf("verify: onscreen=%d surfaces=%d corner=%08x\\n",\n'
              '                       onscreen, g_ndraw, corner);')

old = """                printf("verify: layer0 rect=(%.0f,%.0f %.0fx%.0f)\\n",
                       g_layers[0].x, g_layers[0].y, g_layers[0].w,
                       g_layers[0].h);
                {
                    int cx = (int)(g_layers[0].x + g_layers[0].w / 2);
                    int cy = (int)(g_layers[0].y + g_layers[0].h / 2);

                    if (cx < 0) cx = 0;
                    if (cy < 0) cy = 0;
                    if (cx >= (int)w) cx = (int)w - 1;
                    if (cy >= (int)h) cy = (int)h - 1;
                    printf("verify: layer0 centre (%d,%d) = %08x, (0,0)=%08x\\n",
                           cx, cy, px[(size_t)cy * stride + cx],
                           px[0]);
                }
"""
new = """                for (int si = 0; si < g_ndraw; si++) {
                    int cx = (int)(g_draw[si].x + g_draw[si].w / 2);
                    int cy = (int)(g_draw[si].y + g_draw[si].h / 2);
                    int tx = (int)(g_draw[si].x + 6);
                    int ty = (int)(g_draw[si].y + 6);
                    int by = (int)(g_draw[si].y + g_draw[si].h - 6);

                    if (cx < 0) cx = 0;
                    if (cy < 0) cy = 0;
                    if (cx >= (int)w) cx = (int)w - 1;
                    if (cy >= (int)h) cy = (int)h - 1;
                    if (tx < 0) tx = 0;
                    if (ty < 0) ty = 0;
                    if (by < 0) by = 0;
                    if (tx >= (int)w) tx = (int)w - 1;
                    if (ty >= (int)h) ty = (int)h - 1;
                    if (by >= (int)h) by = (int)h - 1;
                    printf("verify: surf%d rect=(%.0f,%.0f %.0fx%.0f) centre=(%d,%d) %08x  marker top=%08x bottom=%08x\\n",
                           si, g_draw[si].x, g_draw[si].y, g_draw[si].w,
                           g_draw[si].h, cx, cy,
                           px[(size_t)cy * stride + cx],
                           px[(size_t)ty * stride + tx],
                           px[(size_t)by * stride + tx]);
                }
"""
assert s.count(old) == 1, 'verify block'
s = s.replace(old, new, 1)

# --- 11. CPU / idle stats (power evidence) -------------------------------
old = """    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\\n",
           (unsigned long long)frames, total, frames / total,
           zero_copy ? "zero-copy" : "cpu-copy");
"""
new = """    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\\n",
           (unsigned long long)frames, total, frames / total,
           zero_copy ? "zero-copy" : "cpu-copy");
    {
        struct rusage ru;
        double cpu;

        getrusage(RUSAGE_SELF, &ru);
        cpu = ru.ru_utime.tv_sec + ru.ru_stime.tv_sec +
              (ru.ru_utime.tv_usec + ru.ru_stime.tv_usec) / 1e6;
        printf("cpu: %.2fs over %.2fs (%.1f%%), idle frames %llu\\n", cpu,
               total, 100.0 * cpu / (total > 0.0 ? total : 1.0), idle_frames);
    }
"""
assert s.count(old) == 1, 'cpu stats'
s = s.replace(old, new, 1)

(W / 'src/wayland/vk_wl.c').write_text(s)
print('vk_wl.c generated from vk_comp.c (%d lines)' % s.count('\n'))
