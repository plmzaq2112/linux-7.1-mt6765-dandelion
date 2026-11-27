// Persistent KMS player with double buffering + vsync page flip (no tearing).
// usage: kms-loop [card] [animation.kmsa]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <stdint.h>

#include <drm/drm.h>
#include <drm/drm_mode.h>

static volatile int stop;
static void on_sig(int s) { (void)s; stop = 1; }

static int xioctl(int fd, unsigned long req, void *arg)
{
	int r;
	do {
		r = ioctl(fd, req, arg);
	} while (r == -1 && errno == EINTR);
	return r;
}

struct kms_buf {
	uint16_t *map;
	uint32_t fb;
	uint32_t handle;
	uint32_t pitch;   /* in pixels */
};

static struct kms_buf bufs[2];
static int cur;            /* buffer currently scanned out */
static int drm_fd = -1;
static uint32_t conn_id, crtc_id;
static struct drm_mode_modeinfo mode;
static unsigned W, H;

/* animation */
struct anim_frame { uint16_t delay; uint32_t size; };
static struct anim {
	unsigned w, h, n;
	struct anim_frame *fr;
	uint8_t *data;
} A;

static int anim_load(const char *path)
{
	FILE *f = fopen(path, "rb");
	if (!f)
		return -1;
	char magic[4];
	uint32_t w, h, n;
	if (fread(magic, 1, 4, f) != 4 || memcmp(magic, "KMSA", 4))
		goto fail;
	if (fread(&w, 4, 1, f) != 1 || fread(&h, 4, 1, f) != 1 || fread(&n, 4, 1, f) != 1)
		goto fail;
	A.w = w; A.h = h; A.n = n;
	A.fr = calloc(n, sizeof(*A.fr));
	if (!A.fr)
		goto fail;
	size_t total = 0;
	for (unsigned i = 0; i < n; i++) {
		if (fread(&A.fr[i].delay, 2, 1, f) != 1 ||
		    fread(&A.fr[i].size, 4, 1, f) != 1)
			goto fail;
		total += A.fr[i].size;
	}
	A.data = malloc(total);
	if (!A.data)
		goto fail;
	if (fread(A.data, 1, total, f) != total)
		goto fail;
	fclose(f);
	printf("kms-loop: anim %ux%u frames=%u\n", w, h, n);
	return 0;
fail:
	fclose(f);
	return -1;
}

static int make_buf(struct kms_buf *b, struct drm_mode_card_res *res, uint32_t *crtc_ids)
{
	(void)res;
	(void)crtc_ids;
	struct drm_mode_create_dumb cd = { .width = W, .height = H, .bpp = 16 };
	if (xioctl(drm_fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd))
		return -1;
	struct drm_mode_map_dumb md = { .handle = cd.handle };
	if (xioctl(drm_fd, DRM_IOCTL_MODE_MAP_DUMB, &md))
		return -1;
	b->map = mmap(NULL, cd.size, PROT_READ | PROT_WRITE, MAP_SHARED, drm_fd, md.offset);
	if (b->map == MAP_FAILED)
		return -1;
	b->handle = cd.handle;
	b->pitch = cd.pitch / 2;

	struct drm_mode_fb_cmd fc = {
		.width = W, .height = H, .bpp = 16, .depth = 16,
		.pitch = cd.pitch, .handle = cd.handle,
	};
	if (xioctl(drm_fd, DRM_IOCTL_MODE_ADDFB, &fc))
		return -1;
	b->fb = fc.fb_id;
	return 0;
}

static int wait_flip(void)
{
	struct pollfd pfd = { .fd = drm_fd, .events = POLLIN };
	char evbuf[64];
	int r = poll(&pfd, 1, 200);
	if (r <= 0)
		return -1;
	if (read(drm_fd, evbuf, sizeof(evbuf)) <= 0)
		return -1;
	return 0;
}

static int flip_to(int idx)
{
	struct drm_mode_crtc_page_flip fl;
	memset(&fl, 0, sizeof(fl));
	fl.crtc_id = crtc_id;
	fl.fb_id = bufs[idx].fb;
	fl.flags = DRM_MODE_PAGE_FLIP_EVENT;
	if (xioctl(drm_fd, DRM_IOCTL_MODE_PAGE_FLIP, &fl))
		return -1;
	if (wait_flip())
		return -1;
	return 0;
}

static int setup(const char *card)
{
	drm_fd = open(card, O_RDWR);
	if (drm_fd < 0)
		return -1;

	struct drm_mode_card_res res;
	memset(&res, 0, sizeof(res));
	if (xioctl(drm_fd, DRM_IOCTL_MODE_GETRESOURCES, &res))
		goto err;

	uint32_t *conn_ids = calloc(res.count_connectors ? res.count_connectors : 1, 4);
	uint32_t *crtc_ids = calloc(res.count_crtcs ? res.count_crtcs : 1, 4);
	uint32_t *enc_ids = calloc(res.count_encoders ? res.count_encoders : 1, 4);
	uint32_t *fb_ids = calloc(res.count_fbs ? res.count_fbs : 1, 4);
	res.connector_id_ptr = (uint64_t)(uintptr_t)conn_ids;
	res.crtc_id_ptr = (uint64_t)(uintptr_t)crtc_ids;
	res.encoder_id_ptr = (uint64_t)(uintptr_t)enc_ids;
	res.fb_id_ptr = (uint64_t)(uintptr_t)fb_ids;
	if (xioctl(drm_fd, DRM_IOCTL_MODE_GETRESOURCES, &res) || !res.count_crtcs)
		goto err;

	crtc_id = crtc_ids[0];

	int found = 0;
	for (unsigned i = 0; i < res.count_connectors; i++) {
		struct drm_mode_get_connector c;
		memset(&c, 0, sizeof(c));
		c.connector_id = conn_ids[i];
		if (xioctl(drm_fd, DRM_IOCTL_MODE_GETCONNECTOR, &c) || c.connection != 1 || !c.count_modes)
			continue;
		struct drm_mode_modeinfo *ms = calloc(c.count_modes, sizeof(*ms));
		uint32_t *props = calloc(c.count_props ? c.count_props : 1, 4);
		uint64_t *vals = calloc(c.count_props ? c.count_props : 1, 8);
		uint32_t *encs = calloc(c.count_encoders ? c.count_encoders : 1, 4);
		c.modes_ptr = (uint64_t)(uintptr_t)ms;
		c.props_ptr = (uint64_t)(uintptr_t)props;
		c.prop_values_ptr = (uint64_t)(uintptr_t)vals;
		c.encoders_ptr = (uint64_t)(uintptr_t)encs;
		if (xioctl(drm_fd, DRM_IOCTL_MODE_GETCONNECTOR, &c)) {
			free(ms); free(props); free(vals); free(encs);
			continue;
		}
		mode = ms[0];
		conn_id = c.connector_id;
		found = 1;
		free(ms); free(props); free(vals); free(encs);
		break;
	}
	if (!found)
		goto err;

	W = mode.hdisplay;
	H = mode.vdisplay;

	if (make_buf(&bufs[0], &res, crtc_ids) || make_buf(&bufs[1], &res, crtc_ids))
		goto err;

	struct drm_mode_crtc crtc;
	memset(&crtc, 0, sizeof(crtc));
	crtc.crtc_id = crtc_id;
	if (xioctl(drm_fd, DRM_IOCTL_MODE_GETCRTC, &crtc))
		goto err;
	crtc.set_connectors_ptr = (uint64_t)(uintptr_t)&conn_id;
	crtc.count_connectors = 1;
	crtc.fb_id = bufs[0].fb;
	crtc.mode = mode;
	crtc.mode_valid = 1;
	if (xioctl(drm_fd, DRM_IOCTL_MODE_SETCRTC, &crtc))
		goto err;
	cur = 0;

	printf("kms-loop: %ux%u 16bpp double-buffered conn=%u fb=%u/%u ok\n",
	       W, H, conn_id, bufs[0].fb, bufs[1].fb);
	fflush(stdout);
	return 0;
err:
	if (drm_fd >= 0)
		close(drm_fd);
	drm_fd = -1;
	return -1;
}

static void anim_show(uint16_t *px, uint32_t pitch, unsigned idx)
{
	const uint8_t *p = A.data;
	for (unsigned i = 0; i < idx; i++)
		p += A.fr[i].size;
	const uint8_t *end = p + A.fr[idx].size;

	if (A.w == W && A.h == H && pitch == W) {
		uint16_t *dst = px;
		size_t left = (size_t)W * H;
		while (p + 4 <= end && left) {
			uint16_t cnt, val;
			memcpy(&cnt, p, 2);
			memcpy(&val, p + 2, 2);
			p += 4;
			if (cnt > left)
				cnt = left;
			left -= cnt;
			while (cnt--)
				*dst++ = val;
		}
		return;
	}

	unsigned npix = A.w * A.h, x = 0, y = 0;
	size_t done = 0;
	while (p + 4 <= end && done < npix) {
		uint16_t cnt, val;
		memcpy(&cnt, p, 2);
		memcpy(&val, p + 2, 2);
		p += 4;
		while (cnt-- && done < npix) {
			if (y < H && x < W)
				px[(size_t)y * pitch + x] = val;
			done++;
			if (++x == A.w) { x = 0; y++; }
		}
	}
}

static void plasma(uint16_t *px, uint32_t pitch, unsigned t)
{
	for (unsigned y = 0; y < H; y++) {
		uint16_t *row = px + (size_t)y * pitch;
		for (unsigned x = 0; x < W; x++) {
			unsigned r = (x + t) & 0xff, g = (y + t) & 0xff;
			unsigned b = ((x ^ y) + 2 * t) & 0xff;
			row[x] = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
		}
	}
}

int main(int argc, char **argv)
{
	const char *card = argc > 1 ? argv[1] : "/dev/dri/card1";
	const char *anim = argc > 2 ? argv[2] : NULL;

	signal(SIGTERM, on_sig);
	signal(SIGINT, on_sig);

	if (anim && anim_load(anim))
		fprintf(stderr, "kms-loop: cannot load %s, using plasma\n", anim);

	while (!stop) {
		if (setup(card)) {
			fprintf(stderr, "kms-loop: setup failed, retrying\n");
			sleep(2);
			continue;
		}

		unsigned frame = 0;
		while (!stop) {
			int back = cur ^ 1;
			uint16_t *px = bufs[back].map;
			uint32_t pitch = bufs[back].pitch;

			if (A.n) {
				anim_show(px, pitch, frame % A.n);
				usleep(A.fr[frame % A.n].delay * 1000);
			} else {
				plasma(px, pitch, frame);
				usleep(50000);
			}

			if (flip_to(back) == 0)
				cur = back;
			else
				break;
			frame++;
		}
		close(drm_fd);
		drm_fd = -1;
	}
	return 0;
}
