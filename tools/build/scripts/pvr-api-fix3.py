import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
S = os.path.join(R, "include/mtk_plat_stub/linux")
os.makedirs(S, exist_ok=True)

open(os.path.join(S, "pfn_t.h"), "w").write("""#ifndef __PVR_PFN_T_SHIM_H
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
""")
print("pfn_t shim written")

pro = os.path.join(R, "include/pvr_compat_prologue.h")
s = open(pro).read()
if "pvr_register_shrinker" not in s:
    s = s.replace("#endif\n", """
#include <linux/shrinker.h>
/* 7.1 dropped register_shrinker(); bridge to a no-op for bring-up */
static inline int pvr_register_shrinker(struct shrinker *s) { return 0; }
static inline void pvr_unregister_shrinker(struct shrinker *s) { }
#define register_shrinker(s) pvr_register_shrinker(s)
#define unregister_shrinker(s) pvr_unregister_shrinker(s)

#endif
""")
    open(pro, "w").write(s)
    print("shrinker wrappers added")
