# HARMONIA v2.2 Makefile

CC = clang
CFLAGS = -O3 -Wall -Wextra -march=native -flto
LDFLAGS = -flto

TARGET = harmonia_test
TARGET_SIMD = harmonia_simd_test
TARGET_NG = harmonia_ng_test

SOURCES = harmonia.c main.c
SOURCES_SIMD = harmonia_simd.c main.c
SOURCES_NG = harmonia_ng.c
HEADERS = harmonia.h
HEADERS_NG = harmonia_ng.h

all: $(TARGET)

simd: $(TARGET_SIMD)

ng: $(TARGET_NG)

$(TARGET): $(SOURCES) $(HEADERS)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) $(LDFLAGS)

$(TARGET_SIMD): $(SOURCES_SIMD) $(HEADERS)
	$(CC) $(CFLAGS) -o $(TARGET_SIMD) $(SOURCES_SIMD) $(LDFLAGS)

$(TARGET_NG): $(SOURCES_NG) $(HEADERS_NG)
	$(CC) $(CFLAGS) -DHARMONIA_NG_MAIN -o $(TARGET_NG) $(SOURCES_NG) $(LDFLAGS)

harmonia_ng_simd_test: harmonia_ng_simd.c harmonia_ng.h
	$(CC) $(CFLAGS) -DHARMONIA_NG_SIMD_MAIN -o harmonia_ng_simd_test harmonia_ng_simd.c $(LDFLAGS)

debug: CFLAGS = -g -Wall -Wextra -O0
debug: $(TARGET)

clean:
	rm -f $(TARGET) $(TARGET_SIMD) $(TARGET_NG)

test: $(TARGET)
	./$(TARGET) --test

test-simd: $(TARGET_SIMD)
	./$(TARGET_SIMD) --test

test-ng: $(TARGET_NG)
	./$(TARGET_NG)

benchmark: $(TARGET)
	./$(TARGET) --benchmark

benchmark-simd: $(TARGET_SIMD)
	./$(TARGET_SIMD) --benchmark

compare: $(TARGET) $(TARGET_SIMD)
	@echo "=== Standard Version ===" && ./$(TARGET) --benchmark
	@echo ""
	@echo "=== SIMD Version ===" && ./$(TARGET_SIMD) --benchmark

.PHONY: all simd ng clean test test-simd test-ng benchmark benchmark-simd compare debug
