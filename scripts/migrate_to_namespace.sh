#!/bin/bash

#SRC_DIR=./src
SRC_DIR=.

find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/#include \"JS\/Native/#include \"Binding\/Native/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NativeJSExposer</Nidium::Binding::JSExposer</g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NativeJSObjectMapper</Nidium::Binding::JSObjectMapper</g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NativeJSObjectMapper(/JSObjectMapper(/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/public NativeJSAsyncHandler/public Nidium::Binding::JSAsyncHandler/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NativeJSAsyncHandler(/JSAsyncHandler(/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/#include \"NativeJSExposer\.h/#include \"JSExposer.h/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/#include \"NativeJSHttp\.h/#include \"JSHttp.h/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/JSNATIVE_PROLOGUE/NIDIUM_JS_PROLOGUE/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_CHECK_ARGS/NIDIUM_JS_CHECK_ARGS/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_REGISTER_MODULE/NIDIUM_JS_REGISTER_MODULE/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/JSOBJ_SET_PROP/NIDIUM_JSOBJ_SET_PROP/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/JS_INITOPT/NIDIUM_JS_INIT_OPT/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/JSGET_OPT/NIDIUM_JS_GET_OPT/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_JS_SETTER/NIDIUM_JS_SETTER/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_JS_GETTER/NIDIUM_JS_GETTER/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_JS_STUBGETTER/NIDIUM_JS_STUBGETTER/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_PSG/NIDIUM_JS_PSG/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_PSS/NIDIUM_JS_PSS/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NATIVE_PSGS/NIDIUM_JS_PSGS/g" {} \;

find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/<JS\/NativeJSExposer\.h/<Binding\/JSexposer\.h/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NativeJSEvents/Nidium::Binding::JSEvents/g" {} \;
find $SRC_DIR \( -name "*.cpp" -o -name "*.h" \) -exec sed -i "s/NativeJSObjectBuilder/Nidium::Binding::JSObjectBuilder/g" {} \;

