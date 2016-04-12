/*
   Copyright 2016 Nidium Inc. All rights reserved.
   Use of this source code is governed by a MIT license
   that can be found in the LICENSE file.
*/

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
	unsigned char * out = (unsigned char * ) malloc(size);
	char * src = (char *) data;
	base64_decode(out, src, size);

	free(out);

	return 0;
}

}

