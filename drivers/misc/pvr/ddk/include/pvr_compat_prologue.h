#ifndef __PVR_COMPAT_PROLOGUE_H
#define __PVR_COMPAT_PROLOGUE_H
#include <linux/string.h>
/* strlcpy was removed from the kernel; strscpy has the same call signature */
#define strlcpy(dst, src, n) strscpy(dst, src, n)

#include <linux/dma-buf.h>
#include <linux/iosys-map.h>

static inline void *pvr_dma_buf_vmap(struct dma_buf *dmabuf)
{
	struct iosys_map map;

	if (dma_buf_vmap(dmabuf, &map))
		return NULL;
	return map.vaddr;
}

static inline void pvr_dma_buf_vunmap(struct dma_buf *dmabuf, void *vaddr)
{
	struct iosys_map map = IOSYS_MAP_INIT_VADDR(vaddr);

	dma_buf_vunmap(dmabuf, &map);
}

#define dma_buf_vmap(b) pvr_dma_buf_vmap(b)
#define dma_buf_vunmap(b, v) pvr_dma_buf_vunmap(b, v)


#include <linux/shrinker.h>
/* 7.1 dropped register_shrinker(); bridge to a no-op for bring-up */
static inline int pvr_register_shrinker(struct shrinker *s) { return 0; }
static inline void pvr_unregister_shrinker(struct shrinker *s) { }
#define register_shrinker(s) pvr_register_shrinker(s)
#define unregister_shrinker(s) pvr_unregister_shrinker(s)

#endif
