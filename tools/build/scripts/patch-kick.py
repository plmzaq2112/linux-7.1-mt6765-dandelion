import os

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

if "pvr_kick" in s:
    print("already patched")
    raise SystemExit(0)

# include msleep
if "#include <linux/delay.h>" not in s:
    s = s.replace("#include <linux/io.h>\n", "#include <linux/io.h>\n#include <linux/delay.h>\n", 1)

anchor = 'static int pvr_fwtrace = 0;\n'
if anchor not in s:
    raise SystemExit("param anchor missing")

decl = ('static int pvr_kick = 0;\n'
        'module_param(pvr_kick, int, 0644);\n'
        'MODULE_PARM_DESC(pvr_kick, "repeatedly kick MTS_SCHEDULE after POW and log readback");\n\n')
s = s.replace(anchor, decl + anchor, 1)

call = '\tpvr_pow_snap(psDevInfo, "sent", &sPowCmd, ui32CmdKCCBSlot);\n'
if call not in s:
    raise SystemExit("sent anchor missing")

kick = '''
	if (pvr_kick)
	{
		IMG_UINT32 i;

		for (i = 0; i < 40; i++)
		{
			IMG_UINT32 ui32Rb;

			OSWriteMemoryBarrier();
			OSWriteHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_MTS_SCHEDULE,
			               (RGXFWIF_DM_GP & ~RGX_CR_MTS_SCHEDULE_DM_CLRMSK) |
			               RGX_CR_MTS_SCHEDULE_TASK_NON_COUNTED);
			OSMemoryBarrier();
			ui32Rb = OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_MTS_SCHEDULE);

			if ((i % 5) == 0)
			{
				pr_info("pvr-mtk: KICK %u rb=%08x kccb=%u/%u kcmds=%u pow=%u\\n",
				        i, ui32Rb,
				        psDevInfo->psKernelCCBCtl->ui32WriteOffset,
				        psDevInfo->psKernelCCBCtl->ui32ReadOffset,
				        psDevInfo->psRGXFWIfFwOsData->ui32KCCBCmdsExecuted,
				        (unsigned)psDevInfo->psRGXFWIfFwSysData->ePowState);
			}
			msleep(50);
		}
	}
'''
s = s.replace(call, call + kick, 1)
open(p, "w").write(s)
print("pvr_kick added")
