CC=clang
LOCKFILE=run.lock

SRC_DIR=./src
TMP_DIR=./tmp
RUN_DIR=./run
COR_DIR=./corpus
DEP_DIR=../../../deps

LIBSTDCPP=-L /opt/clang-3.7.0/lib -lstdc++

JOBS=100
WORKERS = $(shell grep bogomips /proc/cpuinfo |wc -l)

COV_FLAGS=-fsanitize-coverage=edge,indirect-calls,8bit-counters

