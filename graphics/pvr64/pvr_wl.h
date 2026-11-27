/*
 * pvr_wl.h - Minimal Wayland client (zwp_linux_dmabuf_v1) definitions for
 * EGL_PLATFORM_WAYLAND_KHR in pvr-bridge, without requiring wayland-protocols.
 */
#ifndef PVR_WL_H
#define PVR_WL_H

#include <stdint.h>

/* Matches wayland-egl-backend.h (WL_EGL_WINDOW_INTERFACE_VERSION == 3) */
struct wl_egl_window {
	const intptr_t version;
	int width;
	int height;
	int dx;
	int dy;
	int attached_width;
	int attached_height;
	void *driver_private;
	void (*resize_callback)(struct wl_egl_window *, void *);
	void (*destroy_window_callback)(void *);
	struct wl_surface *surface;
};

/* Minimal libwayland-client ABI */
struct wl_proxy;
struct wl_display;
struct wl_event_queue;
struct wl_registry;
struct wl_surface;
struct wl_buffer;

struct wl_message {
	const char *name;
	const char *signature;
	const struct wl_interface **types;
};

struct wl_interface {
	const char *name;
	int version;
	int method_count;
	const struct wl_message *methods;
	int event_count;
	const struct wl_message *events;
};

struct wl_registry_listener {
	void (*global)(void *data, struct wl_registry *registry,
		       uint32_t name, const char *interface, uint32_t version);
	void (*global_remove)(void *data, struct wl_registry *registry, uint32_t name);
};

struct wl_buffer_listener {
	void (*release)(void *data, struct wl_buffer *wl_buffer);
};

#define WL_MARSHAL_FLAG_DESTROY (1 << 0)

/* zwp_linux_dmabuf_v1 / zwp_linux_buffer_params_v1 opcodes */
#define ZWP_LINUX_DMABUF_V1_DESTROY        0
#define ZWP_LINUX_DMABUF_V1_CREATE_PARAMS  1

#define ZWP_LINUX_BUFFER_PARAMS_V1_DESTROY      0
#define ZWP_LINUX_BUFFER_PARAMS_V1_ADD          1
#define ZWP_LINUX_BUFFER_PARAMS_V1_CREATE       2
#define ZWP_LINUX_BUFFER_PARAMS_V1_CREATE_IMMED 3

/* wl_display / wl_registry / wl_surface opcodes */
#define WL_DISPLAY_GET_REGISTRY  1
#define WL_REGISTRY_BIND         0
#define WL_SURFACE_DESTROY       0
#define WL_SURFACE_ATTACH        1
#define WL_SURFACE_DAMAGE        2
#define WL_SURFACE_COMMIT        6
#define WL_SURFACE_DAMAGE_BUFFER 9
#define WL_BUFFER_DESTROY        0

#endif /* PVR_WL_H */
