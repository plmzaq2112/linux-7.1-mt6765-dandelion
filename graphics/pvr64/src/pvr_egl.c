/*
 * pvr_egl.c - libEGL.so.1 bridge for the PowerVR GE8320 (DDK 1.13) Android
 * blobs running on glibc (Ubuntu / Phosh).
 *
 * Forwards EGL 1.4 to /vendor/lib64/egl/libEGL_mtk.so (-> libIMGegl.so) and
 * adds what Linux compositors (wlroots 0.17 / phoc) need on top:
 *   - client extensions: EGL_EXT_platform_base + EGL_KHR_platform_gbm
 *   - eglGetPlatformDisplay(EXT) for GBM / surfaceless platforms
 *   - eglQueryDmaBufFormatsEXT / eglQueryDmaBufModifiersEXT (linear only)
 *   - eglCreateImageKHR attribute sanitising (linear modifier, PRESERVED)
 *   - fallbacks for configless contexts / surfaceless MakeCurrent
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <drm/drm_fourcc.h>
#include <linux/dma-buf.h>
#include "pvr_wl.h"

#define EXPORT __attribute__((visibility("default")))

typedef int32_t EGLint;
typedef unsigned int EGLBoolean;
typedef unsigned int EGLenum;
typedef intptr_t EGLAttrib;
typedef void *EGLDisplay, *EGLConfig, *EGLSurface, *EGLContext, *EGLClientBuffer, *EGLImageKHR, *EGLSyncKHR;
typedef void *EGLNativeDisplayType, *EGLNativePixmapType;
typedef uintptr_t EGLNativeWindowType;
typedef uint64_t EGLuint64KHR;
typedef void (*__eglMustCastToProperFunctionPointerType)(void);

#define EGL_SYNC_NATIVE_FENCE_ANDROID 0x3144
#define EGL_NO_SYNC_KHR ((EGLSyncKHR)0)

#define EGL_FALSE 0
#define EGL_TRUE 1
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_NO_SURFACE ((EGLSurface)0)
#define EGL_NO_IMAGE_KHR ((EGLImageKHR)0)
#define EGL_DEFAULT_DISPLAY ((EGLNativeDisplayType)0)

#define EGL_SUCCESS 0x3000
#define EGL_BAD_PARAMETER 0x300C
#define EGL_BAD_MATCH 0x3009
#define EGL_NONE 0x3038
#define EGL_EXTENSIONS 0x3055
#define EGL_VERSION 0x3054
#define EGL_SURFACE_TYPE 0x3033
#define EGL_PBUFFER_BIT 0x0001
#define EGL_RENDERABLE_TYPE 0x3040
#define EGL_OPENGL_ES2_BIT 0x0004
#define EGL_RED_SIZE 0x3024
#define EGL_GREEN_SIZE 0x3023
#define EGL_BLUE_SIZE 0x3022
#define EGL_ALPHA_SIZE 0x3021
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_IMAGE_PRESERVED_KHR 0x30D2
#define EGL_PLATFORM_GBM_KHR 0x31D7
#define EGL_PLATFORM_WAYLAND_KHR 0x31D8
#define EGL_PLATFORM_SURFACELESS_MESA 0x31DD
#define EGL_PLATFORM_DEVICE_EXT 0x313F
#define EGL_LINUX_DMA_BUF_EXT 0x3270
#define EGL_LINUX_DRM_FOURCC_EXT 0x3271
#define EGL_DMA_BUF_PLANE0_FD_EXT 0x3272
#define EGL_DMA_BUF_PLANE0_OFFSET_EXT 0x3273
#define EGL_DMA_BUF_PLANE0_PITCH_EXT 0x3274
#define EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT 0x3443
#define EGL_DMA_BUF_PLANE0_MODIFIER_HI_EXT 0x3444
#define EGL_DMA_BUF_PLANE1_MODIFIER_LO_EXT 0x3445
#define EGL_DMA_BUF_PLANE1_MODIFIER_HI_EXT 0x3446
#define EGL_DMA_BUF_PLANE2_MODIFIER_LO_EXT 0x3447
#define EGL_DMA_BUF_PLANE2_MODIFIER_HI_EXT 0x3448
#define EGL_DMA_BUF_PLANE3_MODIFIER_LO_EXT 0x3449
#define EGL_DMA_BUF_PLANE3_MODIFIER_HI_EXT 0x344A

#define VENDOR_EGL "/vendor/lib64/egl/libEGL_mtk.so"
#define VENDOR_GLES "/vendor/lib64/egl/libGLESv2_mtk.so"

static const char client_exts[] =
	"EGL_EXT_client_extensions EGL_EXT_platform_base EGL_KHR_platform_gbm "
	"EGL_MESA_platform_gbm EGL_KHR_platform_wayland EGL_EXT_platform_wayland "
	"EGL_MESA_platform_surfaceless EGL_KHR_client_get_all_proc_addresses";

static void *h_egl, *h_gles;
static pthread_once_t once = PTHREAD_ONCE_INIT;
static int debug;

#define DBG(...) do { if (debug) fprintf(stderr, "[pvr-egl] " __VA_ARGS__); } while (0)

#define REAL_FUNCS(X) \
	X(EGLint, eglGetError, (void)) \
	X(EGLDisplay, eglGetDisplay, (EGLNativeDisplayType)) \
	X(EGLBoolean, eglInitialize, (EGLDisplay, EGLint *, EGLint *)) \
	X(EGLBoolean, eglTerminate, (EGLDisplay)) \
	X(const char *, eglQueryString, (EGLDisplay, EGLint)) \
	X(void *, eglGetProcAddress, (const char *)) \
	X(EGLBoolean, eglGetConfigs, (EGLDisplay, EGLConfig *, EGLint, EGLint *)) \
	X(EGLBoolean, eglChooseConfig, (EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *)) \
	X(EGLBoolean, eglGetConfigAttrib, (EGLDisplay, EGLConfig, EGLint, EGLint *)) \
	X(EGLSurface, eglCreateWindowSurface, (EGLDisplay, EGLConfig, EGLNativeWindowType, const EGLint *)) \
	X(EGLSurface, eglCreatePixmapSurface, (EGLDisplay, EGLConfig, EGLNativePixmapType, const EGLint *)) \
	X(EGLSurface, eglCreatePbufferSurface, (EGLDisplay, EGLConfig, const EGLint *)) \
	X(EGLBoolean, eglDestroySurface, (EGLDisplay, EGLSurface)) \
	X(EGLBoolean, eglQuerySurface, (EGLDisplay, EGLSurface, EGLint, EGLint *)) \
	X(EGLContext, eglCreateContext, (EGLDisplay, EGLConfig, EGLContext, const EGLint *)) \
	X(EGLBoolean, eglDestroyContext, (EGLDisplay, EGLContext)) \
	X(EGLBoolean, eglMakeCurrent, (EGLDisplay, EGLSurface, EGLSurface, EGLContext)) \
	X(EGLContext, eglGetCurrentContext, (void)) \
	X(EGLSurface, eglGetCurrentSurface, (EGLint)) \
	X(EGLDisplay, eglGetCurrentDisplay, (void)) \
	X(EGLBoolean, eglQueryContext, (EGLDisplay, EGLContext, EGLint, EGLint *)) \
	X(EGLBoolean, eglWaitGL, (void)) \
	X(EGLBoolean, eglWaitNative, (EGLint)) \
	X(EGLBoolean, eglSwapBuffers, (EGLDisplay, EGLSurface)) \
	X(EGLBoolean, eglCopyBuffers, (EGLDisplay, EGLSurface, EGLNativePixmapType)) \
	X(EGLBoolean, eglSurfaceAttrib, (EGLDisplay, EGLSurface, EGLint, EGLint)) \
	X(EGLBoolean, eglBindTexImage, (EGLDisplay, EGLSurface, EGLint)) \
	X(EGLBoolean, eglReleaseTexImage, (EGLDisplay, EGLSurface, EGLint)) \
	X(EGLBoolean, eglSwapInterval, (EGLDisplay, EGLint)) \
	X(EGLBoolean, eglBindAPI, (EGLenum)) \
	X(EGLenum, eglQueryAPI, (void)) \
	X(EGLBoolean, eglWaitClient, (void)) \
	X(EGLBoolean, eglReleaseThread, (void)) \
	X(EGLSurface, eglCreatePbufferFromClientBuffer, (EGLDisplay, EGLenum, EGLClientBuffer, EGLConfig, const EGLint *))

#define DECL(ret, name, args) static ret (*real_##name) args;
REAL_FUNCS(DECL)

static EGLImageKHR (*real_eglCreateImageKHR)(EGLDisplay, EGLContext, EGLenum, EGLClientBuffer, const EGLint *);
static EGLBoolean (*real_eglDestroyImageKHR)(EGLDisplay, EGLImageKHR);
static EGLSyncKHR (*real_eglCreateSyncKHR)(EGLDisplay, EGLenum, const EGLint *);
static EGLBoolean (*real_eglDestroySyncKHR)(EGLDisplay, EGLSyncKHR);
static EGLint (*real_eglDupNativeFenceFDANDROID)(EGLDisplay, EGLSyncKHR);
static void (*real_glEGLImageTargetRenderbufferStorageOES)(unsigned int, void *);
static void (*real_glEGLImageTargetTexture2DOES)(unsigned int, void *);

/* Error override for functions implemented here. 0 = defer to the driver. */
static __thread EGLint local_error;

static void load(void)
{
	debug = getenv("PVR_EGL_DEBUG") != NULL;
	h_egl = dlopen(VENDOR_EGL, RTLD_NOW | RTLD_GLOBAL);
	if (!h_egl) {
		fprintf(stderr, "[pvr-egl] dlopen %s: %s\n", VENDOR_EGL, dlerror());
		abort();
	}
	h_gles = dlopen(VENDOR_GLES, RTLD_NOW | RTLD_GLOBAL);
	if (!h_gles)
		fprintf(stderr, "[pvr-egl] dlopen %s: %s\n", VENDOR_GLES, dlerror());
#define LOAD(ret, name, args) real_##name = (ret (*) args)dlsym(h_egl, #name);
	REAL_FUNCS(LOAD)
	real_eglCreateImageKHR = real_eglGetProcAddress("eglCreateImageKHR");
	real_eglDestroyImageKHR = real_eglGetProcAddress("eglDestroyImageKHR");
	real_eglCreateSyncKHR = real_eglGetProcAddress("eglCreateSyncKHR");
	real_eglDestroySyncKHR = real_eglGetProcAddress("eglDestroySyncKHR");
	real_eglDupNativeFenceFDANDROID = real_eglGetProcAddress("eglDupNativeFenceFDANDROID");
	real_glEGLImageTargetRenderbufferStorageOES = real_eglGetProcAddress("glEGLImageTargetRenderbufferStorageOES");
	real_glEGLImageTargetTexture2DOES = real_eglGetProcAddress("glEGLImageTargetTexture2DOES");
	DBG("loaded vendor EGL, CreateImage=%p, CreateSync=%p, DupFence=%p\n",
	    (void *)real_eglCreateImageKHR, (void *)real_eglCreateSyncKHR, (void *)real_eglDupNativeFenceFDANDROID);
}

#define INIT() pthread_once(&once, load)

static void set_error(EGLint e) { local_error = e; }

/* ---------------- Wayland client (EGL_PLATFORM_WAYLAND_KHR) ---------------- */
#define WL_NUM_BUFS 3
#define MAX_WL_SURFS 32
#define PVR_WL_PITCH_ALIGN_PX 32

struct pvr_wl_buf {
	uint32_t handle, stride;
	uint64_t size;
	int dmabuf_fd;
	EGLImageKHR img;
	unsigned int rbo, fbo;
	struct wl_buffer *wl_buf;
	int busy;
};

struct pvr_wl_surface {
	EGLDisplay dpy;
	struct wl_egl_window *ew;
	struct wl_surface *wl_surface;
	EGLSurface dummy_pbuf;
	int card_fd;
	int width, height;
	int cur;
	struct pvr_wl_buf bufs[WL_NUM_BUFS];
};

static struct pvr_wl_surface *wl_surfs[MAX_WL_SURFS];
static pthread_mutex_t wl_lock = PTHREAD_MUTEX_INITIALIZER;
static struct wl_display *g_wl_dpy;
static struct wl_event_queue *g_wl_queue;
static struct wl_proxy *g_wl_dmabuf;
static uint32_t g_wl_dmabuf_ver;

static void *h_wl;
static const struct wl_interface *p_wl_display_iface;
static const struct wl_interface *p_wl_registry_iface;
static const struct wl_interface *p_wl_buffer_iface;
static struct wl_event_queue *(*p_wl_display_create_queue)(struct wl_display *);
static void *(*p_wl_proxy_create_wrapper)(void *);
static void (*p_wl_proxy_wrapper_destroy)(void *);
static void (*p_wl_proxy_set_queue)(struct wl_proxy *, struct wl_event_queue *);
static int (*p_wl_display_roundtrip_queue)(struct wl_display *, struct wl_event_queue *);
static int (*p_wl_display_dispatch_queue)(struct wl_display *, struct wl_event_queue *);
static int (*p_wl_display_dispatch_queue_pending)(struct wl_display *, struct wl_event_queue *);
static int (*p_wl_display_flush)(struct wl_display *);
static struct wl_proxy *(*p_wl_proxy_marshal_flags)(struct wl_proxy *, uint32_t,
						    const struct wl_interface *, uint32_t, uint32_t, ...);
static int (*p_wl_proxy_add_listener)(struct wl_proxy *, void (**)(void), void *);
static uint32_t (*p_wl_proxy_get_version)(struct wl_proxy *);
static void (*p_wl_proxy_destroy)(struct wl_proxy *);

static const struct wl_message dmabuf_reqs[] = {
	{ "destroy", "", NULL },
	{ "create_params", "n", NULL },
};
static const struct wl_interface zwp_linux_dmabuf_v1_iface = {
	"zwp_linux_dmabuf_v1", 3, 2, dmabuf_reqs, 0, NULL
};
static const struct wl_message params_reqs[] = {
	{ "destroy", "", NULL },
	{ "add", "huuuuu", NULL },
	{ "create", "iiuu", NULL },
	{ "create_immed", "2niiuu", NULL },
};
static const struct wl_interface zwp_linux_buffer_params_v1_iface = {
	"zwp_linux_buffer_params_v1", 3, 4, params_reqs, 0, NULL
};

static int wl_load(void)
{
	if (h_wl)
		return 1;
	h_wl = dlopen("libwayland-client.so.0", RTLD_LAZY | RTLD_NOLOAD);
	if (!h_wl)
		h_wl = dlopen("libwayland-client.so.0", RTLD_LAZY);
	if (!h_wl)
		return 0;
	p_wl_display_iface = dlsym(h_wl, "wl_display_interface");
	p_wl_registry_iface = dlsym(h_wl, "wl_registry_interface");
	p_wl_buffer_iface = dlsym(h_wl, "wl_buffer_interface");
	p_wl_display_create_queue = dlsym(h_wl, "wl_display_create_queue");
	p_wl_proxy_create_wrapper = dlsym(h_wl, "wl_proxy_create_wrapper");
	p_wl_proxy_wrapper_destroy = dlsym(h_wl, "wl_proxy_wrapper_destroy");
	p_wl_proxy_set_queue = dlsym(h_wl, "wl_proxy_set_queue");
	p_wl_display_roundtrip_queue = dlsym(h_wl, "wl_display_roundtrip_queue");
	p_wl_display_dispatch_queue = dlsym(h_wl, "wl_display_dispatch_queue");
	p_wl_display_dispatch_queue_pending = dlsym(h_wl, "wl_display_dispatch_queue_pending");
	p_wl_display_flush = dlsym(h_wl, "wl_display_flush");
	p_wl_proxy_marshal_flags = dlsym(h_wl, "wl_proxy_marshal_flags");
	p_wl_proxy_add_listener = dlsym(h_wl, "wl_proxy_add_listener");
	p_wl_proxy_get_version = dlsym(h_wl, "wl_proxy_get_version");
	p_wl_proxy_destroy = dlsym(h_wl, "wl_proxy_destroy");
	return p_wl_display_iface && p_wl_proxy_marshal_flags && p_wl_display_roundtrip_queue;
}

static void wl_reg_global(void *data, struct wl_registry *reg, uint32_t name,
			  const char *iface, uint32_t ver)
{
	(void)data;
	if (!strcmp(iface, "zwp_linux_dmabuf_v1") && !g_wl_dmabuf) {
		uint32_t v = ver < 3 ? ver : 3;
		g_wl_dmabuf = p_wl_proxy_marshal_flags(
			(struct wl_proxy *)reg, WL_REGISTRY_BIND,
			&zwp_linux_dmabuf_v1_iface, v, 0,
			name, iface, v, NULL);
		g_wl_dmabuf_ver = v;
	}
}
static void wl_reg_global_rm(void *data, struct wl_registry *reg, uint32_t name)
{ (void)data; (void)reg; (void)name; }

static const struct wl_registry_listener wl_reg_listener = {
	wl_reg_global, wl_reg_global_rm
};

static int wl_init_dmabuf(struct wl_display *dpy)
{
	if (g_wl_dmabuf)
		return 1;
	if (!wl_load())
		return 0;
	g_wl_queue = p_wl_display_create_queue(dpy);
	if (!g_wl_queue)
		return 0;
	void *wrap = p_wl_proxy_create_wrapper(dpy);
	p_wl_proxy_set_queue((struct wl_proxy *)wrap, g_wl_queue);
	struct wl_proxy *reg = p_wl_proxy_marshal_flags(
		(struct wl_proxy *)wrap, WL_DISPLAY_GET_REGISTRY,
		p_wl_registry_iface, 1, 0, NULL);
	p_wl_proxy_wrapper_destroy(wrap);
	p_wl_proxy_add_listener(reg, (void (**)(void))&wl_reg_listener, NULL);
	p_wl_display_roundtrip_queue(dpy, g_wl_queue);
	p_wl_proxy_destroy(reg);
	DBG("wl_init_dmabuf: dmabuf=%p ver=%u\n", (void *)g_wl_dmabuf, g_wl_dmabuf_ver);
	return g_wl_dmabuf != NULL;
}

static struct pvr_wl_surface *find_wl_surf(EGLSurface s)
{
	if (!s || (uintptr_t)s < 0x10000)
		return NULL;
	pthread_mutex_lock(&wl_lock);
	for (int i = 0; i < MAX_WL_SURFS; i++) {
		if (wl_surfs[i] == (struct pvr_wl_surface *)s) {
			pthread_mutex_unlock(&wl_lock);
			return (struct pvr_wl_surface *)s;
		}
	}
	pthread_mutex_unlock(&wl_lock);
	return NULL;
}

static void wl_buf_release(void *data, struct wl_buffer *wb)
{
	(void)wb;
	struct pvr_wl_buf *b = (struct pvr_wl_buf *)data;
	b->busy = 0;
}
static const struct wl_buffer_listener wl_buf_listener = { wl_buf_release };

static void (*gles_gen_fb)(int, unsigned int *);
static void (*gles_del_fb)(int, const unsigned int *);
static void (*gles_gen_rb)(int, unsigned int *);
static void (*gles_del_rb)(int, const unsigned int *);
static void (*gles_bind_rb)(unsigned int, unsigned int);
static void (*gles_bind_fb)(unsigned int, unsigned int);
static void (*gles_fb_rb)(unsigned int, unsigned int, unsigned int, unsigned int);
static void (*gles_flush)(void);
static void (*gles_viewport)(int, int, int, int);
static void (*gles_set_win_fbo)(unsigned int);

static void resolve_gles_funcs(void)
{
	if (gles_gen_fb)
		return;
	void *hg = dlopen("libGLESv2.so.2", RTLD_NOLOAD);
	if (!hg) hg = h_gles;
	if (!hg) return;
	gles_gen_fb = dlsym(hg, "glGenFramebuffers");
	gles_del_fb = dlsym(hg, "glDeleteFramebuffers");
	gles_gen_rb = dlsym(hg, "glGenRenderbuffers");
	gles_del_rb = dlsym(hg, "glDeleteRenderbuffers");
	gles_bind_rb = dlsym(hg, "glBindRenderbuffer");
	gles_bind_fb = dlsym(hg, "glBindFramebuffer");
	gles_fb_rb = dlsym(hg, "glFramebufferRenderbuffer");
	gles_flush = dlsym(hg, "glFlush");
	gles_viewport = dlsym(hg, "glViewport");
	gles_set_win_fbo = dlsym(hg, "pvr_gles_set_window_fbo");
}

static void wl_buf_free(struct pvr_wl_surface *ws, struct pvr_wl_buf *b)
{
	if (b->fbo && gles_del_fb) { gles_del_fb(1, &b->fbo); b->fbo = 0; }
	if (b->rbo && gles_del_rb) { gles_del_rb(1, &b->rbo); b->rbo = 0; }
	if (b->wl_buf) {
		p_wl_proxy_marshal_flags((struct wl_proxy *)b->wl_buf, WL_BUFFER_DESTROY,
					 NULL, p_wl_proxy_get_version((struct wl_proxy *)b->wl_buf),
					 WL_MARSHAL_FLAG_DESTROY);
		b->wl_buf = NULL;
	}
	if (b->img) { real_eglDestroyImageKHR(ws->dpy, b->img); b->img = NULL; }
	if (b->dmabuf_fd >= 0) { close(b->dmabuf_fd); b->dmabuf_fd = -1; }
	if (b->handle && ws->card_fd >= 0) {
		struct drm_mode_destroy_dumb d = { .handle = b->handle };
		ioctl(ws->card_fd, DRM_IOCTL_MODE_DESTROY_DUMB, &d);
		b->handle = 0;
	}
	b->busy = 0;
}

static int wl_buf_alloc(struct pvr_wl_surface *ws, struct pvr_wl_buf *b, int w, int h)
{
	struct drm_mode_create_dumb creq = {
		.width = (uint32_t)((w + PVR_WL_PITCH_ALIGN_PX - 1) & ~(PVR_WL_PITCH_ALIGN_PX - 1)),
		.height = (uint32_t)h,
		.bpp = 32,
	};
	if (ioctl(ws->card_fd, DRM_IOCTL_MODE_CREATE_DUMB, &creq) < 0)
		return 0;
	struct drm_prime_handle preq = { .handle = creq.handle, .flags = DRM_CLOEXEC | DRM_RDWR, .fd = -1 };
	if (ioctl(ws->card_fd, DRM_IOCTL_PRIME_HANDLE_TO_FD, &preq) < 0) {
		struct drm_mode_destroy_dumb d = { .handle = creq.handle };
		ioctl(ws->card_fd, DRM_IOCTL_MODE_DESTROY_DUMB, &d);
		return 0;
	}
	b->handle = creq.handle;
	b->stride = creq.pitch;
	b->size = creq.size;
	b->dmabuf_fd = preq.fd;

	EGLint attrs[] = {
		EGL_WIDTH, w,
		EGL_HEIGHT, h,
		EGL_LINUX_DRM_FOURCC_EXT, DRM_FORMAT_ARGB8888,
		EGL_DMA_BUF_PLANE0_FD_EXT, b->dmabuf_fd,
		EGL_DMA_BUF_PLANE0_OFFSET_EXT, 0,
		EGL_DMA_BUF_PLANE0_PITCH_EXT, (EGLint)b->stride,
		EGL_NONE
	};
	b->img = real_eglCreateImageKHR(ws->dpy, EGL_NO_CONTEXT, EGL_LINUX_DMA_BUF_EXT, NULL, attrs);
	if (!b->img) {
		wl_buf_free(ws, b);
		return 0;
	}

	struct wl_proxy *params = p_wl_proxy_marshal_flags(
		g_wl_dmabuf, ZWP_LINUX_DMABUF_V1_CREATE_PARAMS,
		&zwp_linux_buffer_params_v1_iface, g_wl_dmabuf_ver, 0, NULL);
	p_wl_proxy_marshal_flags(params, ZWP_LINUX_BUFFER_PARAMS_V1_ADD,
				 NULL, g_wl_dmabuf_ver, 0,
				 b->dmabuf_fd, 0, 0, b->stride, 0, 0);
	b->wl_buf = (struct wl_buffer *)p_wl_proxy_marshal_flags(
		params, ZWP_LINUX_BUFFER_PARAMS_V1_CREATE_IMMED,
		p_wl_buffer_iface, g_wl_dmabuf_ver, 0,
		NULL, w, h, DRM_FORMAT_ARGB8888, 0);
	p_wl_proxy_marshal_flags(params, ZWP_LINUX_BUFFER_PARAMS_V1_DESTROY,
				 NULL, g_wl_dmabuf_ver, WL_MARSHAL_FLAG_DESTROY);
	if (!b->wl_buf) {
		wl_buf_free(ws, b);
		return 0;
	}
	p_wl_proxy_set_queue((struct wl_proxy *)b->wl_buf, g_wl_queue);
	p_wl_proxy_add_listener((struct wl_proxy *)b->wl_buf, (void (**)(void))&wl_buf_listener, b);
	return 1;
}

static int wl_buf_ensure_fbo(struct pvr_wl_surface *ws, struct pvr_wl_buf *b)
{
	if (!b->img && !wl_buf_alloc(ws, b, ws->width, ws->height))
		return 0;
	if (b->fbo)
		return 1;
	resolve_gles_funcs();
	if (!gles_gen_rb || !real_glEGLImageTargetRenderbufferStorageOES)
		return 0;
	gles_gen_rb(1, &b->rbo);
	gles_bind_rb(0x8D41, b->rbo);
	real_glEGLImageTargetRenderbufferStorageOES(0x8D41, b->img);
	gles_gen_fb(1, &b->fbo);
	gles_bind_fb(0x8D40, b->fbo);
	gles_fb_rb(0x8D40, 0x8CE0, 0x8D41, b->rbo);
	return 1;
}

static void wl_attach_fence(struct pvr_wl_buf *b, EGLDisplay dpy)
{
	if (!real_eglCreateSyncKHR || !real_eglDupNativeFenceFDANDROID || !real_eglDestroySyncKHR)
		return;
	EGLSyncKHR sync = real_eglCreateSyncKHR(dpy, EGL_SYNC_NATIVE_FENCE_ANDROID, NULL);
	if (sync == EGL_NO_SYNC_KHR)
		return;
	int sfd = real_eglDupNativeFenceFDANDROID(dpy, sync);
	real_eglDestroySyncKHR(dpy, sync);
	if (sfd < 0)
		return;
	struct dma_buf_import_sync_file imp = { .flags = DMA_BUF_SYNC_WRITE, .fd = sfd };
	ioctl(b->dmabuf_fd, DMA_BUF_IOCTL_IMPORT_SYNC_FILE, &imp);
	close(sfd);
}

static void wl_resize_cb(struct wl_egl_window *ew, void *data)
{
	(void)ew; (void)data;
}

static void wl_destroy_cb(void *data)
{
	struct pvr_wl_surface *ws = (struct pvr_wl_surface *)data;
	if (ws) ws->ew = NULL;
}

static EGLConfig fallback_config(EGLDisplay d);

/* ---------------- plain forwarders ---------------- */
#define FWD0(ret, name) EXPORT ret name(void) { INIT(); return real_##name(); }

EXPORT EGLint eglGetError(void)
{
	INIT();
	EGLint e = local_error;
	if (e) {
		local_error = 0;
		real_eglGetError();
		return e;
	}
	return real_eglGetError();
}

EXPORT EGLDisplay eglGetDisplay(EGLNativeDisplayType d)
{
	INIT();
	if (d != EGL_DEFAULT_DISPLAY && wl_load() && *(void **)d == (void *)p_wl_display_iface) {
		g_wl_dpy = (struct wl_display *)d;
		DBG("eglGetDisplay(wl_display=%p) -> default display\n", (void *)d);
		return real_eglGetDisplay(EGL_DEFAULT_DISPLAY);
	}
	return real_eglGetDisplay(d);
}
EXPORT EGLBoolean eglInitialize(EGLDisplay d, EGLint *ma, EGLint *mi)
{
	INIT();
	EGLBoolean r = real_eglInitialize(d, ma, mi);
	if (r && g_wl_dpy)
		wl_init_dmabuf(g_wl_dpy);
	DBG("eglInitialize(%p) = %u\n", d, r);
	return r;
}
EXPORT EGLBoolean eglTerminate(EGLDisplay d) { INIT(); return real_eglTerminate(d); }
EXPORT EGLBoolean eglGetConfigs(EGLDisplay d, EGLConfig *c, EGLint s, EGLint *n) { INIT(); return real_eglGetConfigs(d, c, s, n); }
EXPORT EGLBoolean eglChooseConfig(EGLDisplay d, const EGLint *a, EGLConfig *c, EGLint s, EGLint *n) { INIT(); return real_eglChooseConfig(d, a, c, s, n); }
EXPORT EGLBoolean eglGetConfigAttrib(EGLDisplay d, EGLConfig c, EGLint a, EGLint *v) { INIT(); return real_eglGetConfigAttrib(d, c, a, v); }
EXPORT EGLSurface eglCreateWindowSurface(EGLDisplay d, EGLConfig c, EGLNativeWindowType w, const EGLint *a)
{
	INIT();
	if (g_wl_dpy && w && g_wl_dmabuf) {
		struct wl_egl_window *ew = (struct wl_egl_window *)w;
		if (ew->version == 3 && ew->surface) {
			static const EGLint pb[] = { EGL_WIDTH, 1, EGL_HEIGHT, 1, EGL_NONE };
			EGLConfig fc = c ? c : fallback_config(d);
			EGLSurface dummy = fc ? real_eglCreatePbufferSurface(d, fc, pb) : EGL_NO_SURFACE;
			int cfd = open("/dev/dri/card1", O_RDWR | O_CLOEXEC);
			if (dummy != EGL_NO_SURFACE && cfd >= 0) {
				struct pvr_wl_surface *ws = calloc(1, sizeof(*ws));
				if (ws) {
					ws->dpy = d;
					ws->ew = ew;
					ws->wl_surface = ew->surface;
					ws->dummy_pbuf = dummy;
					ws->card_fd = cfd;
					ws->width = ew->width > 0 ? ew->width : 1;
					ws->height = ew->height > 0 ? ew->height : 1;
					for (int i = 0; i < WL_NUM_BUFS; i++)
						ws->bufs[i].dmabuf_fd = -1;
					ew->driver_private = ws;
					ew->resize_callback = wl_resize_cb;
					ew->destroy_window_callback = wl_destroy_cb;
					pthread_mutex_lock(&wl_lock);
					for (int i = 0; i < MAX_WL_SURFS; i++) {
						if (!wl_surfs[i]) { wl_surfs[i] = ws; break; }
					}
					pthread_mutex_unlock(&wl_lock);
					DBG("eglCreateWindowSurface(wl %dx%d) = %p\n", ws->width, ws->height, (void *)ws);
					return (EGLSurface)ws;
				}
			}
			if (cfd >= 0) close(cfd);
			if (dummy != EGL_NO_SURFACE) real_eglDestroySurface(d, dummy);
		}
	}
	return real_eglCreateWindowSurface(d, c, w, a);
}
EXPORT EGLSurface eglCreatePixmapSurface(EGLDisplay d, EGLConfig c, EGLNativePixmapType p, const EGLint *a) { INIT(); return real_eglCreatePixmapSurface(d, c, p, a); }
EXPORT EGLSurface eglCreatePbufferSurface(EGLDisplay d, EGLConfig c, const EGLint *a) { INIT(); return real_eglCreatePbufferSurface(d, c, a); }
EXPORT EGLBoolean eglDestroySurface(EGLDisplay d, EGLSurface s)
{
	INIT();
	struct pvr_wl_surface *ws = find_wl_surf(s);
	if (ws) {
		pthread_mutex_lock(&wl_lock);
		for (int i = 0; i < MAX_WL_SURFS; i++)
			if (wl_surfs[i] == ws) wl_surfs[i] = NULL;
		pthread_mutex_unlock(&wl_lock);
		for (int i = 0; i < WL_NUM_BUFS; i++)
			wl_buf_free(ws, &ws->bufs[i]);
		if (ws->card_fd >= 0) close(ws->card_fd);
		if (ws->dummy_pbuf != EGL_NO_SURFACE) real_eglDestroySurface(d, ws->dummy_pbuf);
		if (ws->ew) {
			ws->ew->driver_private = NULL;
			ws->ew->resize_callback = NULL;
			ws->ew->destroy_window_callback = NULL;
		}
		free(ws);
		return EGL_TRUE;
	}
	return real_eglDestroySurface(d, s);
}
EXPORT EGLBoolean eglQuerySurface(EGLDisplay d, EGLSurface s, EGLint a, EGLint *v)
{
	INIT();
	struct pvr_wl_surface *ws = find_wl_surf(s);
	if (ws && v) {
		if (a == EGL_WIDTH) { *v = ws->ew ? ws->ew->width : ws->width; return EGL_TRUE; }
		if (a == EGL_HEIGHT) { *v = ws->ew ? ws->ew->height : ws->height; return EGL_TRUE; }
		return real_eglQuerySurface(d, ws->dummy_pbuf, a, v);
	}
	return real_eglQuerySurface(d, s, a, v);
}
EXPORT EGLBoolean eglDestroyContext(EGLDisplay d, EGLContext c) { INIT(); return real_eglDestroyContext(d, c); }
FWD0(EGLContext, eglGetCurrentContext)
EXPORT EGLSurface eglGetCurrentSurface(EGLint w) { INIT(); return real_eglGetCurrentSurface(w); }
FWD0(EGLDisplay, eglGetCurrentDisplay)
EXPORT EGLBoolean eglQueryContext(EGLDisplay d, EGLContext c, EGLint a, EGLint *v) { INIT(); return real_eglQueryContext(d, c, a, v); }
FWD0(EGLBoolean, eglWaitGL)
EXPORT EGLBoolean eglWaitNative(EGLint e) { INIT(); return real_eglWaitNative(e); }
EXPORT EGLBoolean eglSwapBuffers(EGLDisplay d, EGLSurface s)
{
	INIT();
	struct pvr_wl_surface *ws = find_wl_surf(s);
	if (ws) {
		struct pvr_wl_buf *b = &ws->bufs[ws->cur];
		if (!wl_buf_ensure_fbo(ws, b))
			return EGL_FALSE;
		resolve_gles_funcs();
		if (gles_flush)
			gles_flush();
		wl_attach_fence(b, d);

		p_wl_proxy_marshal_flags((struct wl_proxy *)ws->wl_surface, WL_SURFACE_ATTACH,
					 NULL, p_wl_proxy_get_version((struct wl_proxy *)ws->wl_surface), 0,
					 b->wl_buf, ws->ew ? ws->ew->dx : 0, ws->ew ? ws->ew->dy : 0);
		p_wl_proxy_marshal_flags((struct wl_proxy *)ws->wl_surface, WL_SURFACE_DAMAGE,
					 NULL, p_wl_proxy_get_version((struct wl_proxy *)ws->wl_surface), 0,
					 0, 0, ws->width, ws->height);
		p_wl_proxy_marshal_flags((struct wl_proxy *)ws->wl_surface, WL_SURFACE_COMMIT,
					 NULL, p_wl_proxy_get_version((struct wl_proxy *)ws->wl_surface), 0);
		p_wl_display_flush(g_wl_dpy);
		b->busy = 1;
		if (ws->ew) {
			ws->ew->dx = 0;
			ws->ew->dy = 0;
			ws->ew->attached_width = ws->width;
			ws->ew->attached_height = ws->height;
		}

		p_wl_display_dispatch_queue_pending(g_wl_dpy, g_wl_queue);
		int next = -1;
		for (int attempt = 0; attempt < 200; attempt++) {
			for (int i = 1; i <= WL_NUM_BUFS; i++) {
				int idx = (ws->cur + i) % WL_NUM_BUFS;
				if (!ws->bufs[idx].busy) { next = idx; break; }
			}
			if (next >= 0) break;
			if (p_wl_display_dispatch_queue(g_wl_dpy, g_wl_queue) < 0) break;
		}
		if (next < 0)
			next = (ws->cur + 1) % WL_NUM_BUFS;

		if (ws->ew && (ws->ew->width != ws->width || ws->ew->height != ws->height) &&
		    ws->ew->width > 0 && ws->ew->height > 0) {
			ws->width = ws->ew->width;
			ws->height = ws->ew->height;
			for (int i = 0; i < WL_NUM_BUFS; i++) {
				if (!ws->bufs[i].busy)
					wl_buf_free(ws, &ws->bufs[i]);
			}
		}

		ws->cur = next;
		if (wl_buf_ensure_fbo(ws, &ws->bufs[ws->cur]) && gles_set_win_fbo)
			gles_set_win_fbo(ws->bufs[ws->cur].fbo);
		return EGL_TRUE;
	}
	return real_eglSwapBuffers(d, s);
}
EXPORT EGLBoolean eglCopyBuffers(EGLDisplay d, EGLSurface s, EGLNativePixmapType p) { INIT(); return real_eglCopyBuffers(d, s, p); }
EXPORT EGLBoolean eglSurfaceAttrib(EGLDisplay d, EGLSurface s, EGLint a, EGLint v) { INIT(); return real_eglSurfaceAttrib(d, s, a, v); }
EXPORT EGLBoolean eglBindTexImage(EGLDisplay d, EGLSurface s, EGLint b) { INIT(); return real_eglBindTexImage(d, s, b); }
EXPORT EGLBoolean eglReleaseTexImage(EGLDisplay d, EGLSurface s, EGLint b) { INIT(); return real_eglReleaseTexImage(d, s, b); }
EXPORT EGLBoolean eglSwapInterval(EGLDisplay d, EGLint i)
{
	INIT();
	if (g_wl_dpy) return EGL_TRUE;
	return real_eglSwapInterval(d, i);
}
EXPORT EGLBoolean eglBindAPI(EGLenum a) { INIT(); return real_eglBindAPI(a); }
FWD0(EGLenum, eglQueryAPI)
FWD0(EGLBoolean, eglWaitClient)
FWD0(EGLBoolean, eglReleaseThread)
EXPORT EGLSurface eglCreatePbufferFromClientBuffer(EGLDisplay d, EGLenum t, EGLClientBuffer b, EGLConfig c, const EGLint *a)
{ INIT(); return real_eglCreatePbufferFromClientBuffer(d, t, b, c, a); }

/* ---------------- client extensions / platform displays ---------------- */
EXPORT const char *eglQueryString(EGLDisplay d, EGLint name)
{
	INIT();
	if (d == EGL_NO_DISPLAY) {
		if (name == EGL_EXTENSIONS)
			return client_exts;
		if (name == EGL_VERSION)
			return "1.4";
	}
	return real_eglQueryString(d, name);
}

static EGLDisplay platform_display(EGLenum platform, void *native)
{
	INIT();
	switch (platform) {
	case EGL_PLATFORM_GBM_KHR:
	case EGL_PLATFORM_SURFACELESS_MESA:
		DBG("eglGetPlatformDisplay(0x%x, %p) -> default display\n", platform, native);
		return real_eglGetDisplay(EGL_DEFAULT_DISPLAY);
	case EGL_PLATFORM_WAYLAND_KHR:
		g_wl_dpy = (struct wl_display *)native;
		DBG("eglGetPlatformDisplay(WAYLAND, %p) -> default display\n", native);
		return real_eglGetDisplay(EGL_DEFAULT_DISPLAY);
	default:
		DBG("eglGetPlatformDisplay(0x%x) unsupported\n", platform);
		set_error(EGL_BAD_PARAMETER);
		return EGL_NO_DISPLAY;
	}
}

EXPORT EGLDisplay eglGetPlatformDisplayEXT(EGLenum platform, void *native, const EGLint *attribs)
{
	(void)attribs;
	return platform_display(platform, native);
}

EXPORT EGLDisplay eglGetPlatformDisplay(EGLenum platform, void *native, const EGLAttrib *attribs)
{
	(void)attribs;
	return platform_display(platform, native);
}

EXPORT EGLSurface eglCreatePlatformWindowSurfaceEXT(EGLDisplay d, EGLConfig cfg, void *native, const EGLint *attribs)
{
	return eglCreateWindowSurface(d, cfg, (EGLNativeWindowType)native, attribs);
}

EXPORT EGLSurface eglCreatePlatformWindowSurface(EGLDisplay d, EGLConfig cfg, void *native, const EGLAttrib *attribs)
{
	(void)attribs;
	return eglCreateWindowSurface(d, cfg, (EGLNativeWindowType)native, NULL);
}

EXPORT EGLBoolean eglSwapBuffersWithDamageEXT(EGLDisplay d, EGLSurface s, const EGLint *rects, EGLint n_rects)
{
	(void)rects; (void)n_rects;
	return eglSwapBuffers(d, s);
}

/* ---------------- dma-buf format queries ---------------- */
static const EGLint dmabuf_formats[] = {
	DRM_FORMAT_ARGB8888, DRM_FORMAT_XRGB8888,
	DRM_FORMAT_ABGR8888, DRM_FORMAT_XBGR8888,
	DRM_FORMAT_RGB565,
};
#define N_FORMATS (EGLint)(sizeof(dmabuf_formats) / sizeof(dmabuf_formats[0]))

EXPORT EGLBoolean eglQueryDmaBufFormatsEXT(EGLDisplay d, EGLint max, EGLint *formats, EGLint *num)
{
	(void)d;
	if (!num || max < 0) {
		set_error(EGL_BAD_PARAMETER);
		return EGL_FALSE;
	}
	if (max == 0 || !formats) {
		*num = N_FORMATS;
		return EGL_TRUE;
	}
	EGLint n = max < N_FORMATS ? max : N_FORMATS;
	memcpy(formats, dmabuf_formats, n * sizeof(EGLint));
	*num = n;
	return EGL_TRUE;
}

EXPORT EGLBoolean eglQueryDmaBufModifiersEXT(EGLDisplay d, EGLint format, EGLint max,
					      EGLuint64KHR *mods, EGLBoolean *external, EGLint *num)
{
	(void)d;
	int ok = 0;
	for (EGLint i = 0; i < N_FORMATS; i++)
		if (dmabuf_formats[i] == format)
			ok = 1;
	if (!ok || !num || max < 0) {
		set_error(EGL_BAD_PARAMETER);
		return EGL_FALSE;
	}
	if (max == 0 || !mods) {
		*num = 1;
		return EGL_TRUE;
	}
	mods[0] = DRM_FORMAT_MOD_LINEAR;
	if (external)
		external[0] = EGL_FALSE;
	*num = 1;
	return EGL_TRUE;
}

/* ---------------- EGLImage <-> dma-buf fd & native fence import ---------------- */
#define MAX_DMA_IMAGES 128
struct dma_image_entry {
	EGLImageKHR img;
	EGLDisplay dpy;
	int fd;
};
static struct dma_image_entry dma_images[MAX_DMA_IMAGES];
static pthread_mutex_t dma_img_lock = PTHREAD_MUTEX_INITIALIZER;

static void dma_image_add(EGLDisplay dpy, EGLImageKHR img, int orig_fd)
{
	if (!img || orig_fd < 0)
		return;
	int dup_fd = fcntl(orig_fd, F_DUPFD_CLOEXEC, 3);
	if (dup_fd < 0)
		return;
	pthread_mutex_lock(&dma_img_lock);
	for (int i = 0; i < MAX_DMA_IMAGES; i++) {
		if (!dma_images[i].img) {
			dma_images[i].img = img;
			dma_images[i].dpy = dpy;
			dma_images[i].fd = dup_fd;
			pthread_mutex_unlock(&dma_img_lock);
			return;
		}
	}
	pthread_mutex_unlock(&dma_img_lock);
	close(dup_fd);
}

static void dma_image_remove(EGLImageKHR img)
{
	if (!img)
		return;
	pthread_mutex_lock(&dma_img_lock);
	for (int i = 0; i < MAX_DMA_IMAGES; i++) {
		if (dma_images[i].img == img) {
			if (dma_images[i].fd >= 0)
				close(dma_images[i].fd);
			dma_images[i].img = NULL;
			dma_images[i].dpy = NULL;
			dma_images[i].fd = -1;
			break;
		}
	}
	pthread_mutex_unlock(&dma_img_lock);
}

EXPORT int pvr_egl_attach_fence_to_image(void *img_ptr)
{
	if (!img_ptr || !real_eglCreateSyncKHR || !real_eglDupNativeFenceFDANDROID || !real_eglDestroySyncKHR)
		return -1;

	EGLDisplay dpy = NULL;
	int dmabuf_fd = -1;
	pthread_mutex_lock(&dma_img_lock);
	for (int i = 0; i < MAX_DMA_IMAGES; i++) {
		if (dma_images[i].img == img_ptr) {
			dpy = dma_images[i].dpy;
			dmabuf_fd = dma_images[i].fd;
			break;
		}
	}
	pthread_mutex_unlock(&dma_img_lock);
	if (!dpy || dmabuf_fd < 0)
		return -1;

	EGLSyncKHR sync = real_eglCreateSyncKHR(dpy, EGL_SYNC_NATIVE_FENCE_ANDROID, NULL);
	if (sync == EGL_NO_SYNC_KHR)
		return -1;
	int sfd = real_eglDupNativeFenceFDANDROID(dpy, sync);
	real_eglDestroySyncKHR(dpy, sync);
	if (sfd < 0)
		return -1;

	struct dma_buf_import_sync_file imp = {
		.flags = DMA_BUF_SYNC_WRITE,
		.fd = sfd,
	};
	int rc = ioctl(dmabuf_fd, DMA_BUF_IOCTL_IMPORT_SYNC_FILE, &imp);
	close(sfd);
	return rc;
}

static void (*gles_on_bind_rbo_img)(unsigned int target, void *img);
static void (*gles_on_bind_tex_img)(unsigned int target, void *img);

static void resolve_gles_trackers(void)
{
	if (gles_on_bind_rbo_img && gles_on_bind_tex_img)
		return;
	void *hg = dlopen("libGLESv2.so.2", RTLD_NOLOAD);
	if (!hg)
		hg = RTLD_DEFAULT;
	if (!gles_on_bind_rbo_img)
		gles_on_bind_rbo_img = (void (*)(unsigned int, void *))dlsym(hg, "pvr_gles_track_rbo_image");
	if (!gles_on_bind_tex_img)
		gles_on_bind_tex_img = (void (*)(unsigned int, void *))dlsym(hg, "pvr_gles_track_tex_image");
}

static void wrap_glEGLImageTargetRenderbufferStorageOES(unsigned int target, void *img)
{
	INIT();
	if (real_glEGLImageTargetRenderbufferStorageOES)
		real_glEGLImageTargetRenderbufferStorageOES(target, img);
	resolve_gles_trackers();
	if (gles_on_bind_rbo_img)
		gles_on_bind_rbo_img(target, img);
}

static void wrap_glEGLImageTargetTexture2DOES(unsigned int target, void *img)
{
	INIT();
	if (real_glEGLImageTargetTexture2DOES)
		real_glEGLImageTargetTexture2DOES(target, img);
	resolve_gles_trackers();
	if (gles_on_bind_tex_img)
		gles_on_bind_tex_img(target, img);
}

/* ---------------- EGLImage ---------------- */
static int is_modifier_attr(EGLint a)
{
	return a >= EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT && a <= EGL_DMA_BUF_PLANE3_MODIFIER_HI_EXT;
}

EXPORT EGLImageKHR eglCreateImageKHR(EGLDisplay d, EGLContext ctx, EGLenum target,
				      EGLClientBuffer buf, const EGLint *attrs)
{
	INIT();
	if (target != EGL_LINUX_DMA_BUF_EXT || !attrs)
		return real_eglCreateImageKHR(d, ctx, target, buf, attrs);

	EGLint clean[64];
	int n = 0, bad_mod = 0, dmabuf_fd = -1;
	for (int i = 0; attrs[i] != EGL_NONE && n < 62; i += 2) {
		if (is_modifier_attr(attrs[i])) {
			if (attrs[i + 1] != 0)
				bad_mod = 1; /* only DRM_FORMAT_MOD_LINEAR (0) is supported */
			continue;
		}
		if (attrs[i] == EGL_IMAGE_PRESERVED_KHR)
			continue;
		if (attrs[i] == EGL_DMA_BUF_PLANE0_FD_EXT)
			dmabuf_fd = attrs[i + 1];
		clean[n++] = attrs[i];
		clean[n++] = attrs[i + 1];
	}
	clean[n] = EGL_NONE;
	if (bad_mod) {
		DBG("eglCreateImageKHR: non-linear modifier rejected\n");
		set_error(EGL_BAD_MATCH);
		return EGL_NO_IMAGE_KHR;
	}
	EGLImageKHR img = real_eglCreateImageKHR(d, EGL_NO_CONTEXT, target, NULL, clean);
	if (img && dmabuf_fd >= 0)
		dma_image_add(d, img, dmabuf_fd);
	DBG("eglCreateImageKHR(dmabuf=%d) = %p\n", dmabuf_fd, img);
	return img;
}

EXPORT EGLBoolean eglDestroyImageKHR(EGLDisplay d, EGLImageKHR img)
{
	INIT();
	dma_image_remove(img);
	return real_eglDestroyImageKHR(d, img);
}

/* ---------------- configless / surfaceless fallbacks ---------------- */
static EGLConfig fallback_config(EGLDisplay d)
{
	static const EGLint attribs[] = {
		EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
		EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
		EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
		EGL_NONE
	};
	EGLConfig c = NULL;
	EGLint n = 0;
	if (!real_eglChooseConfig(d, attribs, &c, 1, &n) || n < 1)
		return NULL;
	return c;
}

EXPORT EGLContext eglCreateContext(EGLDisplay d, EGLConfig cfg, EGLContext share, const EGLint *attrs)
{
	INIT();
	EGLContext c = real_eglCreateContext(d, cfg, share, attrs);
	if (c == EGL_NO_CONTEXT && cfg == NULL) {
		DBG("configless eglCreateContext failed (0x%x), retrying with a config\n", real_eglGetError());
		EGLConfig fc = fallback_config(d);
		if (fc)
			c = real_eglCreateContext(d, fc, share, attrs);
	}
	DBG("eglCreateContext(cfg=%p) = %p\n", cfg, c);
	return c;
}

static __thread EGLSurface dummy_surface;
static __thread EGLDisplay dummy_display;

EXPORT EGLBoolean eglMakeCurrent(EGLDisplay d, EGLSurface draw, EGLSurface read, EGLContext ctx)
{
	INIT();
	struct pvr_wl_surface *ws = find_wl_surf(draw);
	if (ws) {
		EGLBoolean r = real_eglMakeCurrent(d, ws->dummy_pbuf, ws->dummy_pbuf, ctx);
		if (r && ctx != EGL_NO_CONTEXT && wl_buf_ensure_fbo(ws, &ws->bufs[ws->cur])) {
			resolve_gles_funcs();
			if (gles_set_win_fbo)
				gles_set_win_fbo(ws->bufs[ws->cur].fbo);
			if (gles_viewport)
				gles_viewport(0, 0, ws->width, ws->height);
		}
		return r;
	}
	resolve_gles_funcs();
	if (gles_set_win_fbo)
		gles_set_win_fbo(0);
	EGLBoolean r = real_eglMakeCurrent(d, draw, read, ctx);
	if (!r && ctx != EGL_NO_CONTEXT && draw == EGL_NO_SURFACE && read == EGL_NO_SURFACE) {
		DBG("surfaceless eglMakeCurrent failed (0x%x), using 1x1 pbuffer\n", real_eglGetError());
		if (!dummy_surface || dummy_display != d) {
			static const EGLint pb[] = { EGL_WIDTH, 1, EGL_HEIGHT, 1, EGL_NONE };
			EGLConfig fc = fallback_config(d);
			dummy_surface = fc ? real_eglCreatePbufferSurface(d, fc, pb) : EGL_NO_SURFACE;
			dummy_display = d;
		}
		if (dummy_surface)
			r = real_eglMakeCurrent(d, dummy_surface, dummy_surface, ctx);
	}
	return r;
}

/* ---------------- proc address ---------------- */
struct proc { const char *name; void *fn; };

EXPORT void *eglGetProcAddress(const char *name)
{
	INIT();
	static const struct proc own[] = {
		{ "eglGetPlatformDisplayEXT", (void *)eglGetPlatformDisplayEXT },
		{ "eglGetPlatformDisplay", (void *)eglGetPlatformDisplay },
		{ "eglCreatePlatformWindowSurfaceEXT", (void *)eglCreatePlatformWindowSurfaceEXT },
		{ "eglCreatePlatformWindowSurface", (void *)eglCreatePlatformWindowSurface },
		{ "eglSwapBuffersWithDamageEXT", (void *)eglSwapBuffersWithDamageEXT },
		{ "eglSwapBuffersWithDamageKHR", (void *)eglSwapBuffersWithDamageEXT },
		{ "eglQueryDmaBufFormatsEXT", (void *)eglQueryDmaBufFormatsEXT },
		{ "eglQueryDmaBufModifiersEXT", (void *)eglQueryDmaBufModifiersEXT },
		{ "eglCreateImageKHR", (void *)eglCreateImageKHR },
		{ "eglDestroyImageKHR", (void *)eglDestroyImageKHR },
		{ "eglCreateContext", (void *)eglCreateContext },
		{ "eglMakeCurrent", (void *)eglMakeCurrent },
		{ "eglCreateWindowSurface", (void *)eglCreateWindowSurface },
		{ "eglDestroySurface", (void *)eglDestroySurface },
		{ "eglQuerySurface", (void *)eglQuerySurface },
		{ "eglSwapBuffers", (void *)eglSwapBuffers },
		{ "eglSwapInterval", (void *)eglSwapInterval },
		{ "eglGetDisplay", (void *)eglGetDisplay },
		{ "eglInitialize", (void *)eglInitialize },
		{ "eglQueryString", (void *)eglQueryString },
		{ "eglGetError", (void *)eglGetError },
		{ "glEGLImageTargetRenderbufferStorageOES", (void *)wrap_glEGLImageTargetRenderbufferStorageOES },
		{ "glEGLImageTargetTexture2DOES", (void *)wrap_glEGLImageTargetTexture2DOES },
	};
	if (!name)
		return NULL;
	for (size_t i = 0; i < sizeof(own) / sizeof(own[0]); i++)
		if (!strcmp(name, own[i].name))
			return own[i].fn;
	void *p = real_eglGetProcAddress(name);
	if (!p && h_gles)
		p = dlsym(h_gles, name);
	if (!p)
		p = dlsym(h_egl, name);
	DBG("eglGetProcAddress(%s) = %p\n", name, p);
	return p;
}
