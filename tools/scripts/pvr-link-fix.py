import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

# 1. DMA_BUF namespace import
p = os.path.join(R, "kernel/drivers/staging/imgtec/pvr_drm.c")
s = open(p).read()
if 'MODULE_IMPORT_NS("DMA_BUF")' not in s:
    # add near the module metadata / end of file
    s += '\nMODULE_IMPORT_NS("DMA_BUF");\n'
    open(p, "w").write(s)
    print("DMA_BUF namespace imported")

# 2. GPU memory usage stubs
p = os.path.join(R, "services/system/rogue/rgx_mtk/pvr_platform_mt6765.c")
s = open(p).read()
if "mtk_get_gpu_memory_usage_fp" not in s:
    s += r'''
/* GPU memory usage reporting hooks referenced by the DDK */
static unsigned int pvr_gpu_mem_usage(void)
{
	return 0;
}

static void pvr_gpu_mem_dump(void)
{
}

unsigned int (*mtk_get_gpu_memory_usage_fp)(void) = pvr_gpu_mem_usage;
void (*mtk_dump_gpu_memory_usage_fp)(void) = pvr_gpu_mem_dump;
'''
    open(p, "w").write(s)
    print("gpu memory stubs added")
