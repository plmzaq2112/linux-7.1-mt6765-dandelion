#!/usr/bin/env python3
"""mesa: time the render submit stages (PVR13_TIME=1)"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_job_render.c')
s = p.read_text()

old = '''   struct pvr_winsys_render_submit_info submit_info;
   struct pvr_device *device = ctx->device;
   VkResult result;

   pvr_render_job_ws_submit_info_init(ctx,
                                      job,
                                      wait_geom,
                                      wait_frag,
                                      &submit_info);
'''
new = '''   struct pvr_winsys_render_submit_info submit_info;
   struct pvr_device *device = ctx->device;
   VkResult result;
   uint64_t t_start = 0, t_info = 0, t_ws = 0;

   if (getenv("PVR13_TIME"))
      t_start = os_time_get_nano();

   pvr_render_job_ws_submit_info_init(ctx,
                                      job,
                                      wait_geom,
                                      wait_frag,
                                      &submit_info);

   if (t_start)
      t_info = os_time_get_nano();
'''
assert s.count(old) == 1, 'anchor 1'
s = s.replace(old, new, 1)

old2 = '''   result = device->ws->ops->render_submit(ctx->ws_ctx,
                                           &submit_info,
                                           &device->pdevice->dev_info,
                                           signal_sync_geom,
                                           signal_sync_frag);
   if (result != VK_SUCCESS)
      return result;
'''
new2 = '''   result = device->ws->ops->render_submit(ctx->ws_ctx,
                                           &submit_info,
                                           &device->pdevice->dev_info,
                                           signal_sync_geom,
                                           signal_sync_frag);

   if (t_start) {
      uint64_t now = os_time_get_nano();

      fprintf(stderr,
              "pvr-time: job=%u init=%llu us ws=%llu us\\n",
              submit_info.job_num,
              (unsigned long long)((t_info - t_start) / 1000),
              (unsigned long long)((now - t_info) / 1000));
   }

   if (result != VK_SUCCESS)
      return result;
'''
assert s.count(old2) == 1, 'anchor 2'
s = s.replace(old2, new2, 1)

p.write_text(s)
print('mesa submit timing added')
