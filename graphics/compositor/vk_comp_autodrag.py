#!/usr/bin/env python3
"""vk_comp: factor the touch maths into touch_event() + VK_COMP_AUTODRAG self-test"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

start = s.index('static void input_handle(uint32_t w, uint32_t h)')
end = s.index('static void layers_init(uint32_t w, uint32_t h, int n)')

new = r'''/* Shared by the evdev path and the self-test. */
static void touch_event(int down, float px, float py)
{
    if (down) {
        if (g_grab < 0) {
            for (int i = g_nlayers - 1; i >= 0; i--) {
                const struct layer *l = &g_layers[i];

                if (px >= l->x && px < l->x + l->w && py >= l->y &&
                    py < l->y + l->h) {
                    g_grab = i;
                    g_grab_dx = px - l->x;
                    g_grab_dy = py - l->y;
                    printf("touch: grab layer %d at %.0f,%.0f\n", i, px, py);
                    break;
                }
            }
        }
        if (g_grab >= 0) {
            struct layer *l = &g_layers[g_grab];
            float w = (float)g_frame_w, h = (float)g_frame_h;

            l->x = px - g_grab_dx;
            l->y = py - g_grab_dy;
            if (l->x < 0) l->x = 0;
            if (l->y < 0) l->y = 0;
            if (l->x + l->w > w) l->x = w - l->w;
            if (l->y + l->h > h) l->y = h - l->h;
            l->vx = l->vy = 0.0f;
        }
    } else {
        if (g_grab >= 0)
            printf("touch: release layer %d\n", g_grab);
        g_grab = -1;
    }
}

static void input_handle(uint32_t w, uint32_t h)
{
    float px = 0, py = 0;
    int state = input_poll(w, h, &px, &py);

    if (!state)
        return;

    touch_event(state == 1, px, py);
}

static void layers_init(uint32_t w, uint32_t h, int n)'''
s = s[:start] + new + s[end:]

# frame extent globals
old = '''static int g_grab = -1;
static float g_grab_dx, g_grab_dy;'''
new = '''static int g_grab = -1;
static float g_grab_dx, g_grab_dy;
static uint32_t g_frame_w, g_frame_h;'''
assert s.count(old) == 1, 'globals'
s = s.replace(old, new, 1)

# set the extent right after layers_init in the initial block
old = '''        layers_init(w, h, getenv("VK_COMP_LAYERS") ? atoi(getenv("VK_COMP_LAYERS")) : 8);
        layers_upload(&v, w, h);'''
new = '''        layers_init(w, h, getenv("VK_COMP_LAYERS") ? atoi(getenv("VK_COMP_LAYERS")) : 8);
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
        }'''
assert s.count(old) == 1, 'autodrag site'
s = s.replace(old, new, 1)

p.write_text(s)
print('touch_event + autodrag added')
