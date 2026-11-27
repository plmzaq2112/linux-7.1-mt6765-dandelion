/*
 * pvr_gbm.c - minimal libgbm.so.1 for the PowerVR GE8320 (DDK 1.13) bridge.
 *
 * The Android PowerVR blobs have no GBM backend.  wlroots 0.17 (phoc) only
 * needs GBM as a buffer allocator: it allocates scanout buffers, exports them
 * as dma-buf and imports them into EGL via EGL_EXT_image_dma_buf_import.
 * We back every gbm_bo with a linear DRM dumb buffer on the KMS device
 * (mediatek-drm), which both the display controller and the GPU (via
 * PVRSRVDmaBufImportDevMem) can use.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <drm/drm_fourcc.h>

#define EXPORT __attribute__((visibility("default")))

#define GBM_BO_USE_SCANOUT   (1 << 0)
#define GBM_BO_USE_CURSOR    (1 << 1)
#define GBM_BO_USE_RENDERING (1 << 2)
#define GBM_BO_USE_WRITE     (1 << 3)
#define GBM_BO_USE_LINEAR    (1 << 4)

#define GBM_BO_IMPORT_WL_BUFFER 0x5501
#define GBM_BO_IMPORT_EGL_IMAGE 0x5502
#define GBM_BO_IMPORT_FD        0x5503
#define GBM_BO_IMPORT_FD_MODIFIER 0x5504

/* Width alignment (pixels) so the PowerVR TPU/PBE pitch constraints are met. */
#define PVR_PITCH_ALIGN_PX 32

union gbm_bo_handle {
	void *ptr;
	int32_t s32;
	uint32_t u32;
	int64_t s64;
	uint64_t u64;
};

struct gbm_device {
	int fd;
};

struct gbm_bo {
	struct gbm_device *dev;
	uint32_t width, height, format, stride, handle, bpp;
	uint64_t size;
	uint64_t modifier;
	void *map;
	void *user_data;
	void (*destroy_user_data)(struct gbm_bo *, void *);
};

struct gbm_surface {
	struct gbm_device *dev;
};

struct gbm_import_fd_data {
	int fd;
	uint32_t width, height, stride, format;
};

struct gbm_import_fd_modifier_data {
	uint32_t width, height, format, num_fds;
	int fds[4];
	int strides[4];
	int offsets[4];
	uint64_t modifier;
};

static uint32_t format_bpp(uint32_t format)
{
	switch (format) {
	case DRM_FORMAT_ARGB8888:
	case DRM_FORMAT_XRGB8888:
	case DRM_FORMAT_ABGR8888:
	case DRM_FORMAT_XBGR8888:
	case DRM_FORMAT_RGBA8888:
	case DRM_FORMAT_RGBX8888:
	case DRM_FORMAT_BGRA8888:
	case DRM_FORMAT_BGRX8888:
	case DRM_FORMAT_ARGB2101010:
	case DRM_FORMAT_XRGB2101010:
	case DRM_FORMAT_ABGR2101010:
	case DRM_FORMAT_XBGR2101010:
		return 32;
	case DRM_FORMAT_RGB888:
	case DRM_FORMAT_BGR888:
		return 24;
	case DRM_FORMAT_RGB565:
	case DRM_FORMAT_BGR565:
		return 16;
	case DRM_FORMAT_R8:
		return 8;
	default:
		return 0;
	}
}

EXPORT struct gbm_device *gbm_create_device(int fd)
{
	struct gbm_device *dev = calloc(1, sizeof(*dev));
	if (!dev)
		return NULL;
	dev->fd = fd;
	return dev;
}

EXPORT void gbm_device_destroy(struct gbm_device *dev)
{
	free(dev);
}

EXPORT int gbm_device_get_fd(struct gbm_device *dev)
{
	return dev->fd;
}

EXPORT const char *gbm_device_get_backend_name(struct gbm_device *dev)
{
	(void)dev;
	return "pvr-dumb";
}

EXPORT int gbm_device_is_format_supported(struct gbm_device *dev, uint32_t format, uint32_t usage)
{
	(void)dev; (void)usage;
	return format_bpp(format) != 0;
}

EXPORT int gbm_device_get_format_modifier_plane_count(struct gbm_device *dev, uint32_t format, uint64_t modifier)
{
	(void)dev;
	if (!format_bpp(format))
		return -1;
	if (modifier != DRM_FORMAT_MOD_LINEAR && modifier != DRM_FORMAT_MOD_INVALID)
		return -1;
	return 1;
}

static struct gbm_bo *bo_create(struct gbm_device *dev, uint32_t w, uint32_t h,
				uint32_t format, uint64_t modifier)
{
	uint32_t bpp = format_bpp(format);
	if (!bpp || !w || !h) {
		errno = EINVAL;
		return NULL;
	}
	struct gbm_bo *bo = calloc(1, sizeof(*bo));
	if (!bo)
		return NULL;

	struct drm_mode_create_dumb creq = {
		.width = (w + PVR_PITCH_ALIGN_PX - 1) & ~(uint32_t)(PVR_PITCH_ALIGN_PX - 1),
		.height = h,
		.bpp = bpp,
	};
	if (ioctl(dev->fd, DRM_IOCTL_MODE_CREATE_DUMB, &creq) < 0) {
		free(bo);
		return NULL;
	}
	bo->dev = dev;
	bo->width = w;
	bo->height = h;
	bo->format = format;
	bo->bpp = bpp;
	bo->stride = creq.pitch;
	bo->handle = creq.handle;
	bo->size = creq.size;
	bo->modifier = modifier;
	return bo;
}

EXPORT struct gbm_bo *gbm_bo_create(struct gbm_device *dev, uint32_t w, uint32_t h,
				     uint32_t format, uint32_t flags)
{
	(void)flags;
	return bo_create(dev, w, h, format, DRM_FORMAT_MOD_INVALID);
}

static int has_linear(const uint64_t *mods, unsigned int count)
{
	if (!mods || !count)
		return 1;
	for (unsigned int i = 0; i < count; i++)
		if (mods[i] == DRM_FORMAT_MOD_LINEAR || mods[i] == DRM_FORMAT_MOD_INVALID)
			return 1;
	return 0;
}

EXPORT struct gbm_bo *gbm_bo_create_with_modifiers(struct gbm_device *dev, uint32_t w, uint32_t h,
						    uint32_t format, const uint64_t *mods, unsigned int count)
{
	if (!has_linear(mods, count)) {
		errno = ENOSYS;
		return NULL;
	}
	return bo_create(dev, w, h, format, DRM_FORMAT_MOD_LINEAR);
}

EXPORT struct gbm_bo *gbm_bo_create_with_modifiers2(struct gbm_device *dev, uint32_t w, uint32_t h,
						     uint32_t format, const uint64_t *mods,
						     unsigned int count, uint32_t flags)
{
	(void)flags;
	return gbm_bo_create_with_modifiers(dev, w, h, format, mods, count);
}

EXPORT struct gbm_bo *gbm_bo_import(struct gbm_device *dev, uint32_t type, void *buffer, uint32_t usage)
{
	(void)usage;
	int fd;
	uint32_t w, h, format, stride;
	uint64_t mod = DRM_FORMAT_MOD_INVALID;

	if (type == GBM_BO_IMPORT_FD) {
		struct gbm_import_fd_data *d = buffer;
		fd = d->fd; w = d->width; h = d->height; format = d->format; stride = d->stride;
	} else if (type == GBM_BO_IMPORT_FD_MODIFIER) {
		struct gbm_import_fd_modifier_data *d = buffer;
		if (d->num_fds != 1 || d->offsets[0] != 0)
			return NULL;
		fd = d->fds[0]; w = d->width; h = d->height; format = d->format;
		stride = d->strides[0]; mod = d->modifier;
		if (mod != DRM_FORMAT_MOD_LINEAR && mod != DRM_FORMAT_MOD_INVALID)
			return NULL;
	} else {
		errno = ENOSYS;
		return NULL;
	}

	struct drm_prime_handle p = { .fd = fd };
	if (ioctl(dev->fd, DRM_IOCTL_PRIME_FD_TO_HANDLE, &p) < 0)
		return NULL;
	struct gbm_bo *bo = calloc(1, sizeof(*bo));
	if (!bo)
		return NULL;
	bo->dev = dev;
	bo->width = w;
	bo->height = h;
	bo->format = format;
	bo->bpp = format_bpp(format);
	bo->stride = stride;
	bo->handle = p.handle;
	bo->size = (uint64_t)stride * h;
	bo->modifier = mod;
	return bo;
}

EXPORT void gbm_bo_destroy(struct gbm_bo *bo)
{
	if (!bo)
		return;
	if (bo->destroy_user_data)
		bo->destroy_user_data(bo, bo->user_data);
	if (bo->map)
		munmap(bo->map, bo->size);
	struct drm_mode_destroy_dumb dreq = { .handle = bo->handle };
	ioctl(bo->dev->fd, DRM_IOCTL_MODE_DESTROY_DUMB, &dreq);
	free(bo);
}

EXPORT int gbm_bo_get_fd(struct gbm_bo *bo)
{
	struct drm_prime_handle p = {
		.handle = bo->handle,
		.flags = DRM_CLOEXEC | DRM_RDWR,
		.fd = -1,
	};
	if (ioctl(bo->dev->fd, DRM_IOCTL_PRIME_HANDLE_TO_FD, &p) < 0)
		return -1;
	return p.fd;
}

EXPORT int gbm_bo_get_fd_for_plane(struct gbm_bo *bo, int plane)
{
	if (plane != 0) {
		errno = EINVAL;
		return -1;
	}
	return gbm_bo_get_fd(bo);
}

EXPORT uint32_t gbm_bo_get_width(struct gbm_bo *bo) { return bo->width; }
EXPORT uint32_t gbm_bo_get_height(struct gbm_bo *bo) { return bo->height; }
EXPORT uint32_t gbm_bo_get_stride(struct gbm_bo *bo) { return bo->stride; }
EXPORT uint32_t gbm_bo_get_stride_for_plane(struct gbm_bo *bo, int plane) { return plane == 0 ? bo->stride : 0; }
EXPORT uint32_t gbm_bo_get_format(struct gbm_bo *bo) { return bo->format; }
EXPORT uint32_t gbm_bo_get_bpp(struct gbm_bo *bo) { return bo->bpp; }
EXPORT uint32_t gbm_bo_get_offset(struct gbm_bo *bo, int plane) { (void)bo; (void)plane; return 0; }
EXPORT int gbm_bo_get_plane_count(struct gbm_bo *bo) { (void)bo; return 1; }
EXPORT uint64_t gbm_bo_get_modifier(struct gbm_bo *bo) { return bo->modifier; }
EXPORT struct gbm_device *gbm_bo_get_device(struct gbm_bo *bo) { return bo->dev; }

EXPORT union gbm_bo_handle gbm_bo_get_handle(struct gbm_bo *bo)
{
	union gbm_bo_handle h;
	h.u64 = 0;
	h.u32 = bo->handle;
	return h;
}

EXPORT union gbm_bo_handle gbm_bo_get_handle_for_plane(struct gbm_bo *bo, int plane)
{
	union gbm_bo_handle h;
	h.u64 = 0;
	if (plane == 0)
		h.u32 = bo->handle;
	else
		h.s32 = -1;
	return h;
}

EXPORT void gbm_bo_set_user_data(struct gbm_bo *bo, void *data,
				 void (*destroy)(struct gbm_bo *, void *))
{
	bo->user_data = data;
	bo->destroy_user_data = destroy;
}

EXPORT void *gbm_bo_get_user_data(struct gbm_bo *bo) { return bo->user_data; }

static void *bo_mmap(struct gbm_bo *bo)
{
	if (bo->map)
		return bo->map;
	struct drm_mode_map_dumb m = { .handle = bo->handle };
	if (ioctl(bo->dev->fd, DRM_IOCTL_MODE_MAP_DUMB, &m) < 0)
		return NULL;
	void *p = mmap(NULL, bo->size, PROT_READ | PROT_WRITE, MAP_SHARED, bo->dev->fd, m.offset);
	if (p == MAP_FAILED)
		return NULL;
	bo->map = p;
	return p;
}

EXPORT void *gbm_bo_map(struct gbm_bo *bo, uint32_t x, uint32_t y, uint32_t w, uint32_t h,
			uint32_t flags, uint32_t *stride, void **map_data)
{
	(void)w; (void)h; (void)flags;
	uint8_t *p = bo_mmap(bo);
	if (!p)
		return NULL;
	*stride = bo->stride;
	*map_data = bo;
	return p + (size_t)y * bo->stride + (size_t)x * (bo->bpp / 8);
}

EXPORT void gbm_bo_unmap(struct gbm_bo *bo, void *map_data)
{
	(void)bo; (void)map_data;
}

EXPORT int gbm_bo_write(struct gbm_bo *bo, const void *buf, size_t count)
{
	void *p = bo_mmap(bo);
	if (!p || count > bo->size)
		return -1;
	memcpy(p, buf, count);
	return 0;
}

EXPORT char *gbm_format_get_name(uint32_t format, char desc[5])
{
	desc[0] = format & 0xff;
	desc[1] = (format >> 8) & 0xff;
	desc[2] = (format >> 16) & 0xff;
	desc[3] = (format >> 24) & 0xff;
	desc[4] = 0;
	return desc;
}

/* Window-surface path is not supported (wlroots never uses it). */
EXPORT struct gbm_surface *gbm_surface_create(struct gbm_device *d, uint32_t w, uint32_t h, uint32_t f, uint32_t fl)
{ (void)d; (void)w; (void)h; (void)f; (void)fl; errno = ENOSYS; return NULL; }
EXPORT struct gbm_surface *gbm_surface_create_with_modifiers(struct gbm_device *d, uint32_t w, uint32_t h, uint32_t f,
							     const uint64_t *m, unsigned int c)
{ (void)d; (void)w; (void)h; (void)f; (void)m; (void)c; errno = ENOSYS; return NULL; }
EXPORT struct gbm_surface *gbm_surface_create_with_modifiers2(struct gbm_device *d, uint32_t w, uint32_t h, uint32_t f,
							      const uint64_t *m, unsigned int c, uint32_t fl)
{ (void)d; (void)w; (void)h; (void)f; (void)m; (void)c; (void)fl; errno = ENOSYS; return NULL; }
EXPORT void gbm_surface_destroy(struct gbm_surface *s) { (void)s; }
EXPORT struct gbm_bo *gbm_surface_lock_front_buffer(struct gbm_surface *s) { (void)s; return NULL; }
EXPORT void gbm_surface_release_buffer(struct gbm_surface *s, struct gbm_bo *bo) { (void)s; (void)bo; }
EXPORT int gbm_surface_has_free_buffers(struct gbm_surface *s) { (void)s; return 0; }
