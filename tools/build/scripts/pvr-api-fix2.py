import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# 1. disable ion in the DDK config header
cp = os.path.join(R, "include/config_kernel_user_mt6765.h")
s = open(cp).read()
if "#define SUPPORT_ION" in s:
    s = s.replace("#define SUPPORT_ION", "/* #define SUPPORT_ION */")
    open(cp, "w").write(s)
    print("SUPPORT_ION disabled")

# 2. dma_buf_vmap/vunmap take iosys_map in 7.1
pro = os.path.join(R, "include/pvr_compat_prologue.h")
s = open(pro).read()
if "pvr_dma_buf_vmap" not in s:
    s = s.replace("#endif\n", """
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

#endif
""")
    open(pro, "w").write(s)
    print("dma_buf wrappers added")
