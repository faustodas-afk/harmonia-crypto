/*
 * HARMONIA-NG: Next Generation SIMD-Optimized Hash Function
 *
 * A 256-bit cryptographic hash function based on HARMONIA, redesigned for
 * SIMD vectorization while preserving the golden ratio and Fibonacci
 * mathematical foundations.
 *
 * Version: 1.0
 * Author: Based on HARMONIA by Fausto Dasè
 */

#ifndef HARMONIA_NG_H
#define HARMONIA_NG_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Algorithm parameters */
#define HARMONIA_NG_BLOCK_SIZE  64   /* 512 bits */
#define HARMONIA_NG_DIGEST_SIZE 32   /* 256 bits */
#define HARMONIA_NG_ROUNDS      32

/* Context structure for incremental hashing */
typedef struct {
    uint32_t state_g[8];    /* Golden stream state */
    uint32_t state_c[8];    /* Complementary stream state */
    uint8_t  buffer[64];    /* Partial block buffer */
    size_t   buffer_len;    /* Bytes in buffer */
    uint64_t total_len;     /* Total message length in bytes */
} harmonia_ng_ctx;

/*
 * Initialize a HARMONIA-NG context.
 */
void harmonia_ng_init(harmonia_ng_ctx *ctx);

/*
 * Update context with data.
 */
void harmonia_ng_update(harmonia_ng_ctx *ctx, const uint8_t *data, size_t len);

/*
 * Finalize and produce digest.
 */
void harmonia_ng_final(harmonia_ng_ctx *ctx, uint8_t *digest);

/*
 * One-shot hash function.
 */
void harmonia_ng(const uint8_t *data, size_t len, uint8_t *digest);

/*
 * One-shot hash with hexadecimal output.
 */
void harmonia_ng_hex(const uint8_t *data, size_t len, char *hex_out);

/*
 * Self-test function.
 * Returns 0 on success, non-zero on failure.
 */
int harmonia_ng_self_test(void);

#ifdef __cplusplus
}
#endif

#endif /* HARMONIA_NG_H */
