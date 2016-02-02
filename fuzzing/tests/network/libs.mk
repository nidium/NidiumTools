INCS = -I ../../../../../../NativeServer/nativejscore/network
LIBS =-L ../../../../../../NativeServer/build/out/Release/obj.target/nativejscore/network/gyp/ -lnativenetwork \
      -L../../../../../../NativeServer/build/third-party/.default/ -lcares -lssl -lcrypto -lz -lrt -ldl

