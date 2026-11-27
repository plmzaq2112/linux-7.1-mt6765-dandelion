/* Minimal vkCmdClearColorImage test: linear host-visible image, TQ path. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <vulkan/vulkan.h>

#ifndef W
#define W 64
#endif
#ifndef H
#define H 64
#endif

static void die(const char *what, VkResult r)
{
    if (r == VK_SUCCESS)
        return;
    fprintf(stderr, "%s failed: %d\n", what, r);
    exit(1);
}

int main(void)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_clear_tq",
        .apiVersion = VK_API_VERSION_1_0,
    };
    VkInstanceCreateInfo ici = {
        .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &app,
    };
    VkInstance inst;
    VkResult r = vkCreateInstance(&ici, NULL, &inst);
    die("vkCreateInstance", r);

    uint32_t n = 0;
    vkEnumeratePhysicalDevices(inst, &n, NULL);
    if (!n) { fprintf(stderr, "no device\n"); return 1; }
    VkPhysicalDevice *pds = calloc(n, sizeof(*pds));
    vkEnumeratePhysicalDevices(inst, &n, pds);
    VkPhysicalDevice pd = pds[0];

    uint32_t qn = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(pd, &qn, NULL);
    VkQueueFamilyProperties *qf = calloc(qn, sizeof(*qf));
    vkGetPhysicalDeviceQueueFamilyProperties(pd, &qn, qf);
    uint32_t qi = 0;
    for (uint32_t i = 0; i < qn; i++) {
        if (qf[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) { qi = i; break; }
    }

    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = qi,
        .queueCount = 1,
        .pQueuePriorities = &prio,
    };
    VkDeviceCreateInfo dci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
        .queueCreateInfoCount = 1,
        .pQueueCreateInfos = &qci,
    };
    VkDevice dev;
    r = vkCreateDevice(pd, &dci, NULL, &dev);
    die("vkCreateDevice", r);
    VkQueue q;
    vkGetDeviceQueue(dev, qi, 0, &q);

    VkImageCreateInfo img = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .extent = { W, H, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    VkImage image;
    r = vkCreateImage(dev, &img, NULL, &image);
    die("vkCreateImage", r);

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(dev, image, &mr);
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    uint32_t mt = 0;
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
        if ((mr.memoryTypeBits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) &&
            (mp.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
            mt = i; break;
        }
    }
    fprintf(stderr, "image mem: size=%llu type=%u\n",
            (unsigned long long)mr.size, mt);

    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = mr.size,
        .memoryTypeIndex = mt,
    };
    VkDeviceMemory mem;
    r = vkAllocateMemory(dev, &mai, NULL, &mem);
    die("vkAllocateMemory", r);
    r = vkBindImageMemory(dev, image, mem, 0);
    die("vkBindImageMemory", r);

    VkCommandPoolCreateInfo pci = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = qi,
    };
    VkCommandPool pool;
    r = vkCreateCommandPool(dev, &pci, NULL, &pool);
    die("vkCreateCommandPool", r);
    VkCommandBufferAllocateInfo cbai = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = pool,
        .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        .commandBufferCount = 1,
    };
    VkCommandBuffer cb;
    r = vkAllocateCommandBuffers(dev, &cbai, &cb);
    die("vkAllocateCommandBuffers", r);

    VkCommandBufferBeginInfo bi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
    };
    vkBeginCommandBuffer(cb, &bi);

    VkImageSubresourceRange range = {
        .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
        .baseMipLevel = 0,
        .levelCount = 1,
        .baseArrayLayer = 0,
        .layerCount = 1,
    };
    VkImageMemoryBarrier to_general = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .newLayout = VK_IMAGE_LAYOUT_GENERAL,
        .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .image = image,
        .subresourceRange = range,
        .srcAccessMask = 0,
        .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
    };
    vkCmdPipelineBarrier(cb,
                         VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         0, 0, NULL, 0, NULL, 1, &to_general);

    VkClearColorValue cv;
    cv.float32[0] = 1.0f;
    cv.float32[1] = 0.0f;
    cv.float32[2] = 0.0f;
    cv.float32[3] = 1.0f;
    vkCmdClearColorImage(cb, image, VK_IMAGE_LAYOUT_GENERAL,
                         &cv, 1, &range);

    VkImageMemoryBarrier to_host = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .oldLayout = VK_IMAGE_LAYOUT_GENERAL,
        .newLayout = VK_IMAGE_LAYOUT_GENERAL,
        .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .image = image,
        .subresourceRange = range,
        .srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
        .dstAccessMask = VK_ACCESS_HOST_READ_BIT,
    };
    vkCmdPipelineBarrier(cb,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT,
                         0, 0, NULL, 0, NULL, 1, &to_host);

    r = vkEndCommandBuffer(cb);
    die("vkEndCommandBuffer", r);

    VkSubmitInfo si = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1,
        .pCommandBuffers = &cb,
    };
    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);

    if (getenv("VK_TQ_LOOP")) {
        int loop = atoi(getenv("VK_TQ_LOOP"));
        struct timespec a, b;
        double tot = 0.0;

        for (int i = 0; i < loop; i++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
            if (r != VK_SUCCESS) break;
            r = vkQueueWaitIdle(q);
            clock_gettime(CLOCK_MONOTONIC, &b);
            if (r != VK_SUCCESS) break;
            tot += (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("tq bench %dx%d: %d frames, %.2f ms/frame\n", W, H, loop,
               1000.0 * tot / loop);
    }

    void *ptr = NULL;
    r = vkMapMemory(dev, mem, 0, VK_WHOLE_SIZE, 0, &ptr);
    die("vkMapMemory", r);

    const uint32_t want = 0xff0000ffu;
    uint32_t hits = 0, nonzero = 0;
    uint32_t *p = ptr;
    size_t words = (size_t)(mr.size / 4);
    for (size_t i = 0; i < words; i++) {
        if (p[i]) nonzero++;
        if (p[i] == want) hits++;
    }
    printf("words=%zu nonzero=%u red=%u\n", words, nonzero, hits);
    printf("first32=%08x last32=%08x\n", p[0], p[words - 1]);
    printf("corners: (0,0)=%08x (W-1,0)=%08x (0,H-1)=%08x (W-1,H-1)=%08x\n",
           p[0], p[W - 1], p[(size_t)(H - 1) * W], p[(size_t)(H - 1) * W + W - 1]);

    vkUnmapMemory(dev, mem);
    return hits ? 0 : 2;
}
