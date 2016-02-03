#ls -l ../corpus/|cut -d'F' -f1|cut -d' ' -f5|sort|uniq|tail -n 1

$(RUN_DIR)/$(LOCKFILE): $(BIN_FILE)
	@echo $@
	@echo "cd $(RUN_DIR); ../$(BIN_FILE) ../$(COR_DIR) -jobs=$(JOBS) -workers=$(WORKERS) -max_len=250"

$(BIN_FILE): $(OBJ_FILE) $(DEP_DIR)/Fuzzer
	@echo $@
	@$(CC) -o $@ -g -fsanitize=address -fno-omit-frame-pointer $< $(LIBSTDCPP) -Wl,--whole-archive $(LIBS) -Wl,-no-whole-archive $(DEP_DIR)/Fuzzer/Fuzzer*.o $(LIBS_HACK)
	@chmod +x $@

$(OBJ_FILE): $(SRC_FILE)
	@echo $@
	@$(CC) -o $@ -c -fsanitize=address -fno-omit-frame-pointer $(COV_FLAGS) $(CC_FLAGS) -c -std=c++11 $(INCS) -g $<

$(DEP_DIR)/Fuzzer:
	@echo $@
	@mkdir -p $(DEP_DIR)/Fuzzer/ && \
	cd $(DEP_DIR)/Fuzzer && \
	svn co http://llvm.org/svn/llvm-project/llvm/trunk/lib/Fuzzer && \
	clang -c -g -O2 $(LIBSTDCPP) -std=c++11 Fuzzer/*.cpp -IFuzzer

.PHONY: clean

clean:
	@echo cleaning
	@rm -rf $(BIN_FILE) $(OBJ_FILE) $(RUN_DIR)/*.log

