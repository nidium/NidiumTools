
$(RUN_DIR)/$(LOCKFILE): $(BIN_FILE)
	@echo $@
	@cd $(RUN_DIR) && \
	touch $(LOCKFILE) && \
		echo remove $(RUN_DIR)/$(LOCKFILE) to stop && \
		../$(BIN_FILE) ../$(COR_DIR) -jobs=$(JOBS) -workers=$(WORKERS)
	@rm -rf $(LOCKFILE)

$(BIN_FILE): $(OBJ_FILE) $(DEP_DIR)/Fuzzer
	@echo $@
	@$(CC) -o $@ -g -fsanitize=address $< $(LIBSTDCPP) -Wl,--whole-archive $(LIBS) -Wl,-no-whole-archive $(DEP_DIR)/Fuzzer/Fuzzer*.o $(LIBS_HACK)
	@chmod +x $@

$(OBJ_FILE): $(SRC_FILE)
	@echo $@
	@$(CC) -o $@ -c -fsanitize=address $(COV_FLAGS) $(CC_FLAGS) -c -std=c++11 $(INCS) -g $<

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

