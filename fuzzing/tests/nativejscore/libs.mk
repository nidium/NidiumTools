# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file.

include ../../../network/libs.mk

CC_FLAGS += '-DNATIVE_VERSION_STR="0.1"' '-DNATIVE_BUILD="10eaca09dfc4b7e4cea06b72a3f2f5b59cb3a22e"' '-DNATIVE_NO_PRIVATE_DIR' '-DNATIVE_NO_FORK' '-D__STDC_LIMIT_MACROS' '-DJSGC_USE_EXACT_ROOTING' 

INCS += -I../../../../../../NativeServer/nativejscore \
		-I../../../../../../NativeServer/third-party/mozilla-central/js/src/dist/include \
		-I../../../../../../NativeServer/third-party/http-parser \
		-I../../../../../../NativeServer/third-party/mozilla-central/dist/include \
		-I../../../../../../NativeServer/third-party/mozilla-central/js/src \
		-I../../../../../../NativeServer/third-party/mozilla-central/nsprpub/dist/include/nspr \
		-I../../../../../../NativeServer/third-party/leveldb/include \
		-include ../../../../../../NativeServer/build/third-party//js-config.h
	
LIBS +=-L ../../../../../../NativeServer/build/out/Release/obj.target/nativejscore/gyp/ -ljsoncpp -lnativejscore \
      -lhttp_parser -lleveldb -ljs_static -lnspr4

