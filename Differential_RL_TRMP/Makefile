CC=gcc
CFLAGS=-O2 -Wall -Wno-unused-but-set-variable -Wno-unused-variable
SRC=src/es_drl.c src/trmp_core.c src/destroy_repair.c
all: out/es_drl out/es_base
out/es_drl: $(SRC) src/trmp.h
	@mkdir -p out
	$(CC) $(CFLAGS) -o $@ $(SRC) -lm
out/es_base: es_pre_sfFIN.c
	@mkdir -p out
	$(CC) -O2 -o $@ $< -lm
test: all
	bash tests/test_equiv.sh
