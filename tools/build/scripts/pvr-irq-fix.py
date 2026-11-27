import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"
p = os.path.join(R, "services/system/rogue/rgx_mtk/sysconfig.c")
s = open(p).read()

old = """		irq_res = platform_get_resource(gpsPVRCfgDev,
						IORESOURCE_IRQ, 0);

		if (irq_res) {
			gsDevices[0].ui32IRQ = irq_res->start;
			g32SysIrq = irq_res->start;

			PVR_LOG(("irq_res = 0x%x", (int)irq_res->start));
		} else {
			PVR_DPF((PVR_DBG_ERROR, "irq_res = NULL!"));
			return PVRSRV_ERROR_INIT_FAILURE;
		}
"""

new = """		irq_res = platform_get_resource(gpsPVRCfgDev,
						IORESOURCE_IRQ, 0);

		if (irq_res) {
			gsDevices[0].ui32IRQ = irq_res->start;
			g32SysIrq = irq_res->start;
			pr_info("pvr-mtk: irq_res = 0x%x\\n", (int)irq_res->start);
		} else {
			int irq = platform_get_irq(gpsPVRCfgDev, 0);
			if (irq > 0) {
				gsDevices[0].ui32IRQ = irq;
				g32SysIrq = irq;
				pr_info("pvr-mtk: irq (platform_get_irq) = %d\\n", irq);
			} else {
				pr_err("pvr-mtk: no IRQ (%d)\\n", irq);
				return PVRSRV_ERROR_INIT_FAILURE;
			}
		}
"""

if old not in s:
    raise SystemExit("irq block not found")
s = s.replace(old, new)

# log the reg resource too
s = s.replace('''			gsDevices[0].sRegsCpuPBase.uiAddr = reg_res->start;
			gsDevices[0].ui32RegsSize = resource_size(reg_res);

			PVR_LOG(("reg_res = 0x%x, 0x%x",''',
'''			gsDevices[0].sRegsCpuPBase.uiAddr = reg_res->start;
			gsDevices[0].ui32RegsSize = resource_size(reg_res);
			pr_info("pvr-mtk: reg_res = 0x%x, 0x%x\\n",
				(int)reg_res->start, (int)resource_size(reg_res));

			PVR_LOG(("reg_res = 0x%x, 0x%x",''')

s = s.replace('''		} else {
			PVR_DPF((PVR_DBG_ERROR, "reg_res = NULL!"));
			return PVRSRV_ERROR_INIT_FAILURE;
		}''',
'''		} else {
			pr_err("pvr-mtk: no MEM resource\\n");
			return PVRSRV_ERROR_INIT_FAILURE;
		}''')

open(p, "w").write(s)
print("sysconfig patched")
