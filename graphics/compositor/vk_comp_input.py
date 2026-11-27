#!/usr/bin/env python3
"""vk_comp: touch input (drag layers around with the FT8006S touchscreen)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

# include evdev
if '#include <linux/input.h>' not in s:
    s = s.replace('#include <drm_fourcc.h>',
                  '#include <linux/input.h>\n\n#include <drm_fourcc.h>', 1)

# --- input handling, inserted before layers_init ---------------------------
anchor = 'static void layers_init(uint32_t w, uint32_t h, int n)'
input_code = r'''/* --- touch input --------------------------------------------------------- */

static int g_evfd = -1;
static int g_abs_xmax = 0;
static int g_abs_ymax = 0;
static int g_grab = -1;
static float g_grab_dx, g_grab_dy;

static int input_open(const char *forced)
{
    char path[64];
    int i;

    for (i = 0; i < 32; i++) {
        unsigned long absbits[(ABS_MAX / (8 * sizeof(unsigned long))) + 1] = { 0 };
        struct input_absinfo ai_x, ai_y;
        int fd;

        if (forced)
            snprintf(path, sizeof(path), "%s", forced);
        else
            snprintf(path, sizeof(path), "/dev/input/event%d", i);

        fd = open(path, O_RDONLY | O_NONBLOCK);
        if (fd < 0)
            continue;

        if (ioctl(fd, EVIOCGBIT(EV_ABS, sizeof(absbits)), absbits) < 0 ||
            !(absbits[ABS_MT_POSITION_X / (8 * sizeof(unsigned long))] &
              (1UL << (ABS_MT_POSITION_X % (8 * sizeof(unsigned long))))) ||
            ioctl(fd, EVIOCGABS(ABS_MT_POSITION_X), &ai_x) < 0 ||
            ioctl(fd, EVIOCGABS(ABS_MT_POSITION_Y), &ai_y) < 0) {
            close(fd);
            if (forced)
                return -1;
            continue;
        }

        g_abs_xmax = ai_x.maximum;
        g_abs_ymax = ai_y.maximum;
        printf("input: %s (abs %dx%d)\n", path, g_abs_xmax, g_abs_ymax);
        return fd;
    }
    return -1;
}

/* Returns 1 when a new touch position is available (down or move), 2 on up. */
static int input_poll(uint32_t w, uint32_t h, float *px, float *py)
{
    struct input_event ev;
    int state = 0;
    int have_pos = 0;
    static int raw_x, raw_y;
    static int touching;
    int tracking = -2;

    if (g_evfd < 0)
        return 0;

    while (read(g_evfd, &ev, sizeof(ev)) == (ssize_t)sizeof(ev)) {
        if (ev.type == EV_ABS) {
            if (ev.code == ABS_MT_POSITION_X) {
                raw_x = ev.value;
                have_pos = 1;
            } else if (ev.code == ABS_MT_POSITION_Y) {
                raw_y = ev.value;
                have_pos = 1;
            } else if (ev.code == ABS_MT_TRACKING_ID) {
                tracking = ev.value;
            }
        } else if (ev.type == EV_SYN && ev.code == SYN_REPORT) {
            if (tracking >= 0) {
                touching = 1;
                state = 1;
            } else if (tracking == -1) {
                touching = 0;
                state = 2;
            } else if (touching && have_pos) {
                state = 1;
            }
            have_pos = 0;
            tracking = -2;
        }
    }

    if (state && g_abs_xmax > 0 && g_abs_ymax > 0) {
        *px = (float)raw_x / (float)g_abs_xmax * (float)(w - 1);
        *py = (float)raw_y / (float)g_abs_ymax * (float)(h - 1);
    }
    return state;
}

static void input_handle(uint32_t w, uint32_t h)
{
    float px = 0, py = 0;
    int state = input_poll(w, h, &px, &py);

    if (!state)
        return;

    if (state == 1) {
        if (g_grab < 0) {
            /* topmost layer under the finger */
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

            l->x = px - g_grab_dx;
            l->y = py - g_grab_dy;
            if (l->x < 0) l->x = 0;
            if (l->y < 0) l->y = 0;
            if (l->x + l->w > (float)w) l->x = (float)w - l->w;
            if (l->y + l->h > (float)h) l->y = (float)h - l->h;
            l->vx = l->vy = 0.0f;
        }
    } else {
        if (g_grab >= 0)
            printf("touch: release layer %d\n", g_grab);
        g_grab = -1;
    }
}

static void layers_init(uint32_t w, uint32_t h, int n)'''
assert s.count(anchor) == 1, 'layers_init anchor'
s = s.replace(anchor, input_code, 1)

# open input after modeset / before the loop; poll each frame
old = '''    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);'''
new = '''    g_evfd = input_open(getenv("VK_COMP_INPUT"));
    if (g_evfd < 0)
        printf("input: no touch device found\\n");

    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);'''
assert s.count(old) == 1, 'input open site'
s = s.replace(old, new, 1)

old = '''            layers_step(w, h, dt);
            layers_upload(&v, w, h);'''
new = '''            input_handle(w, h);
            layers_step(w, h, dt);
            layers_upload(&v, w, h);'''
assert s.count(old) == 1, 'input poll site'
s = s.replace(old, new, 1)

p.write_text(s)
print('touch input added')
