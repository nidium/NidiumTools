CC_FLAGS = -Wall -D_HAVE_SSL_SUPPORT -DNATIVE_DEBUG -DDEBUG -D_DEBUG -fno-rtti -Wno-c++0x-extensions -Wno-invalid-offsetof -Wno-mismatched-tags -O0

INCS = -I ../../../../../../NativeServer/nativejscore/network

LIBS =-L ../../../../../../NativeServer/build/out/Release/obj.target/nativejscore/network/gyp/ -lnativenetwork \
      -L../../../../../../NativeServer/build/third-party/.default/ -lcares -lssl -lz -lrt -ldl

LIBS_HACK=-lcrypto

