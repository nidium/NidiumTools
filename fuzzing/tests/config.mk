# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file.

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

