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

