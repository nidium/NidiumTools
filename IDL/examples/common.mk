PROG=idl2cpp_transformer
PYWIDL=pywidl
CLANG-FORMATSTYLE=../../_clang-format
CLANGFORMAT=/opt/clang-3.7.0/bin/clang-format -style=file
TEMPLATE_FILES=\
        ../../idl2cpp_templates/base_class.cpp.tpl \
        ../../idl2cpp_templates/base_class.h.tpl \
        ../../idl2cpp_templates/dict_class.h.tpl

.PHONY: clean

clean:
	rm -rf *.pyc \
	$(shell find $(OUTPUT_DIR) -name '*.code' -o -name '*_code')