SHELL:=/bin/bash

# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file.

export SHELLOPTS:=errexit:pipefail

FILTER= NativeJSDebugger.cpp.py

#YMMV: this works for me
NIDIUM_DIR=/data/Development/nidium
TOOLS_DIR=$(NIDIUM_DIR)/NativeTools
SERVER_DIR=$(NIDIUM_DIR)/NativeServer
STUDIO_DIR=$(NIDIUM_DIR)/NativeStudio

SERVER_JSCORE_DIR=$(SERVER_DIR)/nativejscore
STUDIO_JSCORE_DIR=$(STUDIO_DIR)/nativejscore
FRAMEWORK_DIR=$(STUDIO_DIR)/framework
REDIS_DIR=$(SERVER_DIR)/modules/NativeRedis
DOCS_DIR=$(FRAMEWORK_DIR)/dist/private/apps/documentation/static/js/docs_api
AUTO_SUITE=var/js/tests/autotests/auto_suites.js
RAW_DOC=var/rawdoc/*.*.py

FILE=$(STUDIO_JSCORE_DIR)

DOKUMENTOR=$(TOOLS_DIR)/src/dokumentor.py

DOCS =	$(DOCS_DIR)/framework.js \
		$(DOCS_DIR)/studio.js \
		$(DOCS_DIR)/server.js \
		$(DOCS_DIR)/jscore.js \
#		$(DOCS_DIR)/redis.js

TESTS = $(FRAMEWORK_DIR)/$(AUTO_SUITE) \
		$(STUDIO_DIR)/$(AUTO_SUITE) \
		$(SERVER_DIR)/$(AUTO_SUITE) \
		$(STUDIO_JSCORE_DIR)/$(AUTO_SUITE) \
		#$(SERVER_JSCORE_DIR)/$(AUTO_SUITE) \
#		$(REDIS_DIR)/$(AUTO_SUITE) \

$(DOCS_DIR)/framework.js :				$(shell ls $(FRAMEWORK_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) json $(dir $<) > $@
	@sed -i '1s;^;var docs = ;' $@
$(DOCS_DIR)/studio.js :					$(shell ls $(STUDIO_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) json $(dir $<) > $@
	@sed -i '1s;^;var docs = ;' $@
$(DOCS_DIR)/server.js :					$(shell ls $(STUDIO_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) json $(dir $<) > $@
	@sed -i '1s;^;var docs = ;' $@
$(DOCS_DIR)/jscore.js :					$(shell ls $(SERVER_JSCORE_DIR)/$(RAW_DOC)) \
#										$(shell ls $(STUDIO_JSCORE_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) json $(dir $<) > $@
	@sed -i '1s;^;var docs = ;' $@
#$(DOCS_DIR)/redis.js :					$(shell ls $(REDIS_DIR)/$(RAW_DOC))
#	@$(DOKUMENTOR) json $(dir $<) > $@
#	@sed -i '1s;^;var docs = ;' $@

$(FRAMEWORK_DIR)/$(AUTO_SUITE):			$(shell ls $(FRAMEWORK_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) exampletest $(dir $<) > $@
$(STUDIO_DIR)/$(AUTO_SUITE) :			$(shell ls $(STUDIO_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) exampletest $(dir $<) > $@
$(SERVER_DIR)/$(AUTO_SUITE) :			$(shell ls $(SERVER_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) exampletest $(dir $<) > $@
$(SERVER_JSCORE_DIR)/$(AUTO_SUITE) :	$(shell ls $(SERVER_JSCORE_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) exampletest $(dir $<) > $@
$(STUDIO_JSCORE_DIR)/$(AUTO_SUITE) :	$(shell ls $(STUDIO_JSCORE_DIR)/$(RAW_DOC))
	@$(DOKUMENTOR) exampletest $(dir $<) > $@
#$(REDIS_DIR)/$(AUTO_SUITE) :			$(shell ls $(REDIS_DIR)/$(RAW_DOC))
#	@$(DOKUMENTOR) exampletest $(dir $<) > $@

all: $(DOCS) $(TESTS)

.PHONY: clean

clean:
	@rm -rf $(DOCS) $(TESTS)

