#!/usr/bin/env python3
"""mesa: stage timing inside pvr_driver_queue_submit (PVR13_TIME=1)"""
from pathlib import Path

p = Path('/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan/pvr_arch_queue.c')
s = p.read_text()

old = '''static VkResult pvr_driver_queue_submit(struct vk_queue *queue,
                                        struct vk_queue_submit *submit)
{
   struct pvr_queue *driver_queue = container_of(queue, struct pvr_queue, vk);
   struct pvr_device *device = driver_queue->device;
   VkResult result;

   result = pvr_clear_last_submits_syncs(driver_queue);
   if (result != VK_SUCCESS)
      return result;

   if (submit->wait_count) {
      result = pvr_process_queue_waits(driver_queue,
                                       submit->waits,
                                       submit->wait_count);
      if (result != VK_SUCCESS)
         return result;
   }

   struct pvr_suspended_data suspended_data = {0};

   for (uint32_t i = 0U; i < submit->command_buffer_count; i++) {
      result = pvr_process_cmd_buffer(
         device,
         driver_queue,
         container_of(submit->command_buffers[i], struct pvr_cmd_buffer, vk),
         &suspended_data);
      if (result != VK_SUCCESS)
         return result;
   }

   assert(suspended_data.rts == NULL && "suspended graphics job never resumed");

   result = pvr_process_queue_signals(driver_queue,
                                      submit->signals,
                                      submit->signal_count);
   if (result != VK_SUCCESS)
      return result;

   return VK_SUCCESS;
}'''

new = '''static VkResult pvr_driver_queue_submit(struct vk_queue *queue,
                                        struct vk_queue_submit *submit)
{
   struct pvr_queue *driver_queue = container_of(queue, struct pvr_queue, vk);
   struct pvr_device *device = driver_queue->device;
   VkResult result;
   struct timespec q0, q1, q2, q3, q4;
   const bool timing = getenv("PVR13_TIME") != NULL;

#define QSTAMP(ts) clock_gettime(CLOCK_MONOTONIC, &(ts))
#define QDELTA(a, b)                                                       \\
   (1000ULL * (uint64_t)((b).tv_sec - (a).tv_sec) +                        \\
    (uint64_t)((b).tv_nsec - (a).tv_nsec) / 1000ULL)

   if (timing)
      QSTAMP(q0);

   result = pvr_clear_last_submits_syncs(driver_queue);
   if (result != VK_SUCCESS)
      return result;

   if (timing)
      QSTAMP(q1);

   if (submit->wait_count) {
      result = pvr_process_queue_waits(driver_queue,
                                       submit->waits,
                                       submit->wait_count);
      if (result != VK_SUCCESS)
         return result;
   }

   if (timing)
      QSTAMP(q2);

   struct pvr_suspended_data suspended_data = {0};

   for (uint32_t i = 0U; i < submit->command_buffer_count; i++) {
      result = pvr_process_cmd_buffer(
         device,
         driver_queue,
         container_of(submit->command_buffers[i], struct pvr_cmd_buffer, vk),
         &suspended_data);
      if (result != VK_SUCCESS)
         return result;
   }

   if (timing)
      QSTAMP(q3);

   assert(suspended_data.rts == NULL && "suspended graphics job never resumed");

   result = pvr_process_queue_signals(driver_queue,
                                      submit->signals,
                                      submit->signal_count);

   if (timing) {
      QSTAMP(q4);
      fprintf(stderr,
              "pvr-q: clear=%llu us waits=%llu us cmds=%llu us sig=%llu us\\n",
              (unsigned long long)QDELTA(q0, q1),
              (unsigned long long)QDELTA(q1, q2),
              (unsigned long long)QDELTA(q2, q3),
              (unsigned long long)QDELTA(q3, q4));
   }

   if (result != VK_SUCCESS)
      return result;

   return VK_SUCCESS;
}'''

assert s.count(old) == 1, 'submit fn anchor'
s = s.replace(old, new, 1)

if '#include <time.h>' not in s:
    s = s.replace('#include "pvr_arch_queue.h"',
                  '#include <time.h>\n\n#include "pvr_arch_queue.h"', 1)

p.write_text(s)
print('queue submit stages instrumented')
