/* vk_ds - depth test + blending probe for the Mesa PowerVR driver.
 *
 * 64x64 color (R8G8B8A8) + D16_UNORM depth, both linear / host visible.
 *
 * Pass 1 (depth test):
 *   - clear color to blue, depth to 1.0
 *   - draw the NEAR green quad (z=0.1, central half) first
 *   - then draw the FAR red quad (z=0.9, full screen)
 *   -> with a working LESS depth test the centre stays green and the border
 *      becomes red; the depth buffer should read ~0.1 in the centre.
 *
 * Pass 2 (blending):
 *   - clear color to blue (depth not attached)
 *   - draw a full screen (1,0,0,0.5) quad with src-alpha blending
 *   -> expected pixel ~ (0.5, 0, 0.5)
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

#include "ds_vert_spv.h"
#include "ds_frag_spv.h"

#define W 64
#define H 64

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
    die("vkCreateShaderModule", vkCreateShaderModule(dev, &ci, NULL, &m));
    return m;
}

static uint32_t find_host_mem(VkPhysicalDevice pd, uint32_t bits)
{
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++)
        if ((bits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags &
             VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) &&
            (mp.memoryTypes[i].propertyFlags &
             VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))
            return i;
    return 0;
}

static VkImage make_image(VkDevice dev, VkPhysicalDevice pd, uint32_t w,
                          uint32_t h, VkFormat fmt, VkImageUsageFlags usage,
                          VkDeviceMemory *mem_out, uint64_t *size_out)
{
    VkImageCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = fmt,
        .extent = { w, h, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = usage,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    VkImage img;
    die("vkCreateImage", vkCreateImage(dev, &ci, NULL, &img));
    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(dev, img, &mr);
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_host_mem(pd, mr.memoryTypeBits),
    };
    die("vkAllocateMemory", vkAllocateMemory(dev, &mai, NULL, mem_out));
    die("vkBindImageMemory", vkBindImageMemory(dev, img, *mem_out, 0));
    *size_out = mr.size;
    return img;
}

int main(void)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_ds",
        .apiVersion = VK_API_VERSION_1_0,
    };
    VkInstanceCreateInfo ici = {
        .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &app,
    };
    VkInstance inst;
    die("vkCreateInstance", vkCreateInstance(&ici, NULL, &inst));

    uint32_t n = 0;
    vkEnumeratePhysicalDevices(inst, &n, NULL);
    if (!n) {
        fprintf(stderr, "no device\n");
        return 1;
    }
    VkPhysicalDevice *pds = calloc(n, sizeof(*pds));
    vkEnumeratePhysicalDevices(inst, &n, pds);
    VkPhysicalDevice pd = pds[0];

    uint32_t qn = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(pd, &qn, NULL);
    VkQueueFamilyProperties *qf = calloc(qn, sizeof(*qf));
    vkGetPhysicalDeviceQueueFamilyProperties(pd, &qn, qf);
    uint32_t qi = 0;
    for (uint32_t i = 0; i < qn; i++)
        if (qf[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) {
            qi = i;
            break;
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
    die("vkCreateDevice", vkCreateDevice(pd, &dci, NULL, &dev));
    VkQueue q;
    vkGetDeviceQueue(dev, qi, 0, &q);

    VkDeviceMemory cmem, dmem;
    uint64_t csize, dsize;
    VkImage color = make_image(dev, pd, W, H, VK_FORMAT_R8G8B8A8_UNORM,
                               VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                                   VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                               &cmem, &csize);
    const int depth32 = getenv("VK_DS_D32") != NULL;
    const VkFormat depth_fmt = depth32 ? VK_FORMAT_D32_SFLOAT
                                       : VK_FORMAT_D16_UNORM;
    VkImage depth = make_image(dev, pd, W, H, depth_fmt,
                               VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT |
                                   VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                               &dmem, &dsize);
    fprintf(stderr, "color size=%llu depth size=%llu\n",
            (unsigned long long)csize, (unsigned long long)dsize);

    VkDeviceMemory cmem2;
    uint64_t csize2;
    VkImage color2 = make_image(dev, pd, W, H, VK_FORMAT_R8G8B8A8_UNORM,
                                VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                                    VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                                &cmem2, &csize2);

    VkImageViewCreateInfo cvci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = color,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    VkImageView cview;
    die("vkCreateImageView(color)", vkCreateImageView(dev, &cvci, NULL, &cview));
    VkImageViewCreateInfo cvci2 = cvci;
    cvci2.image = color2;
    VkImageView cview2;
    die("vkCreateImageView(color2)", vkCreateImageView(dev, &cvci2, NULL, &cview2));

    VkImageViewCreateInfo dvci = cvci;
    dvci.image = depth;
    dvci.format = depth_fmt;
    dvci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    VkImageView dview;
    die("vkCreateImageView(depth)", vkCreateImageView(dev, &dvci, NULL, &dview));

    /* ---- render pass 1: color + depth ---- */
    VkAttachmentDescription att1[2] = {
        { .format = VK_FORMAT_R8G8B8A8_UNORM,
          .samples = VK_SAMPLE_COUNT_1_BIT,
          .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
          .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
          .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
          .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
          .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
          .finalLayout = VK_IMAGE_LAYOUT_GENERAL },
        { .format = depth_fmt,
          .samples = VK_SAMPLE_COUNT_1_BIT,
          .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
          .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
          .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
          .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
          .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
          .finalLayout = VK_IMAGE_LAYOUT_GENERAL },
    };
    VkAttachmentReference cref = { 0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL };
    VkAttachmentReference dref = { 1, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL };
    VkSubpassDescription sp1 = {
        .pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
        .colorAttachmentCount = 1,
        .pColorAttachments = &cref,
        .pDepthStencilAttachment = &dref,
    };
    VkRenderPassCreateInfo rpci1 = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
        .attachmentCount = 2,
        .pAttachments = att1,
        .subpassCount = 1,
        .pSubpasses = &sp1,
    };
    VkRenderPass rp1;
    die("vkCreateRenderPass(1)", vkCreateRenderPass(dev, &rpci1, NULL, &rp1));

    /* ---- render pass 2: color only ---- */
    VkAttachmentDescription att2 = {
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
        .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
        .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        .initialLayout = VK_IMAGE_LAYOUT_GENERAL,
        .finalLayout = VK_IMAGE_LAYOUT_GENERAL,
    };
    VkAttachmentReference cref2 = { 0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL };
    VkSubpassDescription sp2 = {
        .pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
        .colorAttachmentCount = 1,
        .pColorAttachments = &cref2,
    };
    VkRenderPassCreateInfo rpci2 = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
        .attachmentCount = 1,
        .pAttachments = &att2,
        .subpassCount = 1,
        .pSubpasses = &sp2,
    };
    VkRenderPass rp2;
    die("vkCreateRenderPass(2)", vkCreateRenderPass(dev, &rpci2, NULL, &rp2));

    VkFramebufferCreateInfo fbci = {
        .sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
        .renderPass = rp1,
        .attachmentCount = 2,
        .pAttachments = (VkImageView[]){ cview, dview },
        .width = W,
        .height = H,
        .layers = 1,
    };
    VkFramebuffer fb1;
    die("vkCreateFramebuffer(1)", vkCreateFramebuffer(dev, &fbci, NULL, &fb1));
    fbci.renderPass = rp2;
    fbci.attachmentCount = 1;
    fbci.pAttachments = &cview2;
    VkFramebuffer fb2;
    die("vkCreateFramebuffer(2)", vkCreateFramebuffer(dev, &fbci, NULL, &fb2));

    VkShaderModule vs = make_shader(dev, ds_vert_spv, ds_vert_spv_len);
    VkShaderModule fs = make_shader(dev, ds_frag_spv, ds_frag_spv_len);
    VkPipelineShaderStageCreateInfo stages[2] = {
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_VERTEX_BIT, .module = vs, .pName = "main" },
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_FRAGMENT_BIT, .module = fs, .pName = "main" },
    };
    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 7 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[2] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32B32_SFLOAT, .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32B32A32_SFLOAT,
          .offset = 3 * sizeof(float) },
    };
    VkPipelineVertexInputStateCreateInfo vi = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
        .vertexBindingDescriptionCount = 1,
        .pVertexBindingDescriptions = &vib,
        .vertexAttributeDescriptionCount = 2,
        .pVertexAttributeDescriptions = via,
    };
    VkPipelineInputAssemblyStateCreateInfo ia = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
        .topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    };
    VkViewport vp = { 0, 0, W, H, 0, 1 };
    VkRect2D sc = { { 0, 0 }, { W, H } };
    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1, .pViewports = &vp,
        .scissorCount = 1, .pScissors = &sc,
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
    VkPipelineDepthStencilStateCreateInfo dss_on = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO,
        .depthTestEnable = VK_TRUE,
        .depthWriteEnable = VK_TRUE,
        .depthCompareOp = VK_COMPARE_OP_LESS,
    };
    VkPipelineDepthStencilStateCreateInfo dss_off = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO,
        .depthTestEnable = VK_FALSE,
    };
    VkPipelineColorBlendAttachmentState cba_opaque = {
        .blendEnable = VK_FALSE,
        .colorWriteMask = 0xf,
    };
    VkPipelineColorBlendAttachmentState cba_blend = {
        .blendEnable = VK_TRUE,
        .srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA,
        .dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        .colorBlendOp = VK_BLEND_OP_ADD,
        .srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE,
        .dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        .alphaBlendOp = VK_BLEND_OP_ADD,
        .colorWriteMask = 0xf,
    };
    VkPipelineColorBlendStateCreateInfo cb_opaque = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        .attachmentCount = 1, .pAttachments = &cba_opaque,
    };
    VkPipelineColorBlendStateCreateInfo cb_blend = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        .attachmentCount = 1, .pAttachments = &cba_blend,
    };
    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
    };
    VkPipelineLayout pl;
    die("vkCreatePipelineLayout", vkCreatePipelineLayout(dev, &plci, NULL, &pl));

    VkGraphicsPipelineCreateInfo gpci = {
        .sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
        .stageCount = 2, .pStages = stages,
        .pVertexInputState = &vi,
        .pInputAssemblyState = &ia,
        .pViewportState = &vps,
        .pRasterizationState = &rs,
        .pMultisampleState = &ms,
        .pDepthStencilState = &dss_on,
        .pColorBlendState = &cb_opaque,
        .layout = pl, .renderPass = rp1, .subpass = 0,
    };
    VkPipeline pipe_depth;
    die("vkCreateGraphicsPipelines(depth)",
        vkCreateGraphicsPipelines(dev, VK_NULL_HANDLE, 1, &gpci, NULL,
                                  &pipe_depth));
    gpci.pDepthStencilState = &dss_off;
    gpci.pColorBlendState = &cb_blend;
    gpci.renderPass = rp2;
    VkPipeline pipe_blend;
    die("vkCreateGraphicsPipelines(blend)",
        vkCreateGraphicsPipelines(dev, VK_NULL_HANDLE, 1, &gpci, NULL,
                                  &pipe_blend));

    /* 12 vertices: near green quad (6) + far red quad (6) */
    float verts[18][7] = {
        { -0.5f, -0.5f, 0.1f, 0, 1, 0, 1 },
        {  0.5f, -0.5f, 0.1f, 0, 1, 0, 1 },
        { -0.5f,  0.5f, 0.1f, 0, 1, 0, 1 },
        {  0.5f, -0.5f, 0.1f, 0, 1, 0, 1 },
        {  0.5f,  0.5f, 0.1f, 0, 1, 0, 1 },
        { -0.5f,  0.5f, 0.1f, 0, 1, 0, 1 },
        { -1.0f, -1.0f, 0.9f, 1, 0, 0, 1 },
        {  1.0f, -1.0f, 0.9f, 1, 0, 0, 1 },
        { -1.0f,  1.0f, 0.9f, 1, 0, 0, 1 },
        {  1.0f, -1.0f, 0.9f, 1, 0, 0, 1 },
        {  1.0f,  1.0f, 0.9f, 1, 0, 0, 1 },
        { -1.0f,  1.0f, 0.9f, 1, 0, 0, 1 },
        /* blend quad: red, alpha 0.5 */
        { -1.0f, -1.0f, 0.0f, 1, 0, 0, 0.5f },
        {  1.0f, -1.0f, 0.0f, 1, 0, 0, 0.5f },
        { -1.0f,  1.0f, 0.0f, 1, 0, 0, 0.5f },
        {  1.0f, -1.0f, 0.0f, 1, 0, 0, 0.5f },
        {  1.0f,  1.0f, 0.0f, 1, 0, 0, 0.5f },
        { -1.0f,  1.0f, 0.0f, 1, 0, 0, 0.5f },
    };
    VkBufferCreateInfo bci = {
        .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .size = sizeof(verts),
        .usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
    };
    VkBuffer vbo;
    die("vkCreateBuffer", vkCreateBuffer(dev, &bci, NULL, &vbo));
    VkMemoryRequirements vmr;
    vkGetBufferMemoryRequirements(dev, vbo, &vmr);
    VkMemoryAllocateInfo vma = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = vmr.size,
        .memoryTypeIndex = find_host_mem(pd, vmr.memoryTypeBits),
    };
    VkDeviceMemory vbomem;
    die("vkAllocateMemory(vbo)", vkAllocateMemory(dev, &vma, NULL, &vbomem));
    die("vkBindBufferMemory", vkBindBufferMemory(dev, vbo, vbomem, 0));
    void *vptr = NULL;
    die("vkMapMemory(vbo)", vkMapMemory(dev, vbomem, 0, VK_WHOLE_SIZE, 0, &vptr));
    memcpy(vptr, verts, sizeof(verts));
    vkUnmapMemory(dev, vbomem);

    VkCommandPoolCreateInfo pci = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = qi,
    };
    VkCommandPool pool;
    die("vkCreateCommandPool", vkCreateCommandPool(dev, &pci, NULL, &pool));
    VkCommandBufferAllocateInfo cbai = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = pool,
        .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        .commandBufferCount = 1,
    };
    VkCommandBuffer cb;
    die("vkAllocateCommandBuffers", vkAllocateCommandBuffers(dev, &cbai, &cb));
    VkCommandBufferBeginInfo bi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
    };
    vkBeginCommandBuffer(cb, &bi);

    VkClearValue clears[2] = {
        { .color = { { 0.0f, 0.0f, 1.0f, 1.0f } } },
        { .depthStencil = { 1.0f, 0 } },
    };
    VkRenderPassBeginInfo rbi = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
        .renderPass = rp1,
        .framebuffer = fb1,
        .renderArea = { { 0, 0 }, { W, H } },
        .clearValueCount = 2,
        .pClearValues = clears,
    };
    vkCmdBeginRenderPass(cb, &rbi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe_depth);
    VkDeviceSize off = 0;
    vkCmdBindVertexBuffers(cb, 0, 1, &vbo, &off);
    vkCmdDraw(cb, 6, 1, 0, 0);  /* near, green */
    vkCmdDraw(cb, 6, 1, 6, 0);  /* far, red (must be depth rejected) */
    vkCmdEndRenderPass(cb);

    /* Pass 2: blending over a fresh blue clear. */
    VkClearValue clear_blue = { .color = { { 0.0f, 0.0f, 1.0f, 1.0f } } };
    VkRenderPassBeginInfo rbi2 = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
        .renderPass = rp2,
        .framebuffer = fb2,
        .renderArea = { { 0, 0 }, { W, H } },
        .clearValueCount = 1,
        .pClearValues = &clear_blue,
    };
    vkCmdBeginRenderPass(cb, &rbi2, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe_blend);
    vkCmdBindVertexBuffers(cb, 0, 1, &vbo, &off);
    vkCmdDraw(cb, 6, 1, 12, 0);  /* red, alpha 0.5, over blue */
    vkCmdEndRenderPass(cb);

    VkImageMemoryBarrier hb = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .oldLayout = VK_IMAGE_LAYOUT_GENERAL,
        .newLayout = VK_IMAGE_LAYOUT_GENERAL,
        .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .image = color,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
        .srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
        .dstAccessMask = VK_ACCESS_HOST_READ_BIT,
    };
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT, 0, 0, NULL, 0, NULL, 1,
                         &hb);
    die("vkEndCommandBuffer", vkEndCommandBuffer(cb));

    VkSubmitInfo si = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1,
        .pCommandBuffers = &cb,
    };
    die("vkQueueSubmit", vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE));
    die("vkQueueWaitIdle", vkQueueWaitIdle(q));

    void *cptr = NULL, *dptr = NULL;
    die("map color", vkMapMemory(dev, cmem, 0, VK_WHOLE_SIZE, 0, &cptr));
    die("map depth", vkMapMemory(dev, dmem, 0, VK_WHOLE_SIZE, 0, &dptr));
    uint32_t *p = cptr;
    uint16_t *d = dptr;
    uint32_t red = 0, green = 0, blue = 0, other = 0;
    for (size_t i = 0; i < (size_t)(csize / 4); i++) {
        if (p[i] == 0xff0000ffu) red++;
        else if (p[i] == 0xff00ff00u) green++;
        else if (p[i] == 0xffff0000u) blue++;
        else other++;
    }
    printf("color: red=%u green=%u blue=%u other=%u\n", red, green, blue, other);
    printf("center=%08x corner=%08x\n", p[(H / 2) * W + W / 2], p[0]);
    if (depth32) {
        const float *df = (const float *)d;

        printf("depth32: center=%.4f corner=%.4f (expect ~0.1 / ~0.9)\n",
               df[(H / 2) * W + W / 2], df[0]);
    } else {
        printf("depth: center=%u corner=%u (D16 raw)\n",
               d[(H / 2) * W + W / 2], d[0]);
    }

    void *c2ptr = NULL;
    die("map color2", vkMapMemory(dev, cmem2, 0, VK_WHOLE_SIZE, 0, &c2ptr));
    {
        uint32_t *p2 = c2ptr;
        printf("blend: center=%08x corner=%08x (expect ~80007f80)\n",
               p2[(H / 2) * W + W / 2], p2[0]);
        vkUnmapMemory(dev, cmem2);
    }

    vkUnmapMemory(dev, cmem);
    vkUnmapMemory(dev, dmem);
    return (green && red) ? 0 : 2;
}
