INPUT_DIR=./idl
OUTPUT_DIR=./cpp
PARAMS=-- --foo --foobar=1

DOCUMENTATION_DIR = ../../../../Nidium/docs
DOC2IDL=../../doc2idl_transformer.py


CPP_DIRS=\
	$(OUTPUT_DIR)/JSDB.code \
	$(OUTPUT_DIR)/JSConsole.code \
	$(OUTPUT_DIR)/JSImage.code \
	$(OUTPUT_DIR)/JSProcess.code \
	$(OUTPUT_DIR)/JSOS.code \
	$(OUTPUT_DIR)/JSWebSocket.code \
	$(OUTPUT_DIR)/JSWebSocketClient.code \
	$(OUTPUT_DIR)/JSWebGL.code \
	$(OUTPUT_DIR)/JSThread.code \
	$(OUTPUT_DIR)/JSStream.code \
	$(OUTPUT_DIR)/JSSocket.code \
	$(OUTPUT_DIR)/JSModules.code \
	$(OUTPUT_DIR)/JSHTTPServer.code \
	$(OUTPUT_DIR)/JSHTTP.code \
	$(OUTPUT_DIR)/JSGlobal.code \
	$(OUTPUT_DIR)/JSFile.code \
	$(OUTPUT_DIR)/JSFS.code \
	$(OUTPUT_DIR)/JSDocument.code \
	$(OUTPUT_DIR)/JSDebugger.code \
	$(OUTPUT_DIR)/JSDebug.code \
	$(OUTPUT_DIR)/JSCanvas2DContext.code \
	$(OUTPUT_DIR)/JSCanvas.code \
	$(OUTPUT_DIR)/JSAV.code \
	
	#$(OUTPUT_DIR)/JSWindow.code \

all: $(CPP_DIRS)

#$(INPUT_DIR)/JSDB.idl: $(DOCUMENTATION_DIR)/JSDB.cpp.py $(DOC2IDL)
#	$(DOC2IDL) $< $@

$(INPUT_DIR)/%.idl: $(DOCUMENTATION_DIR)/%.cpp.py $(DOC2IDL)
	$(DOC2IDL) $< $@

.PRECIOUS:
	$(INPUT_DIR)/%.idl

include ../common.mk

