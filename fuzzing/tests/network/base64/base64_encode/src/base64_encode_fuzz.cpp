#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/types.h>

#include <ape_base64.h>

extern "C" {

unsigned long _ape_seed = 12315454545;
int ape_running = 0;

int LLVMFuzzerTestOneInput( const uint8_t * data, size_t size )
{
	size_t len = size;
	unsigned char * src = (unsigned char *) data;
	char * dst = base64_encode(src, len);

	free(dst);

	return 0;
}

}

