/* vk_kms2 - zero-copy Vulkan -> DRM/KMS presenter.
 *
 * The MTK display driver only accepts *physically contiguous* dma-bufs
 * (drm_gem_dma_prime_import_sg_table), so instead of exporting the Vulkan
 * image we go the other way round: allocate contiguous scanout buffers with
 * DRM dumb buffers, export them as dma-bufs and import those into Vulkan
 * (VK_KHR_external_memory_fd). Vulkan then renders straight into the buffer
 * that is being scanned out.
 *
 * If the import fails, it falls back to a PVR image + CPU copy (still shows
 * the same scene, just slower).
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include <linux/input.h>

#include <drm_fourcc.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

#include <vulkan/vulkan.h>

#include "comp_vert_spv.h"
#include "comp_frag_spv.h"

#include <sys/resource.h>

#include "wl/wl_backend.h"

#ifndef NSLOT
#define NSLOT 3
#endif

#define MAX_LAYERS 16

#define CHECK_VK(x)                                                          \
    do {                                                                     \
        VkResult r_ = (x);                                                   \
        if (r_ != VK_SUCCESS) {                                              \
            fprintf(stderr, "%s -> VkResult %d\n", #x, r_);                  \
            exit(1);                                                         \
        }                                                                    \
    } while (0)

#define CHECK_DRM(x)                                                         \
    do {                                                                     \
        int r_ = (x);                                                        \
        if (r_ < 0) {                                                        \
            fprintf(stderr, "%s -> %d (%s)\n", #x, r_, strerror(errno));     \
            exit(1);                                                         \
        }                                                                    \
    } while (0)

/* ------------------------------------------------------------------ DRM */

struct drm_state {
    int fd;
    drmModeRes *res;
    drmModeConnector *conn;
    drmModeEncoder *enc;
    drmModeCrtc *orig_crtc;
    drmModeModeInfo mode;
    uint32_t crtc_id;
    uint32_t conn_id;
};

static volatile int g_flip_done;

static void flip_handler(int fd, unsigned seq, unsigned sec, unsigned usec,
                         void *data)
{
    (void)fd;
    (void)seq;
    (void)sec;
    (void)usec;
    (void)data;
    g_flip_done = 1;
}

static int wait_flip(int fd)
{
    while (!g_flip_done) {
        drmEventContext ev = {
            .version = 2,
            .page_flip_handler = flip_handler,
        };
        int r = drmHandleEvent(fd, &ev);
        if (r < 0) {
            fprintf(stderr, "drmHandleEvent: %s\n", strerror(errno));
            return -1;
        }
    }
    return 0;
}

static int drm_find_output(struct drm_state *d)
{
    uint32_t i;

    d->res = drmModeGetResources(d->fd);
    if (!d->res) {
        fprintf(stderr, "drmModeGetResources failed\n");
        return -1;
    }

    for (i = 0; i < (uint32_t)d->res->count_connectors; i++) {
        drmModeConnector *c = drmModeGetConnector(d->fd, d->res->connectors[i]);
        if (!c)
            continue;
        if (c->connection == DRM_MODE_CONNECTED && c->count_modes > 0) {
            d->conn = c;
            d->conn_id = c->connector_id;
            break;
        }
        drmModeFreeConnector(c);
    }
    if (!d->conn) {
        fprintf(stderr, "no connected connector with modes\n");
        return -1;
    }

    d->mode = d->conn->modes[0];
    for (i = 0; i < (uint32_t)d->conn->count_modes; i++) {
        if (d->conn->modes[i].type & DRM_MODE_TYPE_PREFERRED) {
            d->mode = d->conn->modes[i];
            break;
        }
    }

    if (d->conn->encoder_id)
        d->enc = drmModeGetEncoder(d->fd, d->conn->encoder_id);
    if (!d->enc && d->conn->count_encoders)
        d->enc = drmModeGetEncoder(d->fd, d->conn->encoders[0]);
    if (!d->enc) {
        fprintf(stderr, "no encoder for connector\n");
        return -1;
    }

    d->crtc_id = d->enc->crtc_id;
    if (!d->crtc_id && d->res->count_crtcs)
        d->crtc_id = d->res->crtcs[0];

    d->orig_crtc = drmModeGetCrtc(d->fd, d->crtc_id);

    printf("drm: connector %u mode \"%s\" %ux%u@%u crtc=%u\n", d->conn_id,
           d->mode.name, d->mode.hdisplay, d->mode.vdisplay, d->mode.vrefresh,
           d->crtc_id);
    return 0;
}

/* ----------------------------------------------------------------- Vulkan */

struct vk_state {
    VkInstance inst;
    VkPhysicalDevice pd;
    VkDevice dev;
    VkQueue queue;
    uint32_t qfam;
    VkCommandPool pool;
    VkCommandBuffer cmd;
    VkFence fence;

    VkShaderModule vs, fs;
    VkPipelineLayout layout;
    VkPipeline pipe;
    VkRenderPass rp;
    VkRenderPass rp_load;

    VkBuffer vbo;
    VkDeviceMemory vbo_mem;
    void *vbo_ptr;

    PFN_vkGetMemoryFdKHR get_memory_fd;
    PFN_vkGetMemoryFdPropertiesKHR get_fd_props;

    VkDescriptorSetLayout dsl;
    VkDescriptorPool dpool;
    VkSampler sampler;
#define NUM_TEX 4
    VkImage tex_img[NUM_TEX];
    VkDeviceMemory tex_mem[NUM_TEX];
    VkImageView tex_view[NUM_TEX];
    VkDescriptorSet tex_set[NUM_TEX];
};

struct frame {
    VkImage image;
    VkDeviceMemory mem;
    VkImageView view;
    VkFramebuffer fb;
    void *host;
    uint64_t size;
    uint64_t pitch;
    int dmabuf_fd;
    uint32_t drm_fb;
    uint32_t dumb_handle;
    uint32_t dumb_pitch;
    void *dumb_ptr;
};

static uint32_t find_mem_type(VkPhysicalDevice pd, uint32_t bits,
                              VkMemoryPropertyFlags want)
{
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++)
        if ((bits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & want) == want)
            return i;
    return UINT32_MAX;
}

static int ext_supported(VkPhysicalDevice pd, const char *name)
{
    uint32_t n = 0;
    if (vkEnumerateDeviceExtensionProperties(pd, NULL, &n, NULL) != VK_SUCCESS)
        return 0;
    VkExtensionProperties *ex = calloc(n, sizeof(*ex));
    vkEnumerateDeviceExtensionProperties(pd, NULL, &n, ex);
    int found = 0;
    for (uint32_t i = 0; i < n; i++)
        if (!strcmp(ex[i].extensionName, name))
            found = 1;
    free(ex);
    return found;
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
    CHECK_VK(vkCreateShaderModule(dev, &ci, NULL, &m));
    return m;
}

static void vk_init(struct vk_state *v, VkFormat fmt, uint32_t w, uint32_t h)
{
    VkApplicationInfo app = {
        .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName = "vk_kms",
        .apiVersion = VK_API_VERSION_1_0,
    };
    VkInstanceCreateInfo ici = {
        .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &app,
    };
    memset(v, 0, sizeof(*v));
    CHECK_VK(vkCreateInstance(&ici, NULL, &v->inst));

    uint32_t n = 0;
    CHECK_VK(vkEnumeratePhysicalDevices(v->inst, &n, NULL));
    if (!n) {
        fprintf(stderr, "no Vulkan device\n");
        exit(1);
    }
    VkPhysicalDevice *pds = calloc(n, sizeof(*pds));
    vkEnumeratePhysicalDevices(v->inst, &n, pds);
    v->pd = pds[0];
    free(pds);

    uint32_t qn = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(v->pd, &qn, NULL);
    VkQueueFamilyProperties *qf = calloc(qn, sizeof(*qf));
    vkGetPhysicalDeviceQueueFamilyProperties(v->pd, &qn, qf);
    for (uint32_t i = 0; i < qn; i++)
        if (qf[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) {
            v->qfam = i;
            break;
        }
    free(qf);

    const char *want[] = {
        "VK_KHR_external_memory",
        "VK_KHR_external_memory_fd",
        "VK_EXT_external_memory_dma_buf",
        "VK_KHR_dedicated_allocation",
        "VK_KHR_get_memory_requirements2",
        "VK_KHR_image_format_list",
        "VK_EXT_image_drm_format_modifier",
    };
    const char *enable[8];
    uint32_t n_enable = 0;
    for (uint32_t i = 0; i < sizeof(want) / sizeof(want[0]); i++)
        if (ext_supported(v->pd, want[i]))
            enable[n_enable++] = want[i];
    printf("vk: enabling %u device extensions\n", n_enable);

    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = v->qfam,
        .queueCount = 1,
        .pQueuePriorities = &prio,
    };
    VkDeviceCreateInfo dci = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
        .queueCreateInfoCount = 1,
        .pQueueCreateInfos = &qci,
        .enabledExtensionCount = n_enable,
        .ppEnabledExtensionNames = enable,
    };
    CHECK_VK(vkCreateDevice(v->pd, &dci, NULL, &v->dev));
    vkGetDeviceQueue(v->dev, v->qfam, 0, &v->queue);
    v->get_memory_fd = (PFN_vkGetMemoryFdKHR)vkGetDeviceProcAddr(
        v->dev, "vkGetMemoryFdKHR");
    v->get_fd_props = (PFN_vkGetMemoryFdPropertiesKHR)vkGetDeviceProcAddr(
        v->dev, "vkGetMemoryFdPropertiesKHR");

    VkCommandPoolCreateInfo pci = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        .queueFamilyIndex = v->qfam,
        .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    };
    CHECK_VK(vkCreateCommandPool(v->dev, &pci, NULL, &v->pool));
    VkCommandBufferAllocateInfo cbi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = v->pool,
        .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        .commandBufferCount = 1,
    };
    CHECK_VK(vkAllocateCommandBuffers(v->dev, &cbi, &v->cmd));
    VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    CHECK_VK(vkCreateFence(v->dev, &fci, NULL, &v->fence));

    v->vs = make_shader(v->dev, comp_vert_spv, comp_vert_spv_len);
    v->fs = make_shader(v->dev, comp_frag_spv, comp_frag_spv_len);

    VkAttachmentDescription att = {
        .format = fmt,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
        .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
        .stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        .stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        .finalLayout = VK_IMAGE_LAYOUT_GENERAL,
    };
    VkAttachmentReference ref = { 0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL };
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
    CHECK_VK(vkCreateRenderPass(v->dev, &rpci, NULL, &v->rp));
    /* Same pass, but preserve contents so a slot can be redrawn
     * partially (damage tracking). */
    att.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
    att.initialLayout = VK_IMAGE_LAYOUT_GENERAL;
    CHECK_VK(vkCreateRenderPass(v->dev, &rpci, NULL, &v->rp_load));

    VkPipelineShaderStageCreateInfo stages[2] = {
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_VERTEX_BIT, .module = v->vs,
          .pName = "main" },
        { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
          .stage = VK_SHADER_STAGE_FRAGMENT_BIT, .module = v->fs,
          .pName = "main" },
    };
    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 9 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[3] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32B32_SFLOAT,
          .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32_SFLOAT,
          .offset = 3 * sizeof(float) },
        { .location = 2, .binding = 0, .format = VK_FORMAT_R32G32B32A32_SFLOAT,
          .offset = 5 * sizeof(float) },
    };
    VkPipelineVertexInputStateCreateInfo vi = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
        .vertexBindingDescriptionCount = 1,
        .pVertexBindingDescriptions = &vib,
        .vertexAttributeDescriptionCount = 3,
        .pVertexAttributeDescriptions = via,
    };
    VkPipelineInputAssemblyStateCreateInfo ia = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
        .topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    };
    VkViewport static_vp = { 0, 0, (float)w, (float)h, 0, 1 };
    VkRect2D static_sc = { { 0, 0 }, { w, h } };
    VkPipelineViewportStateCreateInfo vps = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        .viewportCount = 1,
        .pViewports = &static_vp,
        .scissorCount = 1,
        .pScissors = &static_sc,
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
        .blendEnable = VK_TRUE,
        .srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA,
        .dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        .colorBlendOp = VK_BLEND_OP_ADD,
        .srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE,
        .dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        .alphaBlendOp = VK_BLEND_OP_ADD,
        .colorWriteMask = 0xf,
    };
    VkPipelineColorBlendStateCreateInfo cb = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        .attachmentCount = 1,
        .pAttachments = &cba,
    };
    VkDynamicState dyn[1] = { VK_DYNAMIC_STATE_SCISSOR };
    VkPipelineDynamicStateCreateInfo ds = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO,
        .dynamicStateCount = 1,
        .pDynamicStates = dyn,
    };
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
    CHECK_VK(vkCreateDescriptorSetLayout(v->dev, &dslci, NULL, &v->dsl));

    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
        .setLayoutCount = 1,
        .pSetLayouts = &v->dsl,
    };
    CHECK_VK(vkCreatePipelineLayout(v->dev, &plci, NULL, &v->layout));
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
        .pDynamicState = &ds,
        .layout = v->layout,
        .renderPass = v->rp,
        .subpass = 0,
    };
    CHECK_VK(vkCreateGraphicsPipelines(v->dev, VK_NULL_HANDLE, 1, &gpci, NULL,
                                       &v->pipe));

    VkBufferCreateInfo bci = {
        .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .size = MAX_LAYERS * 6 * 9 * sizeof(float),
        .usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    };
    CHECK_VK(vkCreateBuffer(v->dev, &bci, NULL, &v->vbo));
    VkMemoryRequirements mr;
    vkGetBufferMemoryRequirements(v->dev, v->vbo, &mr);
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(
            v->pd, mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT),
    };
    CHECK_VK(vkAllocateMemory(v->dev, &mai, NULL, &v->vbo_mem));
    CHECK_VK(vkBindBufferMemory(v->dev, v->vbo, v->vbo_mem, 0));
    CHECK_VK(vkMapMemory(v->dev, v->vbo_mem, 0, VK_WHOLE_SIZE, 0, &v->vbo_ptr));
}

static int frame_view_and_fb(struct vk_state *v, struct frame *f, uint32_t w,
                            uint32_t h, VkFormat fmt)
{
    VkImageViewCreateInfo vci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        .image = f->image,
        .viewType = VK_IMAGE_VIEW_TYPE_2D,
        .format = fmt,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
    };
    CHECK_VK(vkCreateImageView(v->dev, &vci, NULL, &f->view));

    VkFramebufferCreateInfo fbci = {
        .sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
        .renderPass = v->rp,
        .attachmentCount = 1,
        .pAttachments = &f->view,
        .width = w,
        .height = h,
        .layers = 1,
    };
    CHECK_VK(vkCreateFramebuffer(v->dev, &fbci, NULL, &f->fb));
    return 0;
}

static VkImageCreateInfo linear_image_ci(uint32_t w, uint32_t h, VkFormat fmt,
                                         const void *pnext)
{
    VkImageCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        .pNext = pnext,
        .imageType = VK_IMAGE_TYPE_2D,
        .format = fmt,
        .extent = { w, h, 1 },
        .mipLevels = 1,
        .arrayLayers = 1,
        .samples = VK_SAMPLE_COUNT_1_BIT,
        .tiling = VK_IMAGE_TILING_LINEAR,
        .usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                 VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
        .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
    };
    return ci;
}

/* Import a (contiguous) dma-buf as the render target. */
static int frame_init_import(struct vk_state *v, struct frame *f, uint32_t w,
                             uint32_t h, VkFormat fmt, int fd)
{
    f->dmabuf_fd = fd;

    VkExternalMemoryImageCreateInfo ext = {
        .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
        .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
    };
    VkImageCreateInfo ci = linear_image_ci(w, h, fmt, &ext);
    VkResult r = vkCreateImage(v->dev, &ci, NULL, &f->image);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "import: vkCreateImage -> %d\n", r);
        return -1;
    }

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(v->dev, f->image, &mr);

    uint32_t type_bits = mr.memoryTypeBits;
    if (v->get_fd_props) {
        VkMemoryFdPropertiesKHR fp = {
            .sType = VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR,
        };
        r = v->get_fd_props(v->dev,
                           VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd,
                           &fp);
        if (r != VK_SUCCESS) {
            fprintf(stderr, "import: vkGetMemoryFdPropertiesKHR -> %d\n", r);
            return -1;
        }
        type_bits &= fp.memoryTypeBits;
        if (!type_bits) {
            fprintf(stderr, "import: fd has no usable memory type\n");
            return -1;
        }
    }

    VkImportMemoryFdInfoKHR imp = {
        .sType = VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR,
        .handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT,
        .fd = fd,
    };
    VkMemoryDedicatedAllocateInfo ded = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
        .pNext = &imp,
        .image = f->image,
    };
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .pNext = &ded,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(v->pd, type_bits, 0),
    };
    if (mai.memoryTypeIndex == UINT32_MAX) {
        fprintf(stderr, "import: no memory type\n");
        return -1;
    }
    r = vkAllocateMemory(v->dev, &mai, NULL, &f->mem);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "import: vkAllocateMemory -> %d\n", r);
        return -1;
    }
    r = vkBindImageMemory(v->dev, f->image, f->mem, 0);
    if (r != VK_SUCCESS) {
        fprintf(stderr, "import: vkBindImageMemory -> %d\n", r);
        return -1;
    }

    f->size = mr.size;
    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(v->dev, f->image, &sub, &lay);
    f->pitch = lay.rowPitch;
    printf("import: %ux%u pitch=%llu size=%llu (fd %d)\n", w, h,
           (unsigned long long)lay.rowPitch, (unsigned long long)mr.size, fd);
    return frame_view_and_fb(v, f, w, h, fmt);
}

/* PVR-owned linear image (fallback path). */
static int frame_init_own(struct vk_state *v, struct frame *f, uint32_t w,
                          uint32_t h, VkFormat fmt)
{
    memset(f, 0, sizeof(*f));
    f->dmabuf_fd = -1;

    VkImageCreateInfo ci = linear_image_ci(w, h, fmt, NULL);
    CHECK_VK(vkCreateImage(v->dev, &ci, NULL, &f->image));

    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(v->dev, f->image, &mr);

    VkMemoryDedicatedAllocateInfo ded = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
        .image = f->image,
    };
    VkMemoryAllocateInfo mai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .pNext = &ded,
        .allocationSize = mr.size,
        .memoryTypeIndex = find_mem_type(
            v->pd, mr.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                VK_MEMORY_PROPERTY_HOST_COHERENT_BIT),
    };
    if (mai.memoryTypeIndex == UINT32_MAX)
        mai.memoryTypeIndex = find_mem_type(v->pd, mr.memoryTypeBits, 0);
    CHECK_VK(vkAllocateMemory(v->dev, &mai, NULL, &f->mem));
    CHECK_VK(vkBindImageMemory(v->dev, f->image, f->mem, 0));
    f->size = mr.size;
    if (vkMapMemory(v->dev, f->mem, 0, VK_WHOLE_SIZE, 0, &f->host) !=
        VK_SUCCESS)
        f->host = NULL;

    VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
    VkSubresourceLayout lay;
    vkGetImageSubresourceLayout(v->dev, f->image, &sub, &lay);
    f->pitch = lay.rowPitch;
    printf("own: %ux%u pitch=%llu size=%llu host=%p\n", w, h,
           (unsigned long long)lay.rowPitch, (unsigned long long)mr.size,
           f->host);
    return frame_view_and_fb(v, f, w, h, fmt);
}

static void frame_fini(struct vk_state *v, struct frame *f)
{
    if (f->fb)
        vkDestroyFramebuffer(v->dev, f->fb, NULL);
    if (f->view)
        vkDestroyImageView(v->dev, f->view, NULL);
    if (f->mem)
        vkFreeMemory(v->dev, f->mem, NULL);
    if (f->image)
        vkDestroyImage(v->dev, f->image, NULL);
    f->fb = VK_NULL_HANDLE;
    f->view = VK_NULL_HANDLE;
    f->mem = VK_NULL_HANDLE;
    f->image = VK_NULL_HANDLE;
}

#define MAX_LAYERS 16

static struct wl_draw_surf g_draw[MAX_LAYERS];
static int g_ndraw = 0;

/* --- touch input --------------------------------------------------------- */

static int g_evfd = -1;
static int g_abs_xmax = 0;
static int g_abs_ymax = 0;
static int g_grab = -1;
static float g_grab_dx, g_grab_dy;
static uint32_t g_frame_w, g_frame_h;

static int input_open(const char *forced)
{
    char path[64];
    int i;

    for (i = 0; i < 32; i++) {
        unsigned long absbits[(ABS_MAX / (8 * sizeof(unsigned long))) + 1] = { 0 };
        struct input_absinfo ai_x, ai_y;
        int fd;

        if (forced)
            snprintf(path, sizeof(path), "%s", forced);
        else
            snprintf(path, sizeof(path), "/dev/input/event%d", i);

        fd = open(path, O_RDONLY | O_NONBLOCK);
        if (fd < 0)
            continue;

        if (ioctl(fd, EVIOCGBIT(EV_ABS, sizeof(absbits)), absbits) < 0 ||
            !(absbits[ABS_MT_POSITION_X / (8 * sizeof(unsigned long))] &
              (1UL << (ABS_MT_POSITION_X % (8 * sizeof(unsigned long))))) ||
            ioctl(fd, EVIOCGABS(ABS_MT_POSITION_X), &ai_x) < 0 ||
            ioctl(fd, EVIOCGABS(ABS_MT_POSITION_Y), &ai_y) < 0) {
            close(fd);
            if (forced)
                return -1;
            continue;
        }

        g_abs_xmax = ai_x.maximum;
        g_abs_ymax = ai_y.maximum;
        printf("input: %s (abs %dx%d)\n", path, g_abs_xmax, g_abs_ymax);
        return fd;
    }
    return -1;
}

/* Returns 1 when a new touch position is available (down or move), 2 on up. */
static int input_poll(uint32_t w, uint32_t h, float *px, float *py)
{
    struct input_event ev;
    int state = 0;
    int have_pos = 0;
    static int raw_x, raw_y;
    static int touching;
    int tracking = -2;

    if (g_evfd < 0)
        return 0;

    while (read(g_evfd, &ev, sizeof(ev)) == (ssize_t)sizeof(ev)) {
        if (ev.type == EV_ABS) {
            if (ev.code == ABS_MT_POSITION_X) {
                raw_x = ev.value;
                have_pos = 1;
            } else if (ev.code == ABS_MT_POSITION_Y) {
                raw_y = ev.value;
                have_pos = 1;
            } else if (ev.code == ABS_MT_TRACKING_ID) {
                tracking = ev.value;
            }
        } else if (ev.type == EV_SYN && ev.code == SYN_REPORT) {
            if (tracking >= 0) {
                touching = 1;
                state = 1;
            } else if (tracking == -1) {
                touching = 0;
                state = 2;
            } else if (touching && have_pos) {
                state = 1;
            }
            have_pos = 0;
            tracking = -2;
        }
    }

    if (state && g_abs_xmax > 0 && g_abs_ymax > 0) {
        *px = (float)raw_x / (float)g_abs_xmax * (float)(w - 1);
        *py = (float)raw_y / (float)g_abs_ymax * (float)(h - 1);
    }
    return state;
}

static void input_handle(uint32_t w, uint32_t h)
{
    float px = 0, py = 0;
    int state = input_poll(w, h, &px, &py);

    if (state)
        wl_backend_input(state == 1, px, py);
}

/* 6 vertices per surface: pos(vec3) + uv(vec2) + colour(vec4). */
static void wl_upload_vbo(struct vk_state *v, uint32_t w, uint32_t h)
{
    float *dst = v->vbo_ptr;

    for (int i = 0; i < g_ndraw; i++) {
        const struct wl_draw_surf *l = &g_draw[i];
        float x0 = l->x / (float)w * 2.0f - 1.0f;
        float x1 = (l->x + l->w) / (float)w * 2.0f - 1.0f;
        /* Vulkan clip space: y = +1 is the *bottom* of the framebuffer. */
        float y0 = l->y / (float)h * 2.0f - 1.0f;
        float y1 = (l->y + l->h) / (float)h * 2.0f - 1.0f;
        const float q[6][4] = {
            { x0, y0, 0.0f, 0.0f }, { x1, y0, 1.0f, 0.0f },
            { x0, y1, 0.0f, 1.0f }, { x1, y0, 1.0f, 0.0f },
            { x1, y1, 1.0f, 1.0f }, { x0, y1, 0.0f, 1.0f },
        };

        for (int k = 0; k < 6; k++) {
            dst[0] = q[k][0];
            dst[1] = q[k][1];
            dst[2] = 0.0f;
            dst[3] = q[k][2];
            dst[4] = q[k][3];
            dst[5] = 1.0f;
            dst[6] = 1.0f;
            dst[7] = 1.0f;
            dst[8] = 1.0f;
            dst += 9;
        }
    }
}

/* Scissor rect (top-left origin) of a surface, clamped to the screen. */
static VkRect2D draw_scissor(const struct wl_draw_surf *l, uint32_t w,
                             uint32_t h)
{
    int32_t x = (int32_t)l->x;
    int32_t y = (int32_t)l->y;
    int32_t x1 = (int32_t)(l->x + l->w);
    int32_t y1 = (int32_t)(l->y + l->h);

    if (x < 0)
        x = 0;
    if (y < 0)
        y = 0;
    if (x1 > (int32_t)w)
        x1 = (int32_t)w;
    if (y1 > (int32_t)h)
        y1 = (int32_t)h;
    return (VkRect2D){
        { x, y },
        { (uint32_t)(x1 > x ? x1 - x : 0), (uint32_t)(y1 > y ? y1 - y : 0) },
    };
}

/* --- textures ------------------------------------------------------------ */

static void tex_pattern(uint32_t t, uint32_t x, uint32_t y, uint32_t size,
                        uint8_t out[4])
{
    float fx = (float)x / (float)(size - 1);
    float fy = (float)y / (float)(size - 1);

    switch (t) {
    case 0: /* checkerboard + border */
        if (x < 6 || y < 6 || x >= size - 6 || y >= size - 6) {
            out[0] = 255; out[1] = 255; out[2] = 255; out[3] = 255;
        } else if (((x / 32) + (y / 32)) & 1) {
            out[0] = 220; out[1] = 60; out[2] = 60; out[3] = 255;
        } else {
            out[0] = 50; out[1] = 60; out[2] = 220; out[3] = 255;
        }
        break;
    case 1: /* horizontal gradient + vertical bands */
        out[0] = (uint8_t)(255.0f * fx);
        out[1] = (uint8_t)(255.0f * (1.0f - fx));
        out[2] = (uint8_t)(255.0f * fy);
        out[3] = 255;
        if (((x / 8) & 1) == 0) {
            out[0] /= 2;
            out[1] /= 2;
        }
        break;
    case 2: { /* rings */
        float dx = fx - 0.5f, dy = fy - 0.5f;
        float d = sqrtf(dx * dx + dy * dy) * 12.0f;
        int ring = (int)d;

        out[0] = (ring & 1) ? 240 : 30;
        out[1] = (ring & 1) ? 200 : 200;
        out[2] = (ring & 1) ? 40 : 30;
        out[3] = 255;
        break;
    }
    default: /* diagonal stripes */
        if ((((x + y) / 16) & 1) == 0) {
            out[0] = 40; out[1] = 220; out[2] = 120; out[3] = 255;
        } else {
            out[0] = 20; out[1] = 60; out[2] = 40; out[3] = 255;
        }
        break;
    }
}

static int create_textures(struct vk_state *v)
{
    VkSamplerCreateInfo sci = {
        .sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
        .magFilter = VK_FILTER_LINEAR,
        .minFilter = VK_FILTER_LINEAR,
        .addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
        .addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
    };
    CHECK_VK(vkCreateSampler(v->dev, &sci, NULL, &v->sampler));

    VkDescriptorPoolSize psz = {
        .type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        .descriptorCount = MAX_LAYERS,
    };
    VkDescriptorPoolCreateInfo dpci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        .maxSets = MAX_LAYERS,
        .poolSizeCount = 1,
        .pPoolSizes = &psz,
    };
    CHECK_VK(vkCreateDescriptorPool(v->dev, &dpci, NULL, &v->dpool));

    printf("textures: %u surface slots, %ux%u max\n", (unsigned)MAX_LAYERS,
           4096u, 4096u);
    return 0;
}

struct wl_damage {
    int32_t x0, y0, x1, y1;
};

static void dmg_reset(struct wl_damage *d)
{
    d->x0 = 1 << 30;
    d->y0 = 1 << 30;
    d->x1 = -1;
    d->y1 = -1;
}

static void dmg_union(struct wl_damage *d, int32_t x0, int32_t y0, int32_t x1,
                      int32_t y1)
{
    if (x1 <= x0 || y1 <= y0)
        return;
    if (x0 < d->x0) d->x0 = x0;
    if (y0 < d->y0) d->y0 = y0;
    if (x1 > d->x1) d->x1 = x1;
    if (y1 > d->y1) d->y1 = y1;
}

static int dmg_empty(const struct wl_damage *d)
{
    return d->x1 <= d->x0 || d->y1 <= d->y0;
}

static VkRect2D rect_intersect(VkRect2D a, VkRect2D b)
{
    int32_t x0 = a.offset.x > b.offset.x ? a.offset.x : b.offset.x;
    int32_t y0 = a.offset.y > b.offset.y ? a.offset.y : b.offset.y;
    int32_t x1 = (a.offset.x + (int32_t)a.extent.width) <
                         (b.offset.x + (int32_t)b.extent.width)
                     ? (a.offset.x + (int32_t)a.extent.width)
                     : (b.offset.x + (int32_t)b.extent.width);
    int32_t y1 = (a.offset.y + (int32_t)a.extent.height) <
                         (b.offset.y + (int32_t)b.extent.height)
                     ? (a.offset.y + (int32_t)a.extent.height)
                     : (b.offset.y + (int32_t)b.extent.height);

    if (x1 < x0) x1 = x0;
    if (y1 < y0) y1 = y0;
    return (VkRect2D){ { x0, y0 },
                       { (uint32_t)(x1 - x0), (uint32_t)(y1 - y0) } };
}

int main(void)
{
    const char *drm_path =
        getenv("VK_KMS_DRM") ? getenv("VK_KMS_DRM") : "/dev/dri/card0";
    int seconds = getenv("VK_KMS_SECS") ? atoi(getenv("VK_KMS_SECS")) : 20;
    int force_dumb = getenv("VK_KMS_DUMB") != NULL;
    int no_present = getenv("VK_KMS_NOPRESENT") != NULL;
    int draws_per_frame = getenv("VK_KMS_DRAWS") ? atoi(getenv("VK_KMS_DRAWS")) : 1;
    int clear_only = getenv("VK_KMS_CLEARONLY") != NULL;
    if (draws_per_frame < 1)
        draws_per_frame = 1;

    struct drm_state d;
    memset(&d, 0, sizeof(d));
    d.fd = open(drm_path, O_RDWR);
    if (d.fd < 0) {
        fprintf(stderr, "open %s: %s\n", drm_path, strerror(errno));
        return 1;
    }
    if (drm_find_output(&d))
        return 1;
    if (drmSetMaster(d.fd))
        fprintf(stderr, "drmSetMaster: %s (continuing)\n", strerror(errno));

    uint32_t w = d.mode.hdisplay, h = d.mode.vdisplay;

    struct vk_state v;
    VkFormat fmt = VK_FORMAT_B8G8R8A8_UNORM;
    vk_init(&v, fmt, w, h);

    create_textures(&v);

    struct frame fr[NSLOT];
    memset(fr, 0, sizeof(fr));
    int zero_copy = 0;

    if (!force_dumb) {
        int ok = 1;

        for (int i = 0; i < NSLOT && ok; i++) {
            struct drm_mode_create_dumb cd = {
                .width = w,
                .height = h,
                .bpp = 32,
            };
            int fd = -1;

            if (ioctl(d.fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
                fprintf(stderr, "CREATE_DUMB: %s\n", strerror(errno));
                ok = 0;
                break;
            }
            fr[i].dumb_handle = cd.handle;
            fr[i].dumb_pitch = cd.pitch;
            if (drmModeAddFB(d.fd, w, h, 24, 32, cd.pitch, cd.handle,
                             &fr[i].drm_fb)) {
                fprintf(stderr, "AddFB: %s\n", strerror(errno));
                ok = 0;
                break;
            }
            if (drmPrimeHandleToFD(d.fd, cd.handle, DRM_CLOEXEC, &fd)) {
                fprintf(stderr, "PrimeHandleToFD: %s\n", strerror(errno));
                ok = 0;
                break;
            }
            if (frame_init_import(&v, &fr[i], w, h, fmt, fd)) {
                ok = 0;
                break;
            }
        }

        if (ok) {
            zero_copy = 1;
            printf("zero-copy: Vulkan renders into the scanout dma-buf\n");
        } else {
            for (int i = 0; i < NSLOT; i++) {
                frame_fini(&v, &fr[i]);
                if (fr[i].drm_fb) {
                    drmModeRmFB(d.fd, fr[i].drm_fb);
                    fr[i].drm_fb = 0;
                }
            }
        }
    }

    if (!zero_copy) {
        printf("fallback: PVR image + CPU copy\n");
        for (int i = 0; i < NSLOT; i++) {
            struct drm_mode_create_dumb cd = {
                .width = w,
                .height = h,
                .bpp = 32,
            };

            if (frame_init_own(&v, &fr[i], w, h, fmt))
                return 1;
            if (!fr[i].host) {
                fprintf(stderr, "image is not host visible, cannot copy\n");
                return 1;
            }
            if (ioctl(d.fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
                fprintf(stderr, "CREATE_DUMB: %s\n", strerror(errno));
                return 1;
            }
            fr[i].dumb_handle = cd.handle;
            fr[i].dumb_pitch = cd.pitch;
            if (drmModeAddFB(d.fd, w, h, 24, 32, cd.pitch, cd.handle,
                             &fr[i].drm_fb)) {
                fprintf(stderr, "AddFB: %s\n", strerror(errno));
                return 1;
            }
            struct drm_mode_map_dumb md = { .handle = cd.handle };
            if (ioctl(d.fd, DRM_IOCTL_MODE_MAP_DUMB, &md)) {
                fprintf(stderr, "MAP_DUMB: %s\n", strerror(errno));
                return 1;
            }
            fr[i].dumb_ptr = mmap(NULL, cd.size, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, d.fd, md.offset);
            if (fr[i].dumb_ptr == MAP_FAILED) {
                fprintf(stderr, "mmap dumb: %s\n", strerror(errno));
                return 1;
            }
            printf("dumb fb[%d] pitch=%u size=%llu\n", i, cd.pitch,
                   (unsigned long long)cd.size);
        }
    }

    VkFence fences[NSLOT];
    fences[0] = v.fence;
    for (int i = 1; i < NSLOT; i++) {
        VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
        CHECK_VK(vkCreateFence(v.dev, &fci, NULL, &fences[i]));
    }

    int busy[NSLOT] = { 1, 0, 0 };
    int onscreen = 0;
    int pending = -1;
    int next_slot = 1;
    int slot_valid[NSLOT] = { 0 };
    struct wl_damage slot_dmg[NSLOT];
    VkRenderPass frame_rp = v.rp;
    unsigned long long idle_frames = 0;
    int idle_run = 0;

    for (int k = 0; k < NSLOT; k++)
        dmg_reset(&slot_dmg[k]);

    /* First frame: render before the initial modeset. */
    {
        struct frame *f = &fr[0];
        struct wl_backend_cfg wcfg = {
            .fb_width = w,
            .fb_height = h,
            .pd = v.pd,
            .dev = v.dev,
            .dsl = v.dsl,
            .dpool = v.dpool,
            .sampler = v.sampler,
            .get_fd_props = v.get_fd_props,
        };

        if (wl_backend_init(&wcfg))
            return 1;
        g_ndraw = wl_backend_collect(g_draw, MAX_LAYERS);
        wl_upload_vbo(&v, w, h);
        VkCommandBufferBeginInfo bi = {
            .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        };
        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));
        wl_backend_prepare(v.cmd);
        VkClearValue cv = { .color = { { 0.05f, 0.05f, 0.1f, 1.0f } } };
        VkRenderPassBeginInfo rbi = {
            .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
            .renderPass = frame_rp,
            .framebuffer = f->fb,
            .renderArea = { { 0, 0 }, { w, h } },
            .clearValueCount = 1,
            .pClearValues = &cv,
        };
        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        for (int d = 0; d < g_ndraw; d++) {
            const struct wl_draw_surf *l = &g_draw[d];
            VkRect2D dsc = draw_scissor(l, w, h);

            if (!l->tex || !dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets(
                v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.layout, 0, 1,
                &l->tex, 0, NULL);
            vkCmdDraw(v.cmd, 6, 1, (uint32_t)d * 6, 0);
        }
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));
        VkSubmitInfo si = {
            .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
            .commandBufferCount = 1,
            .pCommandBuffers = &v.cmd,
        };
        CHECK_VK(vkResetFences(v.dev, 1, &v.fence));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, v.fence));
        CHECK_VK(vkWaitForFences(v.dev, 1, &v.fence, VK_TRUE, 2000000000ull));
        if (!zero_copy) {
            for (uint32_t y = 0; y < h; y++)
                memcpy((char *)f->dumb_ptr + (size_t)y * f->dumb_pitch,
                       (const char *)f->host + (size_t)y * f->pitch,
                       (size_t)w * 4);
        }
        slot_valid[0] = 1;
    }

    CHECK_DRM(drmModeSetCrtc(d.fd, d.crtc_id, fr[0].drm_fb, 0, 0, &d.conn_id, 1,
                             &d.mode));

    g_evfd = input_open(getenv("VK_COMP_INPUT"));
    if (g_evfd < 0)
        printf("input: no touch device found\n");

    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t frames = 0;
    int cur = 1;
    double t_submit = 0.0, t_flip = 0.0;
    double t_record = 0.0, t_queue = 0.0, t_fence = 0.0;

    while (1) {
        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);
        double elapsed = (now.tv_sec - t0.tv_sec) +
                         (now.tv_nsec - t0.tv_nsec) / 1e9;
        if (elapsed >= seconds)
            break;

        wl_backend_pump();
        input_handle(w, h);
        if (getenv("VK_WL_FAKE_TOUCH") && frames == 240) {
            wl_backend_input(1, 100.0f, 250.0f);
            wl_backend_input(1, 130.0f, 280.0f);
            wl_backend_input(1, 160.0f, 310.0f);
            wl_backend_input(0, 160.0f, 310.0f);
            printf("wl: fake touch drag +60,+60\n");
        }

        /* Nothing changed and nobody waits for a frame: keep the last
         * frame on screen and sleep in the event loop (vsync-rate power). */
        if (pending < 0 && !wl_backend_needs_frame() &&
            !getenv("VK_WL_NOIDLE")) {
            idle_frames++;
            wl_backend_wait(getenv("VK_WL_IDLE_MS")
                                ? atoi(getenv("VK_WL_IDLE_MS"))
                                : 16);
            continue;
        }
        wl_backend_frame((uint32_t)(elapsed * 1000.0));

        /* Pick a buffer that is neither on screen nor awaiting a flip. */
        int i = -1;
        for (int k = 0; k < NSLOT; k++) {
            int idx = (next_slot + k) % NSLOT;
            if (!busy[idx]) {
                i = idx;
                break;
            }
        }
        if (i < 0)
            break;
        next_slot = (i + 1) % NSLOT;

        struct frame *f = &fr[i];
        struct wl_damage cur, dmg;
        int32_t d4[4];
        int full;

        g_ndraw = wl_backend_collect(g_draw, MAX_LAYERS);
        wl_upload_vbo(&v, w, h);

        dmg_reset(&cur);
        if (wl_backend_take_damage(d4)) {
            dmg_union(&cur, d4[0], d4[1], d4[2], d4[3]);
        }

        dmg = slot_dmg[i];
        dmg_union(&dmg, cur.x0, cur.y0, cur.x1, cur.y1);
        full = !slot_valid[i] || getenv("VK_WL_FULLREDRAW") != NULL;
        if (full) {
            dmg.x0 = 0;
            dmg.y0 = 0;
            dmg.x1 = (int32_t)w;
            dmg.y1 = (int32_t)h;
        }
        if (dmg_empty(&dmg)) {
            /* Keep the vsync cadence while the session is active (the old
             * behaviour), and only go idle after ~1 s without any damage. */
            if (idle_run++ < 60) {
                full = 1;
                dmg.x0 = 0;
                dmg.y0 = 0;
                dmg.x1 = (int32_t)w;
                dmg.y1 = (int32_t)h;
            } else if (pending < 0) {
                continue;
            } else {
                i = -1;
                goto present;
            }
        } else {
            idle_run = 0;
        }
        frame_rp = full ? v.rp : v.rp_load;

        VkCommandBufferBeginInfo bi = {
            .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        };
        CHECK_VK(vkBeginCommandBuffer(v.cmd, &bi));
        wl_backend_prepare(v.cmd);
        VkClearValue cv = { .color = { { 0.05f, 0.05f, 0.1f, 1.0f } } };
        VkRenderPassBeginInfo rbi = {
            .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
            .renderPass = frame_rp,
            .framebuffer = f->fb,
            .renderArea = { { 0, 0 }, { w, h } },
            .clearValueCount = 1,
            .pClearValues = &cv,
        };
        vkCmdBeginRenderPass(v.cmd, &rbi, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.pipe);
        VkViewport vp = { 0, 0, (float)w, (float)h, 0, 1 };
        VkRect2D sc = { { 0, 0 }, { w, h } };
        VkRect2D drect = { { dmg.x0, dmg.y0 },
                           { (uint32_t)(dmg.x1 - dmg.x0),
                             (uint32_t)(dmg.y1 - dmg.y0) } };
        VkDeviceSize off = 0;
        vkCmdBindVertexBuffers(v.cmd, 0, 1, &v.vbo, &off);
        if (!full) {
            /* Preserved slot: repaint the background only under damage. */
            VkClearAttachment ca = {
                .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
                .colorAttachment = 0,
                .clearValue = cv,
            };
            VkClearRect cr = { drect, 0, 1 };

            vkCmdSetScissor(v.cmd, 0, 1, &drect);
            vkCmdClearAttachments(v.cmd, 1, &ca, 1, &cr);
        }
        for (int d = 0; d < (clear_only ? 0 : g_ndraw); d++) {
            const struct wl_draw_surf *l = &g_draw[d];
            VkRect2D dsc = draw_scissor(l, w, h);

            dsc = rect_intersect(dsc, drect);
            if (!l->tex || !dsc.extent.width || !dsc.extent.height)
                continue;
            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets(
                v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.layout, 0, 1,
                &l->tex, 0, NULL);
            vkCmdDraw(v.cmd, 6, 1, (uint32_t)d * 6, 0);
        }
        vkCmdEndRenderPass(v.cmd);
        CHECK_VK(vkEndCommandBuffer(v.cmd));

        VkSubmitInfo si = {
            .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
            .commandBufferCount = 1,
            .pCommandBuffers = &v.cmd,
        };
        struct timespec ts0, ts1;
        clock_gettime(CLOCK_MONOTONIC, &ts0);
        CHECK_VK(vkResetFences(v.dev, 1, &fences[i]));
        CHECK_VK(vkQueueSubmit(v.queue, 1, &si, fences[i]));
        clock_gettime(CLOCK_MONOTONIC, &ts1);
        t_queue += (ts1.tv_sec - ts0.tv_sec) + (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
        busy[i] = 1;
        slot_valid[i] = 1;
        dmg_reset(&slot_dmg[i]);
        for (int k = 0; k < NSLOT; k++)
            if (k != i && slot_valid[k])
                dmg_union(&slot_dmg[k], cur.x0, cur.y0, cur.x1, cur.y1);

    present:
        /* Present the previous frame: its render had a whole flip period. */
        if (pending >= 0) {
            struct frame *pf = &fr[pending];

            clock_gettime(CLOCK_MONOTONIC, &ts0);
            CHECK_VK(vkWaitForFences(v.dev, 1, &fences[pending], VK_TRUE,
                                     2000000000ull));
            clock_gettime(CLOCK_MONOTONIC, &ts1);
            t_fence += (ts1.tv_sec - ts0.tv_sec) +
                       (ts1.tv_nsec - ts0.tv_nsec) / 1e9;

            if (!zero_copy) {
                for (uint32_t y = 0; y < h; y++)
                    memcpy((char *)pf->dumb_ptr + (size_t)y * pf->dumb_pitch,
                           (const char *)pf->host + (size_t)y * pf->pitch,
                           (size_t)w * 4);
            }

            if (no_present) {
                busy[pending] = 0;
                frames++;
            } else {
                clock_gettime(CLOCK_MONOTONIC, &ts0);
                g_flip_done = 0;
                if (drmModePageFlip(d.fd, d.crtc_id, pf->drm_fb,
                                    DRM_MODE_PAGE_FLIP_EVENT, NULL)) {
                    fprintf(stderr, "page flip failed: %s\n", strerror(errno));
                    break;
                }
                if (wait_flip(d.fd))
                    break;
                clock_gettime(CLOCK_MONOTONIC, &ts1);
                t_flip += (ts1.tv_sec - ts0.tv_sec) +
                          (ts1.tv_nsec - ts0.tv_nsec) / 1e9;
                busy[onscreen] = 0;
                onscreen = pending;
                frames++;
            }
        }

        pending = i;
    }

    struct timespec t1;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double total =
        (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("surfaces=%d\n", g_ndraw);
    printf("presented %llu frames in %.2fs (%.1f fps), mode=%s\n",
           (unsigned long long)frames, total, frames / total,
           zero_copy ? "zero-copy" : "cpu-copy");
    {
        struct rusage ru;
        double cpu;

        getrusage(RUSAGE_SELF, &ru);
        cpu = ru.ru_utime.tv_sec + ru.ru_stime.tv_sec +
              (ru.ru_utime.tv_usec + ru.ru_stime.tv_usec) / 1e6;
        printf("cpu: %.2fs over %.2fs (%.1f%%), idle frames %llu\n", cpu,
               total, 100.0 * cpu / (total > 0.0 ? total : 1.0), idle_frames);
    }
    if (getenv("VK_COMP_VERIFY")) {
        const float *fv = v.vbo_ptr;

        printf("verify: vbo[0..8] = %.3f %.3f %.3f | %.3f %.3f | %.3f %.3f %.3f\n",
               fv[0], fv[1], fv[2], fv[3], fv[4], fv[5], fv[6], fv[7], fv[8]);
        for (int sl = 0; sl < NSLOT; sl++) {
        struct frame *f = &fr[sl];
        struct drm_mode_map_dumb md = { .handle = f->dumb_handle };

        if (ioctl(d.fd, DRM_IOCTL_MODE_MAP_DUMB, &md) == 0) {
            size_t sz = (size_t)f->dumb_pitch * h;
            void *p = mmap(NULL, sz, PROT_READ, MAP_SHARED, d.fd, md.offset);

            if (p != MAP_FAILED) {
                const uint32_t *px = p;
                uint32_t stride = f->dumb_pitch / 4;
                uint32_t corner = px[0];
                uint32_t diff = 0, total = 0;
                int sw = 0, sx = 0, sy = 0;

                for (uint32_t y = 0; y < h; y += 5) {
                    for (uint32_t x = 0; x < w; x += 5) {
                        total++;
                        if (px[(size_t)y * stride + x] != corner) {
                            diff++;
                            sw = (int)px[(size_t)y * stride + x];
                            sx = (int)x;
                            sy = (int)y;
                        }
                    }
                }
                printf("verify: onscreen=%d surfaces=%d corner=%08x\n",
                       onscreen, g_ndraw, corner);
                for (int si = 0; si < g_ndraw; si++) {
                    int cx = (int)(g_draw[si].x + g_draw[si].w / 2);
                    int cy = (int)(g_draw[si].y + g_draw[si].h / 2);
                    int tx = (int)(g_draw[si].x + 6);
                    int ty = (int)(g_draw[si].y + 6);
                    int by = (int)(g_draw[si].y + g_draw[si].h - 6);

                    if (cx < 0) cx = 0;
                    if (cy < 0) cy = 0;
                    if (cx >= (int)w) cx = (int)w - 1;
                    if (cy >= (int)h) cy = (int)h - 1;
                    if (tx < 0) tx = 0;
                    if (ty < 0) ty = 0;
                    if (by < 0) by = 0;
                    if (tx >= (int)w) tx = (int)w - 1;
                    if (ty >= (int)h) ty = (int)h - 1;
                    if (by >= (int)h) by = (int)h - 1;
                    printf("verify: surf%d rect=(%.0f,%.0f %.0fx%.0f) centre=(%d,%d) %08x  marker top=%08x bottom=%08x\n",
                           si, g_draw[si].x, g_draw[si].y, g_draw[si].w,
                           g_draw[si].h, cx, cy,
                           px[(size_t)cy * stride + cx],
                           px[(size_t)ty * stride + tx],
                           px[(size_t)by * stride + tx]);
                }
                {
                    int minx = (int)w, maxx = -1, miny = (int)h, maxy = -1;

                    for (uint32_t y = 0; y < h; y++) {
                        for (uint32_t x = 0; x < w; x++) {
                            if (px[(size_t)y * stride + x] == corner)
                                continue;
                            if ((int)x < minx) minx = (int)x;
                            if ((int)x > maxx) maxx = (int)x;
                            if ((int)y < miny) miny = (int)y;
                            if ((int)y > maxy) maxy = (int)y;
                        }
                    }
                    printf("verify: slot=%d diff=%u/%u bbox x=%d..%d y=%d..%d\n",
                           sl, diff, total, minx, maxx, miny, maxy);
                }
                munmap(p, sz);
            }
        }
        }
    }

    if (frames)
        printf("avg: submit+fence %.2f ms, pageflip %.2f ms\n",
               1000.0 * t_submit / frames, 1000.0 * t_flip / frames);
    if (frames)
        printf("avg: queue %.2f ms, fence-wait %.2f ms (draws/frame=%d)\n",
               1000.0 * t_queue / frames, 1000.0 * t_fence / frames,
               draws_per_frame);

    if (d.orig_crtc && d.orig_crtc->mode_valid)
        drmModeSetCrtc(d.fd, d.crtc_id, d.orig_crtc->buffer_id,
                       d.orig_crtc->x, d.orig_crtc->y, &d.conn_id, 1,
                       &d.orig_crtc->mode);
    return frames ? 0 : 2;
}
