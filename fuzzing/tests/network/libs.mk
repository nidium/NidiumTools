# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file.

CC_FLAGS = -Wall -D_HAVE_SSL_SUPPORT -DNATIVE_DEBUG -DDEBUG -D_DEBUG -fno-rtti -Wno-c++0x-extensions -Wno-invalid-offsetof -Wno-mismatched-tags -O0

INCS = -I ../../../../../../NativeServer/nativejscore/network

LIBS =-L ../../../../../../NativeServer/build/out/Release/obj.target/nativejscore/network/gyp/ -lnativenetwork \
      -L../../../../../../NativeServer/build/third-party/.default/ -lcares -lssl -lz -lrt -ldl

LIBS_HACK=-lcrypto

