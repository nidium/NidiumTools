#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/types.h>

#include <NativeUtils.h>

extern "C" {

unsigned long _ape_seed = 12315454545;
int ape_running = 0;


int LLVMFuzzerTestOneInput( const uint8_t * data, size_t size )
{
	char * ua = (char *) calloc(size + 1, sizeof(char));
	strcat(ua, (char*) data);
	NativeUserAgentUtils::getOS(ua);
	free(ua);

	return 0;
}

}

