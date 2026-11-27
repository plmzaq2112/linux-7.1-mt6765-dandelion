#!/usr/bin/env python3
"""vk_comp: textured layers (4 generated textures, one per layer modulo 4)"""
from pathlib import Path

p = Path('/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/src/wayland/vk_comp.c')
s = p.read_text()

# --- 1. shaders -------------------------------------------------------------
s = s.replace('#include "ds_vert_spv.h"', '#include "comp_vert_spv.h"', 1)
s = s.replace('#include "ds_frag_spv.h"', '#include "comp_frag_spv.h"', 1)
s = s.replace('v->vs = make_shader(v->dev, ds_vert_spv, ds_vert_spv_len);',
              'v->vs = make_shader(v->dev, comp_vert_spv, comp_vert_spv_len);', 1)
s = s.replace('v->fs = make_shader(v->dev, ds_frag_spv, ds_frag_spv_len);',
              'v->fs = make_shader(v->dev, comp_frag_spv, comp_frag_spv_len);', 1)

# --- 2. state: textures -----------------------------------------------------
old = '''    PFN_vkGetMemoryFdKHR get_memory_fd;
    PFN_vkGetMemoryFdPropertiesKHR get_fd_props;
};'''
new = '''    PFN_vkGetMemoryFdKHR get_memory_fd;
    PFN_vkGetMemoryFdPropertiesKHR get_fd_props;

    VkDescriptorSetLayout dsl;
    VkDescriptorPool dpool;
    VkSampler sampler;
#define NUM_TEX 4
    VkImage tex_img[NUM_TEX];
    VkDeviceMemory tex_mem[NUM_TEX];
    VkImageView tex_view[NUM_TEX];
    VkDescriptorSet tex_set[NUM_TEX];
};'''
assert s.count(old) == 1, 'vk_state'
s = s.replace(old, new, 1)

# --- 3. descriptor set layout before the pipeline layout --------------------
old = '''    VkPipelineLayoutCreateInfo plci = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
    };
    CHECK_VK(vkCreatePipelineLayout(v->dev, &plci, NULL, &v->layout));'''
new = '''    VkDescriptorSetLayoutBinding dslb = {
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
    CHECK_VK(vkCreatePipelineLayout(v->dev, &plci, NULL, &v->layout));'''
assert s.count(old) == 1, 'pipeline layout'
s = s.replace(old, new, 1)

# --- 4. vertex layout: pos3 + uv2 + colour4 --------------------------------
old = '''    VkVertexInputBindingDescription vib = {
        .binding = 0,
        .stride = 7 * sizeof(float),
        .inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
    };
    VkVertexInputAttributeDescription via[2] = {
        { .location = 0, .binding = 0, .format = VK_FORMAT_R32G32B32_SFLOAT,
          .offset = 0 },
        { .location = 1, .binding = 0, .format = VK_FORMAT_R32G32B32A32_SFLOAT,
          .offset = 3 * sizeof(float) },
    };'''
new = '''    VkVertexInputBindingDescription vib = {
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
    };'''
assert s.count(old) == 1, 'vertex input'
s = s.replace(old, new, 1)
s = s.replace('''        .vertexAttributeDescriptionCount = 2,
        .pVertexAttributeDescriptions = via,''',
              '''        .vertexAttributeDescriptionCount = 3,
        .pVertexAttributeDescriptions = via,''', 1)

# --- 5. VBO size 9 floats per vertex --------------------------------------
s = s.replace('        .size = MAX_LAYERS * 6 * 7 * sizeof(float),',
              '        .size = MAX_LAYERS * 6 * 9 * sizeof(float),', 1)

# --- 6. layer upload writes pos/uv/colour ---------------------------------
start = s.index('/* 6 vertices per layer, pos(vec3) + colour(vec4). */')
end = s.index('/* Scissor rect (top-left origin) of layer i, clamped to the screen. */')
upload = r'''/* 6 vertices per layer: pos(vec3) + uv(vec2) + colour(vec4). */
static void layers_upload(struct vk_state *v, uint32_t w, uint32_t h)
{
    float *dst = v->vbo_ptr;

    for (int i = 0; i < g_nlayers; i++) {
        const struct layer *l = &g_layers[i];
        float x0 = l->x / (float)w * 2.0f - 1.0f;
        float x1 = (l->x + l->w) / (float)w * 2.0f - 1.0f;
        float y0 = 1.0f - l->y / (float)h * 2.0f;
        float y1 = 1.0f - (l->y + l->h) / (float)h * 2.0f;
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
            dst[5] = l->r;
            dst[6] = l->g;
            dst[7] = l->b;
            dst[8] = l->a;
            dst += 9;
        }
    }
}

'''
s = s[:start] + upload + s[end:]

# --- 7. textures ------------------------------------------------------------
anchor = 'int main(void)'
textures = r'''/* --- textures ------------------------------------------------------------ */

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
    const uint32_t size = 128;
    VkCommandBufferBeginInfo bi = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
    };
    CHECK_VK(vkBeginCommandBuffer(v->cmd, &bi));

    for (uint32_t t = 0; t < NUM_TEX; t++) {
        VkImageCreateInfo ci = {
            .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
            .imageType = VK_IMAGE_TYPE_2D,
            .format = VK_FORMAT_R8G8B8A8_UNORM,
            .extent = { size, size, 1 },
            .mipLevels = 1,
            .arrayLayers = 1,
            .samples = VK_SAMPLE_COUNT_1_BIT,
            .tiling = VK_IMAGE_TILING_LINEAR,
            .usage = VK_IMAGE_USAGE_SAMPLED_BIT |
                     VK_IMAGE_USAGE_TRANSFER_DST_BIT,
            .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        };
        CHECK_VK(vkCreateImage(v->dev, &ci, NULL, &v->tex_img[t]));

        VkMemoryRequirements mr;
        vkGetImageMemoryRequirements(v->dev, v->tex_img[t], &mr);
        VkMemoryAllocateInfo mai = {
            .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
            .allocationSize = mr.size,
            .memoryTypeIndex = find_mem_type(
                v->pd, mr.memoryTypeBits,
                VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT),
        };
        CHECK_VK(vkAllocateMemory(v->dev, &mai, NULL, &v->tex_mem[t]));
        CHECK_VK(vkBindImageMemory(v->dev, v->tex_img[t], v->tex_mem[t], 0));

        uint8_t *px = NULL;
        CHECK_VK(vkMapMemory(v->dev, v->tex_mem[t], 0, VK_WHOLE_SIZE, 0,
                             (void **)&px));
        VkImageSubresource sub = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
        VkSubresourceLayout lay;
        vkGetImageSubresourceLayout(v->dev, v->tex_img[t], &sub, &lay);
        for (uint32_t y = 0; y < size; y++) {
            uint8_t *row = px + lay.offset + (size_t)y * lay.rowPitch;

            for (uint32_t x = 0; x < size; x++)
                tex_pattern(t, x, y, size, row + (size_t)x * 4);
        }
        vkUnmapMemory(v->dev, v->tex_mem[t]);

        VkImageViewCreateInfo vci = {
            .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
            .image = v->tex_img[t],
            .viewType = VK_IMAGE_VIEW_TYPE_2D,
            .format = VK_FORMAT_R8G8B8A8_UNORM,
            .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
        };
        CHECK_VK(vkCreateImageView(v->dev, &vci, NULL, &v->tex_view[t]));

        VkImageMemoryBarrier b = {
            .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
            .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
            .newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .image = v->tex_img[t],
            .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 },
            .srcAccessMask = 0,
            .dstAccessMask = VK_ACCESS_SHADER_READ_BIT,
        };
        vkCmdPipelineBarrier(v->cmd, VK_PIPELINE_STAGE_HOST_BIT,
                             VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, 0, 0, NULL,
                             0, NULL, 1, &b);
    }
    CHECK_VK(vkEndCommandBuffer(v->cmd));

    VkSubmitInfo si = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1,
        .pCommandBuffers = &v->cmd,
    };
    CHECK_VK(vkQueueSubmit(v->queue, 1, &si, VK_NULL_HANDLE));
    CHECK_VK(vkQueueWaitIdle(v->queue));

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
        .descriptorCount = NUM_TEX,
    };
    VkDescriptorPoolCreateInfo dpci = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        .maxSets = NUM_TEX,
        .poolSizeCount = 1,
        .pPoolSizes = &psz,
    };
    CHECK_VK(vkCreateDescriptorPool(v->dev, &dpci, NULL, &v->dpool));

    VkDescriptorSetAllocateInfo dsai = {
        .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        .descriptorPool = v->dpool,
        .descriptorSetCount = NUM_TEX,
        .pSetLayouts = (VkDescriptorSetLayout[]){ v->dsl, v->dsl, v->dsl,
                                                  v->dsl },
    };
    CHECK_VK(vkAllocateDescriptorSets(v->dev, &dsai, v->tex_set));

    for (uint32_t t = 0; t < NUM_TEX; t++) {
        VkDescriptorImageInfo dii = {
            .sampler = v->sampler,
            .imageView = v->tex_view[t],
            .imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        };
        VkWriteDescriptorSet w = {
            .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
            .dstSet = v->tex_set[t],
            .dstBinding = 0,
            .descriptorCount = 1,
            .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
            .pImageInfo = &dii,
        };
        vkUpdateDescriptorSets(v->dev, 1, &w, 0, NULL);
    }

    printf("textures: %u x %ux%u\n", (unsigned)NUM_TEX, size, size);
    return 0;
}

int main(void)'''
s = s.replace(anchor, textures, 1)

# --- 8. bind the descriptor set per layer (both render sites) --------------
old = '''            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdDraw(v.cmd, 6, 1, (uint32_t)d * 6, 0);'''
new = '''            vkCmdSetScissor(v.cmd, 0, 1, &dsc);
            vkCmdBindDescriptorSets(
                v.cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, v.layout, 0, 1,
                &v.tex_set[d % NUM_TEX], 0, NULL);
            vkCmdDraw(v.cmd, 6, 1, (uint32_t)d * 6, 0);'''
assert s.count(old) == 2, 'render sites %d' % s.count(old)
s = s.replace(old, new)

# --- 9. create textures after vk_init -------------------------------------
old = '''    struct frame fr[NSLOT];'''
new = '''    create_textures(&v);

    struct frame fr[NSLOT];'''
assert s.count(old) == 1, 'create textures call'
s = s.replace(old, new, 1)

p.write_text(s)
print('vk_comp: textured layers')
