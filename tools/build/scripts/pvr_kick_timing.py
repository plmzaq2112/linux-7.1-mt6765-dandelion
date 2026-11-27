#!/usr/bin/env python3
"""kernel: timestamp the TA3D kick path (pvr_kick_time module param)"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxta3d.c')
s = p.read_text()

# 1. module param + helpers, after the existing pvr_dump_stream param
old = '''static int pvr_dump_stream;
module_param(pvr_dump_stream, int, 0644);
MODULE_PARM_DESC(pvr_dump_stream, "Dump next N 1.13 VDM control streams via MMU translation");
'''
new = '''static int pvr_dump_stream;
module_param(pvr_dump_stream, int, 0644);
MODULE_PARM_DESC(pvr_dump_stream, "Dump next N 1.13 VDM control streams via MMU translation");

static int pvr_kick_time;
module_param(pvr_kick_time, int, 0644);
MODULE_PARM_DESC(pvr_kick_time, "Timestamp the next N TA3D kicks (microseconds)");

static IMG_BOOL g_bKickTiming;
static IMG_UINT64 g_ui64KickT0;

#define PVR_KICK_T(tag) \\
	do { \\
		if (g_bKickTiming) \\
			pr_info("pvr-kick: %-10s +%llu us\\n", tag, \\
			        (unsigned long long)(OSClockus64() - g_ui64KickT0)); \\
	} while (0)
'''
assert s.count(old) == 1, 'param anchor'
s = s.replace(old, new, 1)

# 2. start timing at function entry
old = '''	IMG_UINT32				ui32ClientPRUpdateCount = 0;
'''
new = '''	IMG_UINT32				ui32ClientPRUpdateCount = 0;

	g_bKickTiming = (pvr_kick_time-- > 0);
	if (g_bKickTiming)
	{
		g_ui64KickT0 = OSClockus64();
		pr_info("pvr-kick: ==== kick job=%u ta=%u 3d=%u pr=%u ====\\n",
		        ui32IntJobRef, ui32TACmdSize, ui323DCmdSize, ui323DPRCmdSize);
	}
'''
assert s.count(old) == 1, 'entry anchor'
s = s.replace(old, new, 1)

# 3. before the 3D/combined kick
old = '''			s3DKCCBCmd.uCmdData.sCmdKickData = s3DCmdKickData;
		}

		LOOP_UNTIL_TIMEOUT(MAX_HW_TIME_US)'''
new = '''			s3DKCCBCmd.uCmdData.sCmdKickData = s3DCmdKickData;
		}

		PVR_KICK_T("pre-sched");

		LOOP_UNTIL_TIMEOUT(MAX_HW_TIME_US)'''
assert s.count(old) == 1, 'pre-sched anchor'
s = s.replace(old, new, 1)

# 4. after the kick, before the error check
old = '''	/*
	 * Now check eError (which may have returned an error from our earlier calls
	 * to RGXCmdHelperAcquireCmdCCB) - we needed to process any flush command first
	 * so we check it now...
	 */'''
new = '''	PVR_KICK_T("sched-done");

	/*
	 * Now check eError (which may have returned an error from our earlier calls
	 * to RGXCmdHelperAcquireCmdCCB) - we needed to process any flush command first
	 * so we check it now...
	 */'''
assert s.count(old) == 1, 'sched-done anchor'
s = s.replace(old, new, 1)

# 5. end of a successful kick
old = '''	OSLockRelease(psRenderContext->hLock);

	return PVRSRV_OK;
'''
new = '''	OSLockRelease(psRenderContext->hLock);

	PVR_KICK_T("tail");
	g_bKickTiming = IMG_FALSE;

	return PVRSRV_OK;
'''
assert s.count(old) == 1, 'tail anchor'
s = s.replace(old, new, 1)

p.write_text(s)
print('kick timing instrumented')
