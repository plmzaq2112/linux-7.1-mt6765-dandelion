// Minimal KMS test for /dev/dri/cardX using raw DRM ioctls (no libdrm).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <stdint.h>

#include <drm/drm.h>
#include <drm/drm_mode.h>

static int xioctl(int fd, unsigned long req, void *arg)
{
	int r;
	do {
		r = ioctl(fd, req, arg);
	} while (r == -1 && errno == EINTR);
	return r;
}

int main(int argc, char **argv)
{
	const char *card = argc > 1 ? argv[1] : "/dev/dri/card1";
	int fd = open(card, O_RDWR);
	if (fd < 0) {
		perror("open");
		return 1;
	}

	struct drm_mode_card_res res;
	memset(&res, 0, sizeof(res));
	if (xioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res)) {
		perror("GETRESOURCES");
		return 1;
	}
	printf("resources: crtc=%u conn=%u enc=%u fb=%u\n",
	       res.count_crtcs, res.count_connectors, res.count_encoders, res.count_fbs);

	uint32_t *conn_ids = calloc(res.count_connectors ? res.count_connectors : 1, 4);
	uint32_t *crtc_ids = calloc(res.count_crtcs ? res.count_crtcs : 1, 4);
	uint32_t *enc_ids = calloc(res.count_encoders ? res.count_encoders : 1, 4);
	uint32_t *fb_ids = calloc(res.count_fbs ? res.count_fbs : 1, 4);
	res.connector_id_ptr = (uint64_t)(uintptr_t)conn_ids;
	res.crtc_id_ptr = (uint64_t)(uintptr_t)crtc_ids;
	res.encoder_id_ptr = (uint64_t)(uintptr_t)enc_ids;
	res.fb_id_ptr = (uint64_t)(uintptr_t)fb_ids;
	if (xioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res)) {
		perror("GETRESOURCES2");
		return 1;
	}
	printf("crtc_ids[0]=%u enc_ids[0]=%u\n", crtc_ids[0], enc_ids[0]);

	struct drm_mode_modeinfo mode;
	uint32_t conn_id = 0;
	int found = 0;

	for (unsigned i = 0; i < res.count_connectors; i++) {
		struct drm_mode_get_connector c;
		memset(&c, 0, sizeof(c));
		c.connector_id = conn_ids[i];
		if (xioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &c)) {
			perror("GETCONNECTOR");
			continue;
		}
		printf("connector %u: type=%u status=%u modes=%u enc=%u props=%u\n",
		       c.connector_id, c.connector_type, c.connection,
		       c.count_modes, c.encoder_id, c.count_props);
		if (c.connection != 1 || c.count_modes == 0)
			continue;

		struct drm_mode_modeinfo *ms = calloc(c.count_modes, sizeof(*ms));
		uint32_t *props = calloc(c.count_props ? c.count_props : 1, 4);
		uint64_t *vals = calloc(c.count_props ? c.count_props : 1, 8);
		uint32_t *encs = calloc(c.count_encoders ? c.count_encoders : 1, 4);
		c.modes_ptr = (uint64_t)(uintptr_t)ms;
		c.props_ptr = (uint64_t)(uintptr_t)props;
		c.prop_values_ptr = (uint64_t)(uintptr_t)vals;
		c.encoders_ptr = (uint64_t)(uintptr_t)encs;
		if (xioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &c)) {
			perror("GETCONNECTOR2");
			free(ms); free(props); free(vals); free(encs);
			continue;
		}
		mode = ms[0];
		conn_id = c.connector_id;
		found = 1;
		free(ms); free(props); free(vals); free(encs);
		printf("mode: %s %ux%u clock=%u\n", mode.name, mode.hdisplay, mode.vdisplay, mode.clock);
		break;
	}

	if (!found) {
		printf("no connected connector with modes\n");
		return 2;
	}

	struct drm_mode_create_dumb cd = {
		.width = mode.hdisplay, .height = mode.vdisplay, .bpp = 32,
	};
	if (xioctl(fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd)) {
		perror("CREATE_DUMB");
		return 1;
	}
	struct drm_mode_map_dumb md = { .handle = cd.handle };
	if (xioctl(fd, DRM_IOCTL_MODE_MAP_DUMB, &md)) {
		perror("MAP_DUMB");
		return 1;
	}
	void *p = mmap(NULL, cd.size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, md.offset);
	if (p == MAP_FAILED) {
		perror("mmap");
		return 1;
	}
	uint32_t *px = p;
	unsigned npix = (unsigned)mode.hdisplay * mode.vdisplay;
	for (unsigned k = 0; k < npix; k++)
		px[k] = 0x00ff4040;

	struct drm_mode_fb_cmd fc = {
		.width = cd.width, .height = cd.height, .bpp = cd.bpp,
		.depth = 24, .pitch = cd.pitch, .handle = cd.handle,
	};
	if (xioctl(fd, DRM_IOCTL_MODE_ADDFB, &fc)) {
		perror("ADDFB");
		return 1;
	}

	struct drm_mode_crtc crtc;
	memset(&crtc, 0, sizeof(crtc));
	crtc.crtc_id = crtc_ids[0];
	if (xioctl(fd, DRM_IOCTL_MODE_GETCRTC, &crtc)) {
		perror("GETCRTC");
		return 1;
	}
	crtc.set_connectors_ptr = (uint64_t)(uintptr_t)&conn_id;
	crtc.count_connectors = 1;
	crtc.fb_id = fc.fb_id;
	crtc.mode = mode;
	crtc.mode_valid = 1;
	crtc.x = 0; crtc.y = 0;
	printf("SETCRTC crtc=%u fb=%u conn=%u ...\n", crtc.crtc_id, fc.fb_id, conn_id);
	fflush(stdout);
	if (xioctl(fd, DRM_IOCTL_MODE_SETCRTC, &crtc)) {
		perror("SETCRTC");
		return 1;
	}
	printf("SETCRTC ok\n");
	fflush(stdout);
	sleep(6);
	printf("done\n");
	return 0;
}
