/*
 * Wayland test client for the vk_wl compositor.
 *
 * Creates N xdg_toplevel windows with animated shm buffers and prints the
 * configure / pointer events it receives.  This is a normal libwayland-client
 * program: it speaks wl_compositor, wl_shm, wl_seat, wl_output and xdg-shell.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/syscall.h>

#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"
#include "linux-dmabuf-unstable-v1-client-protocol.h"

#include <xkbcommon/xkbcommon.h>
#include <xf86drm.h>
#include <drm_fourcc.h>
#include <sys/ioctl.h>
#include <fcntl.h>

#define MAX_SURF 8

struct shmbuf {
    struct wl_buffer *buf;
    uint32_t *px;
    size_t size;
    int w, h, stride;
    int dmabuf;
    uint32_t dumb_handle;
};

struct surf {
    struct wl_surface *surface;
    struct xdg_surface *xdg;
    struct xdg_toplevel *top;
    struct shmbuf bufs[2];
    int nbuf;
    int cur;
    int configured;
    int index;
    uint32_t bg;        /* ARGB */
    uint32_t phase;     /* animation */
    struct wl_callback *frame_cb;
};

static struct wl_display *dpy;
static struct wl_compositor *comp;
static struct wl_shm *shm;
static struct wl_seat *seat;
static struct wl_pointer *pointer;
static struct wl_keyboard *keyboard;
static struct xkb_context *xkb_ctx;
static struct xkb_keymap *xkb_keymap;
static struct xkb_state *xkb_state;
static struct wl_output *output;
static struct xdg_wm_base *wm_base;
static struct zwp_linux_dmabuf_v1 *dmabuf = NULL;
static struct surf surfs[MAX_SURF];
static int nsurf = 3;
static int running = 1;
static int use_dmabuf = 0;
static int drm_fd = -1;
static int g_static = 0;
static int g_partial = 0;
static int g_freerun = 0;
static unsigned long g_commits = 0;
static unsigned g_block_n = 0;

static const uint32_t colors[4] = { 0xff2060c0, 0xff30a060, 0xffc04040,
                                    0xff8040c0 };

static int create_shm(struct shmbuf *b, int w, int h)
{
    int stride = w * 4;
    size_t size = (size_t)stride * (size_t)h;
    int fd = (int)syscall(SYS_memfd_create, "wl-test", 1 /* MFD_CLOEXEC */);
    void *p;
    struct wl_shm_pool *pool;

    if (fd < 0) {
        fprintf(stderr, "client: memfd_create: %s\n", strerror(errno));
        return -1;
    }
    if (ftruncate(fd, (off_t)size)) {
        fprintf(stderr, "client: ftruncate: %s\n", strerror(errno));
        close(fd);
        return -1;
    }
    p = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) {
        fprintf(stderr, "client: mmap: %s\n", strerror(errno));
        close(fd);
        return -1;
    }
    pool = wl_shm_create_pool(shm, fd, (int32_t)size);
    b->buf = wl_shm_pool_create_buffer(pool, 0, w, h, stride,
                                       WL_SHM_FORMAT_ARGB8888);
    wl_shm_pool_destroy(pool);
    close(fd);

    b->px = p;
    b->size = size;
    b->w = w;
    b->h = h;
    b->stride = stride;
    return 0;
}

static int create_dmabuf(struct shmbuf *b, int w, int h)
{
    struct drm_mode_create_dumb cd = { .width = w, .height = h, .bpp = 32 };
    struct drm_mode_map_dumb md;
    struct zwp_linux_buffer_params_v1 *params;
    void *p;
    int fd = -1;

    if (drm_fd < 0) {
        fprintf(stderr, "client: no DRM fd\n");
        return -1;
    }
    if (ioctl(drm_fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
        fprintf(stderr, "client: CREATE_DUMB: %s\n", strerror(errno));
        return -1;
    }
    memset(&md, 0, sizeof(md));
    md.handle = cd.handle;
    if (ioctl(drm_fd, DRM_IOCTL_MODE_MAP_DUMB, &md)) {
        fprintf(stderr, "client: MAP_DUMB: %s\n", strerror(errno));
        return -1;
    }
    p = mmap(NULL, cd.size, PROT_READ | PROT_WRITE, MAP_SHARED, drm_fd,
             md.offset);
    if (p == MAP_FAILED) {
        fprintf(stderr, "client: mmap dumb: %s\n", strerror(errno));
        return -1;
    }
    if (drmPrimeHandleToFD(drm_fd, cd.handle, DRM_CLOEXEC, &fd)) {
        fprintf(stderr, "client: PrimeHandleToFD failed\n");
        return -1;
    }

    params = zwp_linux_dmabuf_v1_create_params(dmabuf);
    zwp_linux_buffer_params_v1_add(params, fd, 0, 0, (int32_t)cd.pitch,
                                   0 /* LINEAR */, 0);
    b->buf = zwp_linux_buffer_params_v1_create_immed(
        params, w, h,
        getenv("WL_CLIENT_XRGB") ? DRM_FORMAT_XRGB8888 : DRM_FORMAT_ARGB8888,
        0);
    zwp_linux_buffer_params_v1_destroy(params);
    close(fd);

    b->px = p;
    b->size = cd.size;
    b->w = w;
    b->h = h;
    b->stride = (int)cd.pitch;
    b->dmabuf = 1;
    b->dumb_handle = cd.handle;
    printf("client: dmabuf %dx%d pitch=%u (dumb handle %u)\n", w, h, cd.pitch,
           cd.handle);
    return 0;
}

static int create_buffer(struct shmbuf *b, int w, int h)
{
    return use_dmabuf ? create_dmabuf(b, w, h) : create_shm(b, w, h);
}

static void paint(struct surf *s, struct shmbuf *b)
{
    uint32_t *px = b->px;
    int w = b->w, h = b->h;
    int bar = (int)(s->phase % (uint32_t)w);
    int x, y;

    for (y = 0; y < h; y++) {
        for (x = 0; x < w; x++) {
            uint32_t v = s->bg;

            /* moving vertical bar */
            if (x >= bar && x < bar + 24)
                v = 0xffffffff;
            /* 2 px border */
            if (x < 2 || y < 2 || x >= w - 2 || y >= h - 2)
                v = 0xff000000;
            /* orientation marker: top-left 20x20 square */
            if (x < 20 && y < 20)
                v = 0xffffe000;
            px[(size_t)y * (b->stride / 4) + x] = v;
        }
    }
}

static void frame_done(void *data, struct wl_callback *cb, uint32_t time);

static const struct wl_callback_listener frame_listener = {
    .done = frame_done,
};

static void submit(struct surf *s);

static void frame_done(void *data, struct wl_callback *cb, uint32_t time)
{
    struct surf *s = data;

    (void)time;
    wl_callback_destroy(cb);
    s->frame_cb = NULL;
    s->phase += 6;
    submit(s);
}

static void submit(struct surf *s)
{
    struct shmbuf *b;

    if (!s->configured || s->nbuf == 0)
        return;
    s->cur = (s->cur + 1) % s->nbuf;
    b = &s->bufs[s->cur];
    if (g_partial) {
        /* Damage test: paint one new 8x8 block per frame, damage only it.
         * If the compositor drops damage, blocks go missing and the three
         * scanout slots stop matching. */
        int bx = 8 + (int)(g_block_n % 24) * 8;
        int by = 48;
        uint32_t col = 0xff000000 | (uint32_t)(0x101010 * (g_block_n % 12));

        if (bx + 8 > b->w)
            bx = 8;
        int first = (g_block_n == 0);

        for (int y = 0; y < 8; y++)
            for (int x = 0; x < 8; x++)
                b->px[(size_t)(by + y) * (b->stride / 4) + bx + x] = col;
        g_block_n++;
        wl_surface_attach(s->surface, b->buf, 0, 0);
        if (first)
            wl_surface_damage(s->surface, 0, 0, b->w, b->h);
        else
            wl_surface_damage(s->surface, bx, by, 8, 8);
    } else {
        paint(s, b);
        wl_surface_attach(s->surface, b->buf, 0, 0);
        wl_surface_damage_buffer(s->surface, 0, 0, b->w, b->h);
    }
    if (!g_static && !g_freerun) {
        s->frame_cb = wl_surface_frame(s->surface);
        wl_callback_add_listener(s->frame_cb, &frame_listener, s);
    }
    wl_surface_commit(s->surface);
    if (g_static && s == &surfs[0])
        printf("client: static mode, one frame committed\n");
    g_commits++;
}

static void xdg_surface_configure(void *data, struct xdg_surface *xdg,
                                  uint32_t serial)
{
    struct surf *s = data;

    printf("client: surf%d configure serial=%u\n", s->index, serial);
    xdg_surface_ack_configure(xdg, serial);
    if (!s->configured) {
        int bw = use_dmabuf ? 256 + 64 * s->index : 200 + 40 * s->index;
        int bh = use_dmabuf ? 160 + 32 * s->index : 150 + 30 * s->index;

        s->configured = 1;
        s->nbuf = g_partial ? 1 : 2;
        create_buffer(&s->bufs[0], bw, bh);
        if (s->nbuf > 1)
            create_buffer(&s->bufs[1], bw, bh);
        if (g_partial) {
            /* one full paint, then only per-block damage */
            paint(s, &s->bufs[0]);
        }
        submit(s);
    } else {
        submit(s);
    }
}

static const struct xdg_surface_listener xdg_surface_listener = {
    .configure = xdg_surface_configure,
};

static void top_configure(void *data, struct xdg_toplevel *top, int32_t w,
                          int32_t h, struct wl_array *states)
{
    struct surf *s = data;

    (void)top;
    printf("client: surf%d toplevel configure %dx%d (%u states)\n", s->index,
           w, h, (unsigned)(states->size / sizeof(uint32_t)));
}

static void top_close(void *data, struct xdg_toplevel *top)
{
    struct surf *s = data;

    (void)top;
    printf("client: surf%d close requested\n", s->index);
    s->configured = 0;
    running = 0;
}

static void top_bounds(void *data, struct xdg_toplevel *top, int32_t w,
                       int32_t h)
{
    (void)data; (void)top; (void)w; (void)h;
}

static void top_caps(void *data, struct xdg_toplevel *top, struct wl_array *c)
{
    (void)data; (void)top; (void)c;
}

static const struct xdg_toplevel_listener top_listener = {
    .configure = top_configure,
    .close = top_close,
    .configure_bounds = top_bounds,
    .wm_capabilities = top_caps,
};

static void ptr_enter(void *data, struct wl_pointer *p, uint32_t serial,
                      struct wl_surface *surface, wl_fixed_t sx, wl_fixed_t sy)
{
    (void)data; (void)p; (void)serial; (void)surface; (void)sx; (void)sy;
    printf("client: pointer enter (%.0f,%.0f)\n", wl_fixed_to_double(sx),
           wl_fixed_to_double(sy));
}

static void ptr_leave(void *data, struct wl_pointer *p, uint32_t serial,
                      struct wl_surface *surface)
{
    (void)data; (void)p; (void)serial; (void)surface;
    printf("client: pointer leave\n");
}

static void ptr_motion(void *data, struct wl_pointer *p, uint32_t time,
                       wl_fixed_t sx, wl_fixed_t sy)
{
    (void)data; (void)p; (void)time;
    printf("client: pointer motion (%.0f,%.0f)\n", wl_fixed_to_double(sx),
           wl_fixed_to_double(sy));
}

static void ptr_button(void *data, struct wl_pointer *p, uint32_t serial,
                       uint32_t time, uint32_t button, uint32_t state)
{
    (void)data; (void)p; (void)serial; (void)time; (void)button;
    printf("client: pointer button %s\n",
           state == WL_POINTER_BUTTON_STATE_PRESSED ? "down" : "up");
}

static void ptr_axis(void *data, struct wl_pointer *p, uint32_t time,
                     uint32_t axis, wl_fixed_t value)
{
    (void)data; (void)p; (void)time; (void)axis; (void)value;
}

static void ptr_frame(void *data, struct wl_pointer *p)
{
    (void)data; (void)p;
}

static void ptr_axis_source(void *data, struct wl_pointer *p, uint32_t src)
{
    (void)data; (void)p; (void)src;
}

static void ptr_axis_stop(void *data, struct wl_pointer *p, uint32_t t,
                          uint32_t a)
{
    (void)data; (void)p; (void)t; (void)a;
}

static void ptr_axis_discrete(void *data, struct wl_pointer *p, uint32_t a,
                              int32_t d)
{
    (void)data; (void)p; (void)a; (void)d;
}

static const struct wl_pointer_listener pointer_listener = {
    .enter = ptr_enter,
    .leave = ptr_leave,
    .motion = ptr_motion,
    .button = ptr_button,
    .axis = ptr_axis,
    .frame = ptr_frame,
    .axis_source = ptr_axis_source,
    .axis_stop = ptr_axis_stop,
    .axis_discrete = ptr_axis_discrete,
};

/* --- keyboard ------------------------------------------------------------ */

static void kbd_keymap(void *data, struct wl_keyboard *kbd, uint32_t format,
                       int32_t fd, uint32_t size)
{
    char *map;
    struct xkb_keymap *km;
    struct xkb_state *st;

    (void)data; (void)kbd;
    if (format != WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1) {
        close(fd);
        return;
    }
    map = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == MAP_FAILED) {
        close(fd);
        return;
    }
    km = xkb_keymap_new_from_string(xkb_ctx, map,
                                    XKB_KEYMAP_FORMAT_TEXT_V1,
                                    XKB_KEYMAP_COMPILE_NO_FLAGS);
    munmap(map, size);
    close(fd);
    if (!km) {
        printf("client: keymap parse FAILED\n");
        return;
    }
    st = xkb_state_new(km);
    xkb_keymap_unref(xkb_keymap);
    xkb_state_unref(xkb_state);
    xkb_keymap = km;
    xkb_state = st;
    printf("client: keymap ok (%u bytes, %d layouts)\n", size,
           xkb_keymap_num_layouts(km));
}

static void kbd_enter(void *data, struct wl_keyboard *kbd, uint32_t serial,
                      struct wl_surface *surface, struct wl_array *keys)
{
    (void)data; (void)kbd; (void)serial; (void)surface;
    printf("client: keyboard focus in (%u keys down)\n",
           (unsigned)(keys->size / sizeof(uint32_t)));
}

static void kbd_leave(void *data, struct wl_keyboard *kbd, uint32_t serial,
                      struct wl_surface *surface)
{
    (void)data; (void)kbd; (void)serial; (void)surface;
    printf("client: keyboard focus out\n");
}

static void kbd_key(void *data, struct wl_keyboard *kbd, uint32_t serial,
                    uint32_t time, uint32_t key, uint32_t state)
{
    xkb_keysym_t sym = XKB_KEY_NoSymbol;
    char buf[32] = "";

    (void)data; (void)kbd; (void)serial; (void)time;
    if (xkb_state) {
        sym = xkb_state_key_get_one_sym(xkb_state, key);
        xkb_state_key_get_utf8(xkb_state, key, buf, sizeof(buf));
    }
    printf("client: key code=%u %s sym=0x%x \"%s\"\n", key,
           state == WL_KEYBOARD_KEY_STATE_PRESSED ? "down" : "up", sym, buf);
}

static void kbd_modifiers(void *data, struct wl_keyboard *kbd, uint32_t serial,
                          uint32_t dep, uint32_t lat, uint32_t lock,
                          uint32_t group)
{
    (void)data; (void)kbd; (void)serial;
    if (xkb_state)
        xkb_state_update_mask(xkb_state, dep, lat, lock, 0, 0, group);
    printf("client: modifiers dep=%u lat=%u lock=%u group=%u\n", dep, lat, lock,
           group);
}

static void kbd_repeat(void *data, struct wl_keyboard *kbd, int32_t rate,
                       int32_t delay)
{
    (void)data; (void)kbd;
    printf("client: key repeat %d Hz after %d ms\n", rate, delay);
}

static const struct wl_keyboard_listener keyboard_listener = {
    .keymap = kbd_keymap,
    .enter = kbd_enter,
    .leave = kbd_leave,
    .key = kbd_key,
    .modifiers = kbd_modifiers,
    .repeat_info = kbd_repeat,
};

static void seat_caps(void *data, struct wl_seat *s, uint32_t caps)
{
    (void)data;
    if ((caps & WL_SEAT_CAPABILITY_POINTER) && !pointer) {
        pointer = wl_seat_get_pointer(s);
        wl_pointer_add_listener(pointer, &pointer_listener, NULL);
        printf("client: seat has pointer\n");
    }
    if ((caps & WL_SEAT_CAPABILITY_KEYBOARD) && !keyboard) {
        keyboard = wl_seat_get_keyboard(s);
        wl_keyboard_add_listener(keyboard, &keyboard_listener, NULL);
        printf("client: seat has keyboard\n");
    }
}

static void seat_name(void *data, struct wl_seat *s, const char *name)
{
    (void)data; (void)s;
    printf("client: seat name %s\n", name);
}

static const struct wl_seat_listener seat_listener = {
    .capabilities = seat_caps,
    .name = seat_name,
};

static void out_geometry(void *d, struct wl_output *o, int32_t x, int32_t y,
                         int32_t pw, int32_t ph, int32_t subpixel,
                         const char *make, const char *model, int32_t tf)
{
    (void)d; (void)o; (void)x; (void)y; (void)pw; (void)ph; (void)subpixel;
    (void)make; (void)model; (void)tf;
}

static void out_mode(void *d, struct wl_output *o, uint32_t flags, int32_t w,
                     int32_t h, int32_t refresh)
{
    (void)d; (void)o; (void)flags;
    printf("client: output mode %dx%d@%d\n", w, h, refresh);
}

static void out_done(void *d, struct wl_output *o)
{
    (void)d; (void)o;
}

static void out_scale(void *d, struct wl_output *o, int32_t f)
{
    (void)d; (void)o; (void)f;
}

static const struct wl_output_listener output_listener = {
    .geometry = out_geometry,
    .mode = out_mode,
    .done = out_done,
    .scale = out_scale,
};

static void wm_ping(void *data, struct xdg_wm_base *wm, uint32_t serial)
{
    (void)data;
    xdg_wm_base_pong(wm, serial);
}

static const struct xdg_wm_base_listener wm_listener = {
    .ping = wm_ping,
};

static void reg_global(void *data, struct wl_registry *reg, uint32_t name,
                       const char *iface, uint32_t version)
{
    (void)data;
    if (!strcmp(iface, wl_compositor_interface.name)) {
        comp = wl_registry_bind(reg, name, &wl_compositor_interface,
                                version < 4 ? version : 4);
    } else if (!strcmp(iface, wl_shm_interface.name)) {
        shm = wl_registry_bind(reg, name, &wl_shm_interface, 1);
    } else if (!strcmp(iface, xdg_wm_base_interface.name)) {
        wm_base = wl_registry_bind(reg, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(wm_base, &wm_listener, NULL);
    } else if (!strcmp(iface, wl_seat_interface.name)) {
        seat = wl_registry_bind(reg, name, &wl_seat_interface,
                                version < 5 ? version : 5);
        wl_seat_add_listener(seat, &seat_listener, NULL);
    } else if (!strcmp(iface, wl_output_interface.name)) {
        output = wl_registry_bind(reg, name, &wl_output_interface,
                                  version < 2 ? version : 2);
        wl_output_add_listener(output, &output_listener, NULL);
    } else if (!strcmp(iface, zwp_linux_dmabuf_v1_interface.name)) {
        dmabuf = wl_registry_bind(reg, name, &zwp_linux_dmabuf_v1_interface,
                                  version < 3 ? version : 3);
        printf("client: zwp_linux_dmabuf_v1 v%u\n", version < 3 ? version : 3);
    }
}

static void reg_remove(void *data, struct wl_registry *reg, uint32_t name)
{
    (void)data; (void)reg; (void)name;
}

static const struct wl_registry_listener reg_listener = {
    .global = reg_global,
    .global_remove = reg_remove,
};

static double now_sec(void)
{
    struct timespec ts;

    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

int main(int argc, char **argv)
{
    struct wl_registry *reg;
    double t0;
    int secs = getenv("WL_CLIENT_SECS") ? atoi(getenv("WL_CLIENT_SECS")) : 15;
    int i;

    if (getenv("WL_CLIENT_SURFACES"))
        nsurf = atoi(getenv("WL_CLIENT_SURFACES"));
    if (nsurf < 1)
        nsurf = 1;
    if (nsurf > MAX_SURF)
        nsurf = MAX_SURF;

    use_dmabuf = getenv("WL_CLIENT_DMABUF") != NULL;
    g_static = getenv("WL_CLIENT_STATIC") != NULL;
    g_partial = getenv("WL_CLIENT_PARTIAL") != NULL;
    g_freerun = getenv("WL_CLIENT_FREERUN") != NULL;
    if (use_dmabuf) {
        const char *node = getenv("WL_CLIENT_DRM");

        drm_fd = open(node ? node : "/dev/dri/card1", O_RDWR);
        if (drm_fd < 0) {
            fprintf(stderr, "client: open %s: %s\n",
                    node ? node : "/dev/dri/card1", strerror(errno));
            return 1;
        }
        printf("client: dma-buf mode via %s\n",
               node ? node : "/dev/dri/card1");
    }

    xkb_ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);

    dpy = wl_display_connect(NULL);
    if (!dpy) {
        fprintf(stderr, "client: cannot connect to %s\n",
                getenv("WAYLAND_DISPLAY") ? getenv("WAYLAND_DISPLAY") : "(null)");
        return 1;
    }
    printf("client: connected to %s\n",
           getenv("WAYLAND_DISPLAY") ? getenv("WAYLAND_DISPLAY") : "wayland-0");

    reg = wl_display_get_registry(dpy);
    wl_registry_add_listener(reg, &reg_listener, NULL);
    wl_display_roundtrip(dpy);
    if (!comp || !shm || !wm_base) {
        fprintf(stderr, "client: missing globals (comp=%p shm=%p wm=%p)\n",
                (void *)comp, (void *)shm, (void *)wm_base);
        return 1;
    }
    if (use_dmabuf && !dmabuf) {
        fprintf(stderr, "client: compositor has no zwp_linux_dmabuf_v1\n");
        return 1;
    }

    for (i = 0; i < nsurf; i++) {
        struct surf *s = &surfs[i];

        s->index = i;
        s->bg = colors[i % 4];
        s->surface = wl_compositor_create_surface(comp);
        s->xdg = xdg_wm_base_get_xdg_surface(wm_base, s->surface);
        xdg_surface_add_listener(s->xdg, &xdg_surface_listener, s);
        s->top = xdg_surface_get_toplevel(s->xdg);
        xdg_toplevel_add_listener(s->top, &top_listener, s);
        xdg_toplevel_set_title(s->top, "vk-wl test");
        xdg_toplevel_set_app_id(s->top, "vk.wl.test");
        wl_surface_commit(s->surface);
    }
    wl_display_roundtrip(dpy);

    t0 = now_sec();
    while (running && now_sec() - t0 < secs) {
        struct pollfd p = { .fd = wl_display_get_fd(dpy), .events = POLLIN };
        static double last_submit;

        /* Free-running mode: commit every ~10 ms, no frame callbacks. */
        if (g_freerun && now_sec() - last_submit > 0.010) {
            last_submit = now_sec();
            submit(&surfs[0]);
        }

        while (wl_display_prepare_read(dpy) != 0)
            wl_display_dispatch_pending(dpy);
        wl_display_flush(dpy);
        if (poll(&p, 1, 2) > 0) {
            if (wl_display_read_events(dpy) < 0) {
                fprintf(stderr, "client: display closed\n");
                running = 0;
                break;
            }
        } else {
            wl_display_cancel_read(dpy);
        }
        wl_display_dispatch_pending(dpy);
        wl_display_flush(dpy);
    }

    printf("client: exiting after %.0fs (%lu commits, %.1f fps)\n",
           now_sec() - t0, g_commits, g_commits / (now_sec() - t0));
    for (i = 0; i < nsurf; i++) {
        if (surfs[i].frame_cb)
            wl_callback_destroy(surfs[i].frame_cb);
        if (surfs[i].top)
            xdg_toplevel_destroy(surfs[i].top);
        if (surfs[i].xdg)
            xdg_surface_destroy(surfs[i].xdg);
        if (surfs[i].surface)
            wl_surface_destroy(surfs[i].surface);
        for (int b = 0; b < surfs[i].nbuf; b++) {
            if (surfs[i].bufs[b].buf)
                wl_buffer_destroy(surfs[i].bufs[b].buf);
            if (surfs[i].bufs[b].px)
                munmap(surfs[i].bufs[b].px, surfs[i].bufs[b].size);
        }
    }
    wl_display_flush(dpy);
    wl_display_disconnect(dpy);
    if (xkb_state)
        xkb_state_unref(xkb_state);
    if (xkb_keymap)
        xkb_keymap_unref(xkb_keymap);
    if (xkb_ctx)
        xkb_context_unref(xkb_ctx);
    return 0;
}
