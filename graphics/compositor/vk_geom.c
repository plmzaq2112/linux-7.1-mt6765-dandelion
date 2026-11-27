/* Geometry probe: same tri.vert as vk_triangle, but viewport/scissor are
 * taken from the environment (VX VY VW VH SX SY SW SH) and a pixel map plus
 * the non-zero bounding box are printed, so we can tell "scaled" from
 * "clipped" output. */
#include <stdint.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

#include "tri_vert_spv.h"
#include "tri_frag_spv.h"

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

static VkShaderModule make_shader(VkDevice dev, const unsigned char *code,
                                  unsigned int size)
{
    VkShaderModuleCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
        .codeSize = size,
        .pCode = (const uint32_t *)code,
    };
    VkShaderModule m;
    VkResult r = vkCreateShaderModule(dev, &ci, NULL, &m);
    die("vkCreateShaderModule", r);
    return m;
}

int main(void)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_triangle",
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

    const int tiled = getenv("VK_GEOM_TILED") != NULL;

    VkImageCreateInfo img = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .extent = { W, H, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR, /* overridden below when tiled */
        .usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                 VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    if (tiled)
        img.tiling = VK_IMAGE_TILING_OPTIMAL;

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
    if (tiled &&
        !(mp.memoryTypes[mt].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)) {
        for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
            if (mr.memoryTypeBits & (1u << i)) {
                mt = i;
                break;
            }
        }
    }
    fprintf(stderr, "image mem: size=%llu type=%u tiled=%d\n",
            (unsigned long long)mr.size, mt, tiled);

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

    VkImageViewCreateInfo ivci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = image,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    VkImageView view;
    r = vkCreateImageView(dev, &ivci, NULL, &view);
    die("vkCreateImageView", r);

    VkAttachmentDescription att = {
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR, /* see nop_* below */
        .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
        .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .finalLayout = VK_IMAGE_LAYOUT_GENERAL,
    };
    VkAttachmentReference ref = { 0, VK_IMAGE_LAYOUT_GENERAL };
    if (getenv("VK_GEOM_NOCLEAR"))
        att.loadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;

    VkSubpassDescription sp = {
        .pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
        .colorAttachmentCount = 1,
        .pColorAttachments = &ref,
    };
    VkRenderPassCreateInfo rpci = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
        .attachmentCount = 1,
        .pAttachments = &att,
        .subpassCount = 1,
        .pSubpasses = &sp,
    };
    VkRenderPass rp;
    r = vkCreateRenderPass(dev, &rpci, NULL, &rp);
    die("vkCreateRenderPass", r);

    VkFramebufferCreateInfo fbci = {
        .sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
        .renderPass = rp,
        .attachmentCount = 1,
        .pAttachments = &view,
        .width = W,
        .height = H,
        .layers = 1,
    };
    VkFramebuffer fb;
    r = vkCreateFramebuffer(dev, &fbci, NULL, &fb);
    die("vkCreateFramebuffer", r);

    VkShaderModule vs = make_shader(dev, tri_vert_spv, tri_vert_spv_len);
    VkShaderModule fs = make_shader(dev, tri_frag_spv, tri_frag_spv_len);

    VkPipelineShaderStageCreateInfo stages[2] = {
        {
            .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
            .stage = VK_SHADER_STAGE_VERTEX_BIT,
            .module = vs,
            .pName = "main",
        },
        {
            .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
            .stage = VK_SHADER_STAGE_FRAGMENT_BIT,
            .module = fs,
            .pName = "main",
        },
    };
    VkPipelineVertexInputStateCreateInfo vi = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
    };
    VkPipelineInputAssemblyStateCreateInfo ia = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
        .topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    };
    float vx = getenv("VX") ? (float)atoi(getenv("VX")) : 0.0f;
    float vy = getenv("VY") ? (float)atoi(getenv("VY")) : 0.0f;
    float vw = getenv("VW") ? (float)atoi(getenv("VW")) : (float)W;
    float vh = getenv("VH") ? (float)atoi(getenv("VH")) : (float)H;
    int32_t sx = getenv("SX") ? atoi(getenv("SX")) : 0;
    int32_t sy = getenv("SY") ? atoi(getenv("SY")) : 0;
    uint32_t sw = getenv("SW") ? (uint32_t)atoi(getenv("SW")) : W;
    uint32_t sh = getenv("SH") ? (uint32_t)atoi(getenv("SH")) : H;
    VkViewport vp = { vx, vy, vw, vh, 0, 1 };
    VkRect2D sc = { { sx, sy }, { sw, sh } };
    fprintf(stderr, "viewport=(%g,%g %gx%g) scissor=(%d,%d %ux%u)\n",
            vx, vy, vw, vh, sx, sy, sw, sh);
    const int dyn_sc = getenv("VK_GEOM_DYNSC") != NULL;
    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .pViewports = dyn_sc ? NULL : &vp,
        .scissorCount = 1,
        .pScissors = dyn_sc ? NULL : &sc,
    };
    VkDynamicState dyn_states[2] = { VK_DYNAMIC_STATE_VIEWPORT,
                                     VK_DYNAMIC_STATE_SCISSOR };
    VkPipelineDynamicStateCreateInfo dyn_ci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO,
        .dynamicStateCount = dyn_sc ? 2 : 0,
        .pDynamicStates = dyn_states,
    };
    VkPipelineRasterizationStateCreateInfo rs = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO,
        .polygonMode = VK_POLYGON_MODE_FILL,
        .cullMode = VK_CULL_MODE_NONE,
        .frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE,
        .lineWidth = 1.0f,
    };
    VkPipelineMultisampleStateCreateInfo ms = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
        .rasterizationSamples = VK_SAMPLE_COUNT_1_BIT,
    };
    VkPipelineColorBlendAttachmentState cba = {
        .blendEnable = VK_FALSE,
        .colorWriteMask = 0xf,
    };
    VkPipelineColorBlendStateCreateInfo cb = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        .attachmentCount = 1,
        .pAttachments = &cba,
    };
    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
    };
    VkPipelineLayout pl;
    r = vkCreatePipelineLayout(dev, &plci, NULL, &pl);
    die("vkCreatePipelineLayout", r);

    VkGraphicsPipelineCreateInfo gpci = {
        .sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
        .stageCount = 2,
        .pStages = stages,
        .pVertexInputState = &vi,
        .pInputAssemblyState = &ia,
        .pViewportState = &vps,
        .pRasterizationState = &rs,
        .pMultisampleState = &ms,
        .pColorBlendState = &cb,
        .pDynamicState = dyn_sc ? &dyn_ci : NULL,
        .layout = pl,
        .renderPass = rp,
        .subpass = 0,
    };
    VkPipeline pipe;
    r = vkCreateGraphicsPipelines(dev, VK_NULL_HANDLE, 1, &gpci, NULL, &pipe);
    die("vkCreateGraphicsPipelines", r);

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
    VkCommandBuffer cmd;
    r = vkAllocateCommandBuffers(dev, &cbai, &cmd);
    die("vkAllocateCommandBuffers", r);

    VkCommandBufferBeginInfo bi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
    };
    vkBeginCommandBuffer(cmd, &bi);

    VkClearValue clear;
    clear.color.float32[0] = 0.0f;
    clear.color.float32[1] = 0.0f;
    clear.color.float32[2] = 1.0f;
    clear.color.float32[3] = 1.0f;
    VkRenderPassBeginInfo rbi = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
        .renderPass = rp,
        .framebuffer = fb,
        .renderArea = { { 0, 0 }, { W, H } },
        .clearValueCount = 1,
        .pClearValues = &clear,
    };
    vkCmdBeginRenderPass(cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe);
    if (dyn_sc) {
        vkCmdSetViewport(cmd, 0, 1, &vp);
        vkCmdSetScissor(cmd, 0, 1, &sc);
    }
    {
        int ndraws = getenv("VK_GEOM_DRAWS") ? atoi(getenv("VK_GEOM_DRAWS")) : 1;

        if (ndraws < 1)
            ndraws = 1;
        for (int d = 0; d < (getenv("VK_GEOM_NODRAW") ? 0 : ndraws); d++)
            vkCmdDraw(cmd, 3, 1, 0, 0);
    }
    vkCmdEndRenderPass(cmd);

    VkImageMemoryBarrier host_barrier = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .oldLayout = VK_IMAGE_LAYOUT_GENERAL,
        .newLayout = VK_IMAGE_LAYOUT_GENERAL,
        .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .image = image,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
        .srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
        .dstAccessMask = VK_ACCESS_HOST_READ_BIT,
    };
    vkCmdPipelineBarrier(cmd,
                         VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT,
                         0, 0, NULL, 0, NULL, 1, &host_barrier);

    r = vkEndCommandBuffer(cmd);
    die("vkEndCommandBuffer", r);

    VkSubmitInfo si = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1,
        .pCommandBuffers = &cmd,
    };
    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);

    if (getenv("VK_GEOM_LOOP")) {
        int loop = atoi(getenv("VK_GEOM_LOOP"));
        struct timespec a, b;
        double tot = 0.0;
        for (int k = 0; k < loop; k++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
            if (r != VK_SUCCESS) {
                fprintf(stderr, "loop submit %d\n", r);
                break;
            }
            r = vkQueueWaitIdle(q);
            clock_gettime(CLOCK_MONOTONIC, &b);
            if (r != VK_SUCCESS) {
                fprintf(stderr, "loop wait %d\n", r);
                break;
            }
            tot += (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("bench %dx%d: %d frames, %.2f ms/frame\n", W, H, loop,
               1000.0 * tot / loop);
    }

    if (tiled) {
        printf("tiled: readback skipped\n");
        return 0;
    }

    void *ptr = NULL;
    r = vkMapMemory(dev, mem, 0, VK_WHOLE_SIZE, 0, &ptr);
    die("vkMapMemory", r);

    const uint32_t green = 0xff00ff00u; /* RGBA 0,255,0,255 */
    const uint32_t blue = 0xffff0000u;  /* RGBA 0,0,255,255 */
    uint32_t *p = ptr;
    size_t words = (size_t)(mr.size / 4);
    uint32_t n_green = 0, n_blue = 0, nonzero = 0;
    for (size_t i = 0; i < words; i++) {
        if (p[i] == green) n_green++;
        if (p[i] == blue) n_blue++;
        if (p[i]) nonzero++;
    }
    printf("words=%zu nonzero=%u green=%u blue=%u\n",
           words, nonzero, n_green, n_blue);
    printf("center=%08x (0,0)=%08x (63,0)=%08x (0,63)=%08x (63,63)=%08x\n",
           p[(H / 2) * W + W / 2], p[0], p[W - 1],
           p[(H - 1) * W], p[(H - 1) * W + W - 1]);

    {
        int minx = W, maxx = -1, miny = H, maxy = -1;
        for (int y = 0; y < H; y++) {
            for (int x = 0; x < W; x++) {
                if (!p[y * W + x])
                    continue;
                if (x < minx) minx = x;
                if (x > maxx) maxx = x;
                if (y < miny) miny = y;
                if (y > maxy) maxy = y;
            }
        }
        printf("bbox x=%d..%d y=%d..%d\n", minx, maxx, miny, maxy);
        fprintf(stderr, "map:\n");
        for (int y = 0; y < H; y++) {
            char line[W + 1];
            for (int x = 0; x < W; x++) {
                uint32_t v = p[y * W + x];
                line[x] = (v == green) ? '#' : (v == blue ? '.' : (v ? '+' : ' '));
            }
            line[W] = 0;
            fprintf(stderr, "|%s|\n", line);
        }
    }

    vkUnmapMemory(dev, mem);
    return n_green ? 0 : 2;
}
