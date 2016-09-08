INPUT_DIR=./idl
OUTPUT_DIR=./cpp
PARAMS=-- --foo --foobar=1

FRAGMENT_IDL_FILE=$(INPUT_DIR)/fragment.idl
FRAGMENT_CPP_DIR=$(OUTPUT_DIR)/fragment.code

HELLO_IDL_FILE=$(INPUT_DIR)/hello.idl
HELLO_CPP_DIR=$(OUTPUT_DIR)/hello.code

all: $(FRAGMENT_CPP_DIR) $(HELLO_CPP_DIR)

include ../common.mk

$(OUTPUT_DIR)/%.code: $(INPUT_DIR)/%.idl ../../$(PROG).py $(TEMPLATE_FILES) $(CLANG-FORMATSTYLE)
	@rm -rf $@
	@$(PYWIDL) -n -o $@ -t $(PROG) $< $(PARAMS)
	@$(CLANGFORMAT) -i `cat $@`

