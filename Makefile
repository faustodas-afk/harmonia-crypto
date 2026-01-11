# HARMONIA v2.2 Makefile

CC = clang
CFLAGS = -O3 -Wall -Wextra -march=native -flto
LDFLAGS = -flto

TARGET = harmonia_test
TARGET_SIMD = harmonia_simd_test

SOURCES = harmonia.c main.c
SOURCES_SIMD = harmonia_simd.c main.c
HEADERS = harmonia.h

all: $(TARGET)

simd: $(TARGET_SIMD)

$(TARGET): $(SOURCES) $(HEADERS)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES) $(LDFLAGS)

$(TARGET_SIMD): $(SOURCES_SIMD) $(HEADERS)
	$(CC) $(CFLAGS) -o $(TARGET_SIMD) $(SOURCES_SIMD) $(LDFLAGS)

debug: CFLAGS = -g -Wall -Wextra -O0
debug: $(TARGET)

clean:
	rm -f $(TARGET) $(TARGET_SIMD)

test: $(TARGET)
	./$(TARGET) --test

test-simd: $(TARGET_SIMD)
	./$(TARGET_SIMD) --test

benchmark: $(TARGET)
	./$(TARGET) --benchmark

benchmark-simd: $(TARGET_SIMD)
	./$(TARGET_SIMD) --benchmark

compare: $(TARGET) $(TARGET_SIMD)
	@echo "=== Standard Version ===" && ./$(TARGET) --benchmark
	@echo ""
	@echo "=== SIMD Version ===" && ./$(TARGET_SIMD) --benchmark

.PHONY: all simd clean test test-simd benchmark benchmark-simd compare debug
