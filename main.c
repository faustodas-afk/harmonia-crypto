/*
 * HARMONIA v2.2 - Test and Benchmark Driver
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "harmonia.h"

/* Optional: OpenSSL for comparison */
#ifdef USE_OPENSSL
#include <openssl/sha.h>
#endif

/* High-resolution timer */
static double get_time_sec(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

/* Benchmark function */
static void benchmark(const char *name, size_t data_size, int iterations) {
    uint8_t *data;
    uint8_t digest[32];
    double start, elapsed;
    double throughput;
    int i;

    data = (uint8_t*)malloc(data_size);
    if (!data) {
        printf("Memory allocation failed\n");
        return;
    }
    memset(data, 'x', data_size);

    /* Warmup */
    for (i = 0; i < 10; i++) {
        harmonia(data, data_size, digest);
    }

    /* Benchmark */
    start = get_time_sec();
    for (i = 0; i < iterations; i++) {
        harmonia(data, data_size, digest);
    }
    elapsed = get_time_sec() - start;

    throughput = (data_size * iterations) / elapsed / (1024.0 * 1024.0);

    printf("  %-20s %8zu bytes x %6d = %8.2f MB/s  (%.4f ms/hash)\n",
           name, data_size, iterations, throughput,
           elapsed / iterations * 1000);

    free(data);
}

#ifdef USE_OPENSSL
static void benchmark_sha256(const char *name, size_t data_size, int iterations) {
    uint8_t *data;
    uint8_t digest[32];
    double start, elapsed;
    double throughput;
    int i;

    data = (uint8_t*)malloc(data_size);
    if (!data) return;
    memset(data, 'x', data_size);

    /* Warmup */
    for (i = 0; i < 10; i++) {
        SHA256(data, data_size, digest);
    }

    /* Benchmark */
    start = get_time_sec();
    for (i = 0; i < iterations; i++) {
        SHA256(data, data_size, digest);
    }
    elapsed = get_time_sec() - start;

    throughput = (data_size * iterations) / elapsed / (1024.0 * 1024.0);

    printf("  %-20s %8zu bytes x %6d = %8.2f MB/s\n",
           name, data_size, iterations, throughput);

    free(data);
}
#endif

static void run_benchmarks(void) {
    printf("\n");
    printf("============================================================\n");
    printf("HARMONIA v%s Performance Benchmark\n", HARMONIA_VERSION);
    printf("============================================================\n");
    printf("\n");

    printf("HARMONIA:\n");
    benchmark("Small (64 B)",     64,     100000);
    benchmark("Medium (1 KB)",    1024,   50000);
    benchmark("Large (10 KB)",    10240,  5000);
    benchmark("XL (100 KB)",      102400, 500);
    benchmark("XXL (1 MB)",       1048576, 50);

#ifdef USE_OPENSSL
    printf("\nSHA-256 (OpenSSL):\n");
    benchmark_sha256("Small (64 B)",     64,     100000);
    benchmark_sha256("Medium (1 KB)",    1024,   50000);
    benchmark_sha256("Large (10 KB)",    10240,  5000);
    benchmark_sha256("XL (100 KB)",      102400, 500);
    benchmark_sha256("XXL (1 MB)",       1048576, 50);
#endif

    printf("\n============================================================\n");
}

static void print_usage(const char *prog) {
    printf("HARMONIA v%s - Cryptographic Hash Function\n\n", HARMONIA_VERSION);
    printf("Usage:\n");
    printf("  %s --test        Run self-test\n", prog);
    printf("  %s --benchmark   Run performance benchmark\n", prog);
    printf("  %s <string>      Hash a string\n", prog);
    printf("  %s               Run self-test (default)\n", prog);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        return harmonia_self_test() ? 0 : 1;
    }

    if (strcmp(argv[1], "--test") == 0 || strcmp(argv[1], "-t") == 0) {
        return harmonia_self_test() ? 0 : 1;
    }

    if (strcmp(argv[1], "--benchmark") == 0 || strcmp(argv[1], "-b") == 0) {
        harmonia_self_test();
        run_benchmarks();
        return 0;
    }

    if (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
        print_usage(argv[0]);
        return 0;
    }

    /* Hash the argument */
    {
        char hex[65];
        harmonia_hex((const uint8_t*)argv[1], strlen(argv[1]), hex);
        printf("%s\n", hex);
    }

    return 0;
}
