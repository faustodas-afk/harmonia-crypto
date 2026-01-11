/*
 * HARMONIA v2.2 - Cryptographic Hash Function
 *
 * A 256-bit hash function based on the Golden Ratio and Temporal Quasicrystals
 * Inspired by: Dumitrescu et al., Nature 607, 463-467 (2022)
 *
 * Author: [Your Name]
 * License: MIT
 */

#include "harmonia.h"
#include <string.h>
#include <stdio.h>

/* ============================================================================
 * CONSTANTS
 * ============================================================================ */

/* Golden ratio derived constants (Hamming weight ~16) */
static const uint32_t PHI_CONSTANTS[16] = {
    0x9E37605A, 0xDAC1E0F2, 0xF287A338, 0xFA8CFC04,
    0xFD805AA6, 0xCCF29760, 0xFF8184C3, 0xFF850D11,
    0xCC32476B, 0x98767486, 0xFFF82080, 0x30E4E2F3,
    0xFCC3ACC1, 0xE5216F38, 0xF30E4CC9, 0x948395F6
};

/* Reciprocal constants */
static const uint32_t RECIPROCAL_CONSTANTS[16] = {
    0x7249217F, 0x5890EB7C, 0x4786B47C, 0x4C51DBE8,
    0x4E4DA61B, 0x4F76650C, 0x4F2F1A2A, 0x4F6CE289,
    0x4F1ADF40, 0x4E84BABC, 0x4F22D993, 0x497FA704,
    0x4F514F19, 0x4E8F43B8, 0x508E2FD9, 0x4B5F94A4
};

/* Fibonacci sequence */
static const uint32_t FIBONACCI[12] = {
    1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144
};

/* Fibonacci word for round scheduling (A=1, B=0) */
/* "ABAABABAABAABABAABABAABAABABAABAABABAABABAABAABABAABAABABAABABAAB" */
static const uint8_t FIBONACCI_WORD[64] = {
    1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,
    1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,
    1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,
    0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1
};

/* Pre-computed quasicrystal rotation table [66][10] */
static const uint8_t QUASICRYSTAL_ROTATIONS[66][10] = {
    {14, 11, 5, 4, 11, 13, 11, 5, 3, 10},
    {5, 11, 13, 11, 4, 5, 11, 13, 11, 5},
    {20, 6, 11, 2, 5, 21, 7, 10, 1, 5},
    {14, 18, 7, 7, 17, 14, 18, 9, 9, 15},
    {6, 12, 18, 1, 3, 10, 9, 16, 2, 6},
    {16, 2, 6, 14, 13, 18, 6, 11, 10, 11},
    {19, 15, 14, 17, 3, 12, 12, 16, 2, 12},
    {16, 20, 6, 12, 4, 7, 6, 16, 8, 9},
    {16, 1, 6, 6, 21, 11, 10, 5, 5, 4},
    {14, 16, 16, 5, 12, 19, 11, 10, 21, 2},
    {11, 16, 14, 9, 17, 20, 8, 19, 10, 10},
    {18, 3, 10, 13, 13, 1, 20, 20, 18, 4},
    {4, 5, 11, 13, 11, 5, 4, 11, 13, 11},
    {13, 10, 3, 5, 12, 13, 11, 4, 5, 11},
    {12, 3, 5, 19, 5, 11, 2, 5, 20, 7},
    {5, 5, 20, 15, 18, 7, 6, 18, 14, 18},
    {20, 21, 21, 5, 14, 18, 1, 2, 8, 11},
    {3, 20, 15, 16, 21, 4, 16, 14, 17, 5},
    {10, 6, 10, 1, 16, 13, 14, 1, 15, 13},
    {21, 17, 18, 11, 5, 11, 14, 2, 2, 12},
    {20, 17, 2, 17, 18, 19, 15, 7, 13, 6},
    {21, 1, 7, 7, 5, 18, 19, 19, 13, 1},
    {11, 19, 2, 19, 15, 17, 3, 20, 8, 7},
    {13, 10, 16, 20, 3, 8, 18, 8, 5, 2},
    {12, 13, 10, 4, 5, 11, 13, 11, 4, 5},
    {2, 6, 12, 13, 10, 3, 6, 12, 13, 10},
    {5, 18, 4, 13, 3, 5, 19, 5, 12, 2},
    {1, 16, 17, 5, 4, 20, 15, 18, 6, 6},
    {17, 1, 17, 20, 21, 20, 3, 15, 19, 1},
    {17, 13, 15, 5, 1, 16, 15, 20, 2, 18},
    {1, 10, 19, 8, 3, 14, 4, 17, 12, 11},
    {9, 15, 3, 4, 18, 16, 6, 10, 15, 15},
    {2, 21, 3, 12, 5, 8, 19, 14, 11, 3},
    {1, 15, 17, 1, 14, 14, 21, 15, 19, 12},
    {2, 12, 20, 13, 13, 2, 5, 14, 19, 18},
    {15, 10, 19, 10, 15, 10, 21, 3, 7, 2},
    {10, 3, 6, 12, 13, 10, 3, 6, 12, 13},
    {12, 13, 9, 2, 7, 12, 13, 10, 3, 6},
    {2, 15, 4, 5, 18, 3, 13, 3, 5, 19},
    {16, 2, 1, 2, 16, 17, 4, 3, 21, 15},
    {21, 21, 19, 16, 2, 19, 20, 20, 18, 2},
    {9, 12, 7, 18, 12, 13, 7, 3, 17, 14},
    {21, 3, 14, 5, 13, 20, 7, 21, 17, 6},
    {2, 18, 20, 6, 10, 9, 8, 18, 13, 1},
    {6, 3, 15, 8, 1, 19, 3, 14, 15, 20},
    {6, 1, 5, 8, 8, 5, 1, 6, 1, 15},
    {2, 7, 17, 21, 18, 18, 14, 6, 2, 12},
    {4, 4, 9, 9, 8, 15, 6, 19, 4, 21},
    {7, 12, 13, 10, 2, 6, 12, 13, 10, 3},
    {9, 1, 7, 12, 13, 9, 2, 7, 12, 13},
    {4, 4, 16, 1, 15, 4, 5, 17, 2, 14},
    {3, 4, 17, 16, 2, 1, 2, 16, 17, 3},
    {18, 12, 7, 1, 1, 19, 15, 4, 20, 21},
    {12, 19, 9, 7, 14, 9, 18, 12, 12, 9},
    {3, 17, 21, 21, 1, 11, 8, 15, 20, 5},
    {21, 17, 13, 7, 21, 21, 4, 5, 14, 12},
    {3, 6, 1, 1, 15, 3, 14, 1, 14, 16},
    {15, 21, 15, 14, 1, 17, 15, 1, 14, 1},
    {17, 13, 5, 21, 8, 9, 20, 3, 16, 16},
    {2, 3, 8, 18, 18, 13, 2, 6, 11, 1},
    {13, 9, 1, 7, 12, 13, 9, 2, 7, 12},
    {8, 13, 13, 8, 1, 8, 13, 13, 9, 2},
    {15, 2, 17, 4, 4, 16, 1, 15, 4, 4},
    {18, 15, 20, 4, 5, 17, 16, 1, 2, 3},
    {12, 5, 2, 17, 11, 8, 2, 1, 18, 14},
    {6, 21, 1, 14, 20, 8, 5, 17, 10, 19}
};

/* PHI for penrose_index calculation (fixed-point approximation) */
#define PHI_FIXED 0x19E3779B9ULL  /* φ * 2^32 */

/* ============================================================================
 * PRIMITIVE OPERATIONS
 * ============================================================================ */

#define ROTR32(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define ROTL32(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

static inline uint8_t quasicrystal_rotation(int round_num, int state_index) {
    return QUASICRYSTAL_ROTATIONS[round_num][state_index];
}

static inline uint32_t penrose_index(int n) {
    /* PHI ≈ 1.618, PHI^2 ≈ 2.618 */
    uint32_t x = (uint32_t)((n * 1.6180339887498948) * 1.0) & 0xFF;
    uint32_t y = (uint32_t)((n * 1.6180339887498948 * 1.6180339887498948)) & 0xFF;
    return (x ^ y) & 0x1F;
}

/* ============================================================================
 * MIXING FUNCTIONS
 * ============================================================================ */

static void mix_golden(uint32_t *a, uint32_t *b, uint32_t k, int r, int i) {
    uint32_t rot1, rot2, mix;
    uint32_t va = *a, vb = *b;  /* Work on copies to handle a==b case */

    /* Phase 1 */
    rot1 = quasicrystal_rotation(r, i);
    va = ROTR32(va, rot1);
    va = (va + vb);
    va ^= k;

    /* Phase 2 */
    rot2 = quasicrystal_rotation(r + 1, i + 1);
    vb = ROTL32(vb, rot2);
    vb ^= va;
    vb = (vb + k);

    /* Phase 3: Non-linear mixing */
    mix = (va * 3) ^ (vb * 5);
    va ^= (mix >> 11);
    vb ^= (mix << 7);

    *a = va;
    *b = vb;
}

static void mix_complementary(uint32_t *a, uint32_t *b, uint32_t k, int r, int i) {
    uint32_t va = *a, vb = *b;  /* Work on copies to handle a==b case */

    va ^= vb;
    va = ROTL32(va, quasicrystal_rotation(r, i));
    va = (va + (k >> 1));

    vb = (vb + va);
    vb = ROTR32(vb, quasicrystal_rotation(r + 1, i + 1));
    vb ^= (k >> 1);

    *a = va;
    *b = vb;
}

static void exchange_quasi_periodic(uint32_t *g, uint32_t *c, int r, int round_type) {
    uint32_t temp;
    int i, pi;

    if (round_type == 1) {  /* Type A - intensive */
        for (i = 0; i < 8; i++) {
            pi = penrose_index(r + i);
            if (pi % 3 == 0) {
                temp = g[i] ^ c[i];
                g[i] += (temp >> 8);
                c[i] += (temp & 0xFF00);
            }
        }
    } else {  /* Type B - light (edges only) */
        temp = g[0] ^ c[7];
        g[0] ^= (temp >> 16);
        c[7] ^= (temp & 0xFFFF);
    }
}

static void edge_protection(uint32_t *s, int r) {
    uint32_t rot_l, rot_r, fib_const, interaction;

    /* Left edge */
    rot_l = quasicrystal_rotation(r, 0);
    s[0] = ROTR32(s[0], rot_l);
    fib_const = FIBONACCI[r % 12] * 0x9E3779B9U;
    s[0] ^= fib_const;

    /* Right edge */
    rot_r = quasicrystal_rotation(r, 7);
    s[7] = ROTL32(s[7], rot_r);
    s[7] ^= ~fib_const;

    /* Edge interaction */
    interaction = (s[0] ^ s[7]) >> 16;
    s[0] += interaction;
    s[7] += interaction;
}

/* ============================================================================
 * CORE FUNCTIONS
 * ============================================================================ */

static void compress(const uint8_t *block, uint32_t *state_g, uint32_t *state_c) {
    uint32_t words[64];
    uint32_t g[8], c[8];
    int r, i, j, idx;
    uint32_t w1, w2, w3, w4, rot1, rot2, shift;

    /* Parse block into 16 words (big-endian) */
    for (i = 0; i < 16; i++) {
        words[i] = ((uint32_t)block[i*4] << 24) |
                   ((uint32_t)block[i*4+1] << 16) |
                   ((uint32_t)block[i*4+2] << 8) |
                   ((uint32_t)block[i*4+3]);
    }

    /* Expand to 64 words */
    for (idx = 16; idx < 64; idx++) {
        w1 = words[idx - 2];
        w2 = words[idx - 7];
        w3 = words[idx - 15];
        w4 = words[idx - 16];

        rot1 = quasicrystal_rotation(idx, 0);
        rot2 = quasicrystal_rotation(idx, 1);
        shift = (penrose_index(idx) & 0xF) + 1;

        words[idx] = ROTR32(w1, rot1) ^ ROTL32(w2, rot2) ^ (w3 >> shift) ^ w4;
    }

    /* Initialize working state */
    memcpy(g, state_g, 32);
    memcpy(c, state_c, 32);

    /* 64 rounds */
    for (r = 0; r < 64; r++) {
        int round_type = FIBONACCI_WORD[r];

        i = r & 7;
        j = (r + FIBONACCI[r % 12]) & 7;

        if (round_type == 1) {  /* Golden round */
            mix_golden(&g[i], &g[j], PHI_CONSTANTS[r & 15], r, i);
            g[i] += words[r];

            mix_golden(&c[i], &c[j], RECIPROCAL_CONSTANTS[r & 15], r, i);
            c[j] += words[63 - r];
        } else {  /* Complementary round */
            mix_complementary(&g[i], &g[j], PHI_CONSTANTS[r & 15], r, i);
            g[j] += words[r];

            mix_complementary(&c[j], &c[i], RECIPROCAL_CONSTANTS[r & 15], r, j);
            c[i] += words[63 - r];
        }

        exchange_quasi_periodic(g, c, r, round_type);

        /* Edge protection every 8 rounds */
        if ((r & 7) == 7) {
            edge_protection(g, r);
            edge_protection(c, r);
        }
    }

    /* Davies-Meyer construction */
    for (i = 0; i < 8; i++) {
        state_g[i] += g[i];
        state_c[i] += c[i];
    }
}

/* ============================================================================
 * PUBLIC API
 * ============================================================================ */

void harmonia_init(harmonia_ctx *ctx) {
    int i;
    for (i = 0; i < 8; i++) {
        ctx->state_g[i] = PHI_CONSTANTS[i];
        ctx->state_c[i] = RECIPROCAL_CONSTANTS[i];
    }
    ctx->total_len = 0;
    ctx->buffer_len = 0;
}

void harmonia_update(harmonia_ctx *ctx, const uint8_t *data, size_t len) {
    ctx->total_len += len;

    /* If we have buffered data, try to complete a block */
    if (ctx->buffer_len > 0) {
        size_t needed = 64 - ctx->buffer_len;
        if (len >= needed) {
            memcpy(ctx->buffer + ctx->buffer_len, data, needed);
            compress(ctx->buffer, ctx->state_g, ctx->state_c);
            data += needed;
            len -= needed;
            ctx->buffer_len = 0;
        } else {
            memcpy(ctx->buffer + ctx->buffer_len, data, len);
            ctx->buffer_len += len;
            return;
        }
    }

    /* Process complete blocks */
    while (len >= 64) {
        compress(data, ctx->state_g, ctx->state_c);
        data += 64;
        len -= 64;
    }

    /* Buffer remaining data */
    if (len > 0) {
        memcpy(ctx->buffer, data, len);
        ctx->buffer_len = len;
    }
}

void harmonia_final(harmonia_ctx *ctx, uint8_t *digest) {
    uint8_t pad[128];
    size_t pad_len;
    uint64_t bit_len;
    uint32_t g[8], c[8];
    int i;
    uint32_t rot, g_rot, c_rot, fused;

    /* Calculate padding */
    bit_len = ctx->total_len * 8;
    pad_len = (ctx->buffer_len < 56) ? (56 - ctx->buffer_len) : (120 - ctx->buffer_len);

    memset(pad, 0, pad_len + 8);
    pad[0] = 0x80;

    /* Append length (big-endian) */
    pad[pad_len + 0] = (bit_len >> 56) & 0xFF;
    pad[pad_len + 1] = (bit_len >> 48) & 0xFF;
    pad[pad_len + 2] = (bit_len >> 40) & 0xFF;
    pad[pad_len + 3] = (bit_len >> 32) & 0xFF;
    pad[pad_len + 4] = (bit_len >> 24) & 0xFF;
    pad[pad_len + 5] = (bit_len >> 16) & 0xFF;
    pad[pad_len + 6] = (bit_len >> 8) & 0xFF;
    pad[pad_len + 7] = bit_len & 0xFF;

    harmonia_update(ctx, pad, pad_len + 8);

    /* Final edge protection */
    memcpy(g, ctx->state_g, 32);
    memcpy(c, ctx->state_c, 32);
    edge_protection(g, 64);
    edge_protection(c, 65);

    /* Fuse streams */
    for (i = 0; i < 8; i++) {
        rot = quasicrystal_rotation(i, i);
        g_rot = ROTR32(g[i], rot);
        c_rot = ROTL32(c[i], rot);

        fused = g_rot ^ c_rot;
        fused += PHI_CONSTANTS[i] + (penrose_index(i) * 0x01010101U);

        /* Output big-endian */
        digest[i*4 + 0] = (fused >> 24) & 0xFF;
        digest[i*4 + 1] = (fused >> 16) & 0xFF;
        digest[i*4 + 2] = (fused >> 8) & 0xFF;
        digest[i*4 + 3] = fused & 0xFF;
    }
}

void harmonia(const uint8_t *data, size_t len, uint8_t *digest) {
    harmonia_ctx ctx;
    harmonia_init(&ctx);
    harmonia_update(&ctx, data, len);
    harmonia_final(&ctx, digest);
}

void harmonia_hex(const uint8_t *data, size_t len, char *hex_digest) {
    uint8_t digest[32];
    int i;

    harmonia(data, len, digest);

    for (i = 0; i < 32; i++) {
        sprintf(hex_digest + i*2, "%02x", digest[i]);
    }
    hex_digest[64] = '\0';
}

/* ============================================================================
 * SELF-TEST
 * ============================================================================ */

int harmonia_self_test(void) {
    static const struct {
        const char *input;
        const char *expected;
    } test_vectors[] = {
        {"", "3acc512691bd37d475cec1695d99503b4a3401aa9366b312951ba200190bfe3d"},
        {"Harmonia", "5aa5b3bf63ed5d726288f05da3b9ecc419216b260cc780e2435dddf9bf593257"},
        {"The quick brown fox jumps over the lazy dog",
         "39661e930dae99563e597b155d177e331d3016fa65405624c3b2159b9c86b4aa"},
        {NULL, NULL}
    };

    char hex[65];
    int i, passed = 1;

    printf("HARMONIA v%s Self-Test (C Implementation)\n", HARMONIA_VERSION);
    printf("============================================================\n");

    for (i = 0; test_vectors[i].input != NULL; i++) {
        harmonia_hex((const uint8_t*)test_vectors[i].input,
                     strlen(test_vectors[i].input), hex);

        if (strcmp(hex, test_vectors[i].expected) == 0) {
            printf("  [PASS] \"%s\"\n",
                   test_vectors[i].input[0] ? test_vectors[i].input : "(empty)");
        } else {
            printf("  [FAIL] \"%s\"\n",
                   test_vectors[i].input[0] ? test_vectors[i].input : "(empty)");
            printf("    Expected: %s\n", test_vectors[i].expected);
            printf("    Got:      %s\n", hex);
            passed = 0;
        }
    }

    printf("============================================================\n");
    printf("Result: %s\n", passed ? "PASS" : "FAIL");

    return passed;
}
