#ifndef __PVR_PFN_T_SHIM_H
#define __PVR_PFN_T_SHIM_H
#include <linux/pfn.h>
#include <linux/mm.h>

/* pfn_t was removed from the kernel; the DDK only needs a plain PFN. */
typedef unsigned long pfn_t;

#define pfn_to_pfn_t(x)        ((pfn_t)(x))
#define pfn_t_to_pfn(x)        ((unsigned long)(x))
#define pfn_t_to_page(x)       pfn_to_page((unsigned long)(x))
#define page_to_pfn_t(p)       ((pfn_t)page_to_pfn(p))
#define phys_to_pfn_t(a, f)    ((pfn_t)((phys_addr_t)(a) >> PAGE_SHIFT))
#define pfn_t_valid(x)         ((x) != 0)
#endif
