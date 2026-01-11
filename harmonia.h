/*
 * HARMONIA v2.2 - Cryptographic Hash Function
 *
 * A 256-bit hash function based on the Golden Ratio and Temporal Quasicrystals
 *
 * Author: [Your Name]
 * License: MIT
 */

#ifndef HARMONIA_H
#define HARMONIA_H

#include <stdint.h>
#include <stddef.h>

#define HARMONIA_BLOCK_SIZE   64   /* 512 bits */
#define HARMONIA_DIGEST_SIZE  32   /* 256 bits */
#define HARMONIA_VERSION      "2.2"

/* Hash context for incremental hashing */
typedef struct {
    uint32_t state_g[8];      /* Golden stream state */
    uint32_t state_c[8];      /* Complementary stream state */
    uint8_t  buffer[64];      /* Input buffer */
    uint64_t total_len;       /* Total bytes processed */
    size_t   buffer_len;      /* Bytes in buffer */
} harmonia_ctx;

/* Initialize context */
void harmonia_init(harmonia_ctx *ctx);

/* Update context with data */
void harmonia_update(harmonia_ctx *ctx, const uint8_t *data, size_t len);

/* Finalize and get digest */
void harmonia_final(harmonia_ctx *ctx, uint8_t *digest);

/* One-shot hash function */
void harmonia(const uint8_t *data, size_t len, uint8_t *digest);

/* One-shot hash returning hex string (must provide 65-byte buffer) */
void harmonia_hex(const uint8_t *data, size_t len, char *hex_digest);

/* Self-test function */
int harmonia_self_test(void);

#endif /* HARMONIA_H */
