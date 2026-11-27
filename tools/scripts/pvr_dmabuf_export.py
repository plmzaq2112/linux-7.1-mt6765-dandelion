#!/usr/bin/env python3
"""Allow other drivers (DRM/KMS display) to import PVR dma-bufs.

The DDK stubs out the dma-buf export ops on purpose ("prevent anyone outside
of our driver from importing and using our dmabuf"), which makes
drmPrimeFDToHandle() fail with -ENOSYS. Implement attach/map/unmap by building
an sg_table from the PMR's physical pages so KMS can scan out a Vulkan image
without a CPU copy.
"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/env/linux/physmem_dmabuf.c')
s = p.read_text()

old_attach = '''static int PVRDmaBufOpsAttach(struct dma_buf *psDmaBuf,
#if ((LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)) && \\
	!((LINUX_VERSION_CODE >= KERNEL_VERSION(4, 14, 0)) && (defined(CHROMIUMOS_KERNEL))))
							  struct device *psDev,
#endif
							  struct dma_buf_attachment *psAttachment)
{
	return -ENOSYS;
}
'''

new_attach = '''struct PVR_DMA_BUF_MAP {
	struct sg_table *psSgTable;
	IMG_BOOL bPhysLocked;
};

static int PVRDmaBufOpsAttach(struct dma_buf *psDmaBuf,
#if ((LINUX_VERSION_CODE < KERNEL_VERSION(4, 19, 0)) && \\
	!((LINUX_VERSION_CODE >= KERNEL_VERSION(4, 14, 0)) && (defined(CHROMIUMOS_KERNEL))))
							  struct device *psDev,
#endif
							  struct dma_buf_attachment *psAttachment)
{
	/* Importers (e.g. a DRM display driver) are allowed to attach; the
	 * pages are pinned in map_dma_buf().
	 */
	psAttachment->priv = NULL;
	return 0;
}
'''

old_map = '''static struct sg_table *PVRDmaBufOpsMap(struct dma_buf_attachment *psAttachment,
                                        enum dma_data_direction eDirection)
{
	/* Attach hasn't been called yet */
	return ERR_PTR(-EINVAL);
}

static void PVRDmaBufOpsUnmap(struct dma_buf_attachment *psAttachment,
                              struct sg_table *psTable,
                              enum dma_data_direction eDirection)
{
}
'''

new_map = '''static struct sg_table *PVRDmaBufOpsMap(struct dma_buf_attachment *psAttachment,
                                        enum dma_data_direction eDirection)
{
	struct dma_buf *psDmaBuf = psAttachment->dmabuf;
	PMR *psPMR = (PMR *)psDmaBuf->priv;
	struct PVR_DMA_BUF_MAP *psMap;
	struct sg_table *psTable;
	struct scatterlist *psWalk;
	IMG_DEV_PHYADDR *pasAddr = NULL;
	IMG_BOOL *pabValid = NULL;
	IMG_DEVMEM_SIZE_T uiSize;
	IMG_UINT32 uiNumPages, uiSegs = 0, i;
	PVRSRV_ERROR eError;

	if (PMR_LogicalSize(psPMR, &uiSize) != PVRSRV_OK)
		return ERR_PTR(-EINVAL);

	uiNumPages = (IMG_UINT32)DIV_ROUND_UP((IMG_UINT64)uiSize, PAGE_SIZE);
	if (!uiNumPages)
		return ERR_PTR(-EINVAL);

	eError = PMRLockSysPhysAddresses(psPMR);
	if (eError != PVRSRV_OK)
		return ERR_PTR(-EINVAL);

	pasAddr = kcalloc(uiNumPages, sizeof(*pasAddr), GFP_KERNEL);
	pabValid = kcalloc(uiNumPages, sizeof(*pabValid), GFP_KERNEL);
	psMap = kzalloc(sizeof(*psMap), GFP_KERNEL);
	psTable = kzalloc(sizeof(*psTable), GFP_KERNEL);
	if (!pasAddr || !pabValid || !psMap || !psTable) {
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
		if (i == 0 ||
		    pasAddr[i].uiAddr != pasAddr[i - 1].uiAddr + PAGE_SIZE)
			uiSegs++;
	}

	if (sg_alloc_table(psTable, uiSegs, GFP_KERNEL))
		goto err_free;

	psWalk = psTable->sgl;
	i = 0;
	while (i < uiNumPages) {
		IMG_UINT32 j = i + 1;

		while (j < uiNumPages &&
		       pasAddr[j].uiAddr == pasAddr[j - 1].uiAddr + PAGE_SIZE)
			j++;

		sg_set_page(psWalk, pfn_to_page(PFN_DOWN(pasAddr[i].uiAddr)),
		            (j - i) * PAGE_SIZE, 0);
		psWalk = sg_next(psWalk);
		i = j;
	}
	psTable->nents = psTable->orig_nents = uiSegs;

	psMap->psSgTable = psTable;
	psMap->bPhysLocked = IMG_TRUE;
	psAttachment->priv = psMap;

	kfree(pasAddr);
	kfree(pabValid);

	PVR_DPF((PVR_DBG_WARNING,
	         "%s: dmabuf %llu KiB mapped for import, %u sg segment(s)",
	         __func__, (unsigned long long)(uiSize >> 10), uiSegs));

	return psTable;

err_free:
	kfree(pasAddr);
	kfree(pabValid);
	kfree(psMap);
	kfree(psTable);
	PMRUnlockSysPhysAddresses(psPMR);
	return ERR_PTR(-EINVAL);
}

static void PVRDmaBufOpsUnmap(struct dma_buf_attachment *psAttachment,
                              struct sg_table *psTable,
                              enum dma_data_direction eDirection)
{
	struct dma_buf *psDmaBuf = psAttachment->dmabuf;
	PMR *psPMR = (PMR *)psDmaBuf->priv;
	struct PVR_DMA_BUF_MAP *psMap = psAttachment->priv;

	if (!psMap)
		return;

	sg_free_table(psTable);
	kfree(psTable);
	if (psMap->bPhysLocked)
		PMRUnlockSysPhysAddresses(psPMR);
	kfree(psMap);
	psAttachment->priv = NULL;
}
'''

assert s.count(old_attach) == 1, 'attach anchor'
assert s.count(old_map) == 1, 'map anchor'
s = s.replace(old_attach, new_attach, 1)
s = s.replace(old_map, new_map, 1)

if '#include <linux/mm.h>' not in s:
    s = s.replace('#include <linux/scatterlist.h>',
                  '#include <linux/scatterlist.h>\n#include <linux/mm.h>', 1)

p.write_text(s)
print('dmabuf export ops implemented')
