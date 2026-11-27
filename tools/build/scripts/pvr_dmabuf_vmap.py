#!/usr/bin/env python3
"""add vmap/vunmap to the PVR dma-buf ops

dma_buf_vmap() returns -EINVAL when ->vmap is missing, and mtk-drm's GEM
import helper uses the vmap variant of drm_gem_dma_prime_import_sg_table,
which is why drmPrimeFDToHandle() failed with EINVAL.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/env/linux/physmem_dmabuf.c')
s = p.read_text()

anchor = 'static int PVRDmaBufOpsMMap(struct dma_buf *psDmaBuf, struct vm_area_struct *psVMA)'
assert s.count(anchor) == 1

new_funcs = '''static int PVRDmaBufOpsVmap(struct dma_buf *psDmaBuf, struct iosys_map *psMap)
{
	PMR *psPMR = (PMR *)psDmaBuf->priv;
	IMG_DEVMEM_SIZE_T uiSize;
	IMG_DEV_PHYADDR *pasAddr = NULL;
	IMG_BOOL *pabValid = NULL;
	struct page **ppsPages = NULL;
	IMG_UINT32 uiNumPages, i;
	void *pvAddr;
	PVRSRV_ERROR eError;

	if (PMR_LogicalSize(psPMR, &uiSize) != PVRSRV_OK)
		return -EINVAL;

	uiNumPages = (IMG_UINT32)DIV_ROUND_UP((IMG_UINT64)uiSize, PAGE_SIZE);
	if (!uiNumPages)
		return -EINVAL;

	eError = PMRLockSysPhysAddresses(psPMR);
	if (eError != PVRSRV_OK)
		return -EINVAL;

	pasAddr = kcalloc(uiNumPages, sizeof(*pasAddr), GFP_KERNEL);
	pabValid = kcalloc(uiNumPages, sizeof(*pabValid), GFP_KERNEL);
	ppsPages = kcalloc(uiNumPages, sizeof(*ppsPages), GFP_KERNEL);
	if (!pasAddr || !pabValid || !ppsPages) {
		eError = PVRSRV_ERROR_OUT_OF_MEMORY;
		goto err_free;
	}

	eError = PMR_DevPhysAddr(psPMR, PAGE_SHIFT, uiNumPages, 0, pasAddr,
	                         pabValid);
	if (eError != PVRSRV_OK)
		goto err_free;

	for (i = 0; i < uiNumPages; i++) {
		if (!pabValid[i]) {
			eError = PVRSRV_ERROR_INVALID_PARAMS;
			goto err_free;
		}
		ppsPages[i] = pfn_to_page(PFN_DOWN(pasAddr[i].uiAddr));
	}

	pvAddr = vm_map_ram(ppsPages, uiNumPages, -1);

	kfree(pasAddr);
	kfree(pabValid);
	kfree(ppsPages);
	PMRUnlockSysPhysAddresses(psPMR);

	if (!pvAddr)
		return -ENOMEM;

	iosys_map_set_vaddr(psMap, pvAddr);
	return 0;

err_free:
	kfree(pasAddr);
	kfree(pabValid);
	kfree(ppsPages);
	PMRUnlockSysPhysAddresses(psPMR);
	return -EINVAL;
}

static void PVRDmaBufOpsVunmap(struct dma_buf *psDmaBuf,
                               struct iosys_map *psMap)
{
	PMR *psPMR = (PMR *)psDmaBuf->priv;
	IMG_DEVMEM_SIZE_T uiSize;
	IMG_UINT32 uiNumPages;

	if (PMR_LogicalSize(psPMR, &uiSize) != PVRSRV_OK)
		return;

	uiNumPages = (IMG_UINT32)DIV_ROUND_UP((IMG_UINT64)uiSize, PAGE_SIZE);
	if (!uiNumPages)
		return;

	vm_unmap_ram(iosys_map_rd(psMap), uiNumPages);
}

'''

s = s.replace(anchor, new_funcs + anchor, 1)

old_ops = '''	.mmap          = PVRDmaBufOpsMMap,
};'''
new_ops = '''	.mmap          = PVRDmaBufOpsMMap,
	.vmap          = PVRDmaBufOpsVmap,
	.vunmap        = PVRDmaBufOpsVunmap,
};'''
assert s.count(old_ops) == 1
s = s.replace(old_ops, new_ops, 1)

if '#include <linux/vmalloc.h>' not in s:
    s = s.replace('#include <linux/mm.h>',
                  '#include <linux/mm.h>\n#include <linux/vmalloc.h>\n#include <linux/iosys-map.h>', 1)

p.write_text(s)
print('vmap/vunmap added')
