import os

R = "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk"

drm = os.path.join(R, "kernel/drivers/staging/imgtec/pvr_drm.c")
s = open(drm).read()
s = s.replace("\t.dev_priv_size\t\t= 0,\n", "")
s = s.replace("\t.date\t\t\t= PVR_DRM_DRIVER_DATE,\n", "")
s = s.replace("DRM_RENDER_ALLOW | DRM_UNLOCKED", "DRM_RENDER_ALLOW")
open(drm, "w").write(s)
print("pvr_drm patched")

pl = os.path.join(R, "kernel/drivers/staging/imgtec/pvr_platform_drv.c")
s = open(pl).read()
s = s.replace("static int pvr_remove(struct platform_device *pdev)",
              "static void pvr_remove(struct platform_device *pdev)")
open(pl, "w").write(s)
print("pvr_platform_drv patched")

sf = os.path.join(R, "kernel/drivers/staging/imgtec/pvr_sync_file.c")
s = open(sf).read()
s = s.replace("\tfence_ops->timeline_value_str(fence, time, sizeof(time));",
              "\t/* timeline_value_str removed in 6.11 */")
open(sf, "w").write(s)
print("pvr_sync_file patched")

ct = os.path.join(R, "kernel/drivers/staging/imgtec/pvr_counting_timeline.c")
s = open(ct).read()
s = s.replace("\t\t\tobj->fence->ops->fence_value_str(obj->fence,\n\t\t\t\t\t\t\t value, sizeof(value));",
              "\t\t\t/* fence_value_str removed in 6.11 */")
open(ct, "w").write(s)
print("pvr_counting_timeline patched")
