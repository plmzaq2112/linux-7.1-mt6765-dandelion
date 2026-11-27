#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

int main(int argc, char **argv)
{
	int wr, bits, fd;
	unsigned long phys, val, page, off, r;
	void *m;
	volatile unsigned char *p;

	if (argc < 3) {
		fprintf(stderr, "usage: %s r|w <phys> [val] [bits]\n", argv[0]);
		return 2;
	}
	wr = argv[1][0] == 'w';
	phys = strtoul(argv[2], NULL, 0);
	val = (argc > 3) ? strtoul(argv[3], NULL, 0) : 0;
	bits = (argc > 4) ? atoi(argv[4]) : 32;
	page = phys & ~0xFFFUL;
	off = phys - page;

	fd = open("/dev/mem", O_RDWR | O_SYNC);
	if (fd < 0) {
		perror("open /dev/mem");
		return 1;
	}
	m = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page);
	if (m == MAP_FAILED) {
		perror("mmap");
		return 1;
	}
	p = (volatile unsigned char *)m + off;
	if (wr) {
		if (bits == 32)
			*(volatile unsigned int *)p = (unsigned int)val;
		else
			*(volatile unsigned long *)p = val;
	}
	r = (bits == 32) ? *(volatile unsigned int *)p
			 : *(volatile unsigned long *)p;
	printf("%s 0x%lx = 0x%0*lx\n", wr ? "wr" : "rd", phys,
	       bits / 4, r);
	return 0;
}
