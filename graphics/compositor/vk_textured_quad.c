/* Vulkan textured quad: 2x2 RGBA texture, sampler, descriptor set, 6 vertices. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

#include "quad_vert_spv.h"
#include "quad_frag_spv.h"

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
    VkResult r = vkCreateShaderModule(dev, &ci, NULL, &m);
    die("vkCreateShaderModule", r);
    return m;
}

static uint32_t find_host_mem(VkPhysicalDevice pd, uint32_t bits)
{
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
        if ((bits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) &&
            (mp.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))
            return i;
    }
    return 0;
}

int main(void)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_textured_quad",
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

    /* Render target */
    VkImageCreateInfo rtci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .extent = { W, H, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                 VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    VkImage rt;
    r = vkCreateImage(dev, &rtci, NULL, &rt);
    die("vkCreateImage(rt)", r);
    VkMemoryRequirements rtmr;
    vkGetImageMemoryRequirements(dev, rt, &rtmr);
    VkMemoryAllocateInfo rtma = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = rtmr.size,
        .memoryTypeIndex = find_host_mem(pd, rtmr.memoryTypeBits),
    };
    VkDeviceMemory rtmem;
    r = vkAllocateMemory(dev, &rtma, NULL, &rtmem);
    die("vkAllocateMemory(rt)", r);
    r = vkBindImageMemory(dev, rt, rtmem, 0);
    die("vkBindImageMemory(rt)", r);
    VkImageViewCreateInfo rtvi = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = rt,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    VkImageView rtview;
    r = vkCreateImageView(dev, &rtvi, NULL, &rtview);
    die("vkCreateImageView(rt)", r);

    /* 2x2 texture */
    VkImageCreateInfo tci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .extent = { 2, 2, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_SAMPLED_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    VkImage tex;
    r = vkCreateImage(dev, &tci, NULL, &tex);
    die("vkCreateImage(tex)", r);
    VkMemoryRequirements tmr;
    vkGetImageMemoryRequirements(dev, tex, &tmr);
    VkMemoryAllocateInfo tma = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = tmr.size,
        .memoryTypeIndex = find_host_mem(pd, tmr.memoryTypeBits),
    };
    VkDeviceMemory texmem;
    r = vkAllocateMemory(dev, &tma, NULL, &texmem);
    die("vkAllocateMemory(tex)", r);
    r = vkBindImageMemory(dev, tex, texmem, 0);
    die("vkBindImageMemory(tex)", r);
    void *texptr = NULL;
    r = vkMapMemory(dev, texmem, 0, VK_WHOLE_SIZE, 0, &texptr);
    die("vkMapMemory(tex)", r);
    {
        uint32_t px[4] = {
            0xff0000ffu, /* (0,0) red */
            0xff00ff00u, /* (1,0) green */
            0xffff0000u, /* (0,1) blue */
            0xff00ffffu, /* (1,1) yellow */
        };
        memcpy(texptr, px, sizeof(px));
    }
    vkUnmapMemory(dev, texmem);
    VkImageViewCreateInfo tvi = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = tex,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    VkImageView texview;
    r = vkCreateImageView(dev, &tvi, NULL, &texview);
    die("vkCreateImageView(tex)", r);
    VkSamplerCreateInfo sci = {
        .sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
        .magFilter = VK_FILTER_NEAREST,
        .minFilter = VK_FILTER_NEAREST,
        .mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST,
        .addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        .addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        .addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        .maxLod = 0.0f,
    };
    VkSampler sampler;
    r = vkCreateSampler(dev, &sci, NULL, &sampler);
    die("vkCreateSampler", r);

    /* Render pass */
    VkAttachmentDescription att = {
        .format = VK_FORMAT_R8G8B8A8_UNORM,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
        .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
        .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .finalLayout = VK_IMAGE_LAYOUT_GENERAL,
    };
    VkAttachmentReference ref = { 0, VK_IMAGE_LAYOUT_GENERAL };
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
        .pAttachments = &rtview,
        .width = W,
        .height = H,
        .layers = 1,
    };
    VkFramebuffer fb;
    r = vkCreateFramebuffer(dev, &fbci, NULL, &fb);
    die("vkCreateFramebuffer", r);

    /* Descriptor set */
    VkDescriptorSetLayoutBinding dslb = {
        .binding = 0,
        .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .descriptorCount = 1,
        .stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT,
    };
    VkDescriptorSetLayoutCreateInfo dslci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
        .bindingCount = 1,
        .pBindings = &dslb,
    };
    VkDescriptorSetLayout dsl;
    r = vkCreateDescriptorSetLayout(dev, &dslci, NULL, &dsl);
    die("vkCreateDescriptorSetLayout", r);
    VkDescriptorPoolSize dps = {
        .type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .descriptorCount = 1,
    };
    VkDescriptorPoolCreateInfo dpci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        .maxSets = 1,
        .poolSizeCount = 1,
        .pPoolSizes = &dps,
    };
    VkDescriptorPool dp;
    r = vkCreateDescriptorPool(dev, &dpci, NULL, &dp);
    die("vkCreateDescriptorPool", r);
    VkDescriptorSetAllocateInfo dsai = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        .descriptorPool = dp,
        .descriptorSetCount = 1,
        .pSetLayouts = &dsl,
    };
    VkDescriptorSet ds;
    r = vkAllocateDescriptorSets(dev, &dsai, &ds);
    die("vkAllocateDescriptorSets", r);
    VkDescriptorImageInfo dii = {
        .sampler = sampler,
        .imageView = texview,
        .imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
    };
    VkWriteDescriptorSet wds = {
        .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
        .dstSet = ds,
        .dstBinding = 0,
        .descriptorCount = 1,
        .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .pImageInfo = &dii,
    };
    vkUpdateDescriptorSets(dev, 1, &wds, 0, NULL);

    /* Shaders/pipeline */
    VkShaderModule vs = make_shader(dev, quad_vert_spv, quad_vert_spv_len);
    VkShaderModule fs = make_shader(dev, quad_frag_spv, quad_frag_spv_len);
    VkPipelineShaderStageCreateInfo stages[2] = {
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_VERTEX_BIT, .module = vs, .pName = "main" },
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_FRAGMENT_BIT, .module = fs, .pName = "main" },
    };
    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 4 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[2] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32_SFLOAT,
          .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32_SFLOAT,
          .offset = 2 * sizeof(float) },
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
    VkPipelineColorBlendAttachmentState cba = {
        .blendEnable = VK_FALSE,
        .colorWriteMask = 0xf,
    };
    VkPipelineColorBlendStateCreateInfo cb = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        .attachmentCount = 1, .pAttachments = &cba,
    };
    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
        .setLayoutCount = 1, .pSetLayouts = &dsl,
    };
    VkPipelineLayout pl;
    r = vkCreatePipelineLayout(dev, &plci, NULL, &pl);
    die("vkCreatePipelineLayout", r);
    VkGraphicsPipelineCreateInfo gpci = {
        .sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
        .stageCount = 2, .pStages = stages,
        .pVertexInputState = &vi,
        .pInputAssemblyState = &ia,
        .pViewportState = &vps,
        .pRasterizationState = &rs,
        .pMultisampleState = &ms,
        .pColorBlendState = &cb,
        .layout = pl, .renderPass = rp, .subpass = 0,
    };
    VkPipeline pipe;
    r = vkCreateGraphicsPipelines(dev, VK_NULL_HANDLE, 1, &gpci, NULL, &pipe);
    die("vkCreateGraphicsPipelines", r);

    /* Vertex buffer */
    float verts[] = {
        -1, -1, 0, 1,
         1, -1, 1, 1,
        -1,  1, 0, 0,
        -1,  1, 0, 0,
         1, -1, 1, 1,
         1,  1, 1, 0,
    };
    VkBufferCreateInfo bci = {
        .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .size = sizeof(verts),
        .usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
    };
    VkBuffer vbo;
    r = vkCreateBuffer(dev, &bci, NULL, &vbo);
    die("vkCreateBuffer", r);
    VkMemoryRequirements vmr;
    vkGetBufferMemoryRequirements(dev, vbo, &vmr);
    VkMemoryAllocateInfo vma = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = vmr.size,
        .memoryTypeIndex = find_host_mem(pd, vmr.memoryTypeBits),
    };
    VkDeviceMemory vbomem;
    r = vkAllocateMemory(dev, &vma, NULL, &vbomem);
    die("vkAllocateMemory(vbo)", r);
    r = vkBindBufferMemory(dev, vbo, vbomem, 0);
    die("vkBindBufferMemory", r);
    void *vboptr = NULL;
    r = vkMapMemory(dev, vbomem, 0, VK_WHOLE_SIZE, 0, &vboptr);
    die("vkMapMemory(vbo)", r);
    memcpy(vboptr, verts, sizeof(verts));
    vkUnmapMemory(dev, vbomem);

    /* Command buffer */
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

    VkImageMemoryBarrier tb = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .image = tex,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
        .srcAccessMask = 0,
        .dstAccessMask = VK_ACCESS_SHADER_READ_BIT,
    };
    vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                         VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, 0,
                         0, NULL, 0, NULL, 1, &tb);

    VkClearValue clear;
    clear.color.float32[0] = 0.0f;
    clear.color.float32[1] = 0.0f;
    clear.color.float32[2] = 1.0f;
    clear.color.float32[3] = 1.0f;
    VkRenderPassBeginInfo rbi = {
        .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
        .renderPass = rp, .framebuffer = fb,
        .renderArea = { { 0, 0 }, { W, H } },
        .clearValueCount = 1, .pClearValues = &clear,
    };
    vkCmdBeginRenderPass(cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pl,
                            0, 1, &ds, 0, NULL);
    VkDeviceSize off = 0;
    vkCmdBindVertexBuffers(cmd, 0, 1, &vbo, &off);
    vkCmdDraw(cmd, 6, 1, 0, 0);
    vkCmdEndRenderPass(cmd);

    VkImageMemoryBarrier hb = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        .oldLayout = VK_IMAGE_LAYOUT_GENERAL,
        .newLayout = VK_IMAGE_LAYOUT_GENERAL,
        .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .image = rt,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
        .srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
        .dstAccessMask = VK_ACCESS_HOST_READ_BIT,
    };
    vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                         VK_PIPELINE_STAGE_HOST_BIT, 0,
                         0, NULL, 0, NULL, 1, &hb);

    r = vkEndCommandBuffer(cmd);
    die("vkEndCommandBuffer", r);
    VkSubmitInfo si = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1, .pCommandBuffers = &cmd,
    };
    r = vkQueueSubmit(q, 1, &si, VK_NULL_HANDLE);
    die("vkQueueSubmit", r);
    r = vkQueueWaitIdle(q);
    die("vkQueueWaitIdle", r);

    void *ptr = NULL;
    r = vkMapMemory(dev, rtmem, 0, VK_WHOLE_SIZE, 0, &ptr);
    die("vkMapMemory(rt)", r);
    uint32_t *p = ptr;
    size_t words = (size_t)(rtmr.size / 4);
    uint32_t red = 0, green = 0, blue = 0, yellow = 0, nonzero = 0;
    for (size_t i = 0; i < words; i++) {
        if (p[i]) nonzero++;
        if (p[i] == 0xff0000ffu) red++;
        else if (p[i] == 0xff00ff00u) green++;
        else if (p[i] == 0xffff0000u) blue++;
        else if (p[i] == 0xff00ffffu) yellow++;
    }
    printf("words=%zu nonzero=%u red=%u green=%u blue=%u yellow=%u\n",
           words, nonzero, red, green, blue, yellow);
    printf("(0,0)=%08x (31,0)=%08x (0,31)=%08x (31,31)=%08x\n",
           p[0], p[31], p[31 * W], p[31 * W + 31]);
    vkUnmapMemory(dev, rtmem);
    return (red || green || yellow) ? 0 : 2;
}
