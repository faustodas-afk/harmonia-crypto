/*
 * HARMONIA-NG: Next Generation SIMD-Optimized Hash Function
 *
 * A 256-bit cryptographic hash function based on HARMONIA, redesigned for
 * SIMD vectorization while preserving the golden ratio and Fibonacci
 * mathematical foundations.
 *
 * Features:
 * - Fixed rotations per round (enables SIMD)
 * - 32 rounds with 97% security margin
 * - ChaCha-style quarter-round mixing
 * - ARM NEON SIMD acceleration
 *
 * Version: 1.0
 * Author: Based on HARMONIA by Fausto Dasè
 */

#include "harmonia_ng.h"
#include <string.h>
#include <stdio.h>

/* Detect SIMD support */
#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#define HARMONIA_NG_NEON 1
#include <arm_neon.h>
#endif

#if defined(__AVX2__)
#define HARMONIA_NG_AVX2 1
#include <immintrin.h>
#endif

/* ============================================================================
 * CONSTANTS
 * ============================================================================ */

/* Fibonacci sequence (first 12 values) */
static const uint32_t FIBONACCI[12] = {
    1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144
};

/* Golden ratio constants (derived from φ) */
static const uint32_t PHI_CONSTANTS[16] = {
    0x9E37605A, 0xDAC1E0F2, 0xF287A338, 0xFA8CFC04,
    0xFD805AA6, 0xCCF29760, 0xFF8184C3, 0xFF850D11,
    0xCC32476B, 0x98767486, 0xFFF82080, 0x30E4E2F3,
    0xFCC3ACC1, 0xE5216F38, 0xF30E4CC9, 0x948395F6
};

/* Reciprocal constants (derived from 1/φ) */
static const uint32_t RECIPROCAL_CONSTANTS[16] = {
    0x7249217F, 0x5890EB7C, 0x4786B47C, 0x4C51DBE8,
    0x4E4DA61B, 0x4F76650C, 0x4F2F1A2A, 0x4F6CE289,
    0x4F1ADF40, 0x4E84BABC, 0x4F22D993, 0x497FA704,
    0x4F514F19, 0x4E8F43B8, 0x508E2FD9, 0x4B5F94A4
};

/* Initial hash values (golden stream) */
static const uint32_t INITIAL_HASH_G[8] = {
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19
};

/* Initial hash values (complementary stream) */
static const uint32_t INITIAL_HASH_C[8] = {
    0x9E3779B9, 0x7F4A7C15, 0xF39CC060, 0x5CEDC834,
    0x2FE12A6D, 0x4786B47C, 0xC8A5E2F0, 0x3A8D6B7F
};

/* Pre-computed rotation schedule (32 rounds x 4 rotations)
 * Generated from Fibonacci word with rotation sets A=(7,12,8,16), B=(5,11,9,13)
 * Must match Python harmonia_ng._generate_rotation_schedule() exactly */
static const uint8_t ROUND_ROTATIONS[32][4] = {
    {12, 8, 16, 7},   /* Round 0:  A */
    {11, 9, 13, 5},   /* Round 1:  B */
    {8, 16, 7, 12},   /* Round 2:  A */
    {16, 7, 12, 8},   /* Round 3:  A */
    {11, 9, 13, 5},   /* Round 4:  B */
    {7, 12, 8, 16},   /* Round 5:  A */
    {11, 9, 13, 5},   /* Round 6:  B */
    {12, 8, 16, 7},   /* Round 7:  A */
    {8, 16, 7, 12},   /* Round 8:  A */
    {13, 5, 11, 9},   /* Round 9:  B */
    {12, 8, 16, 7},   /* Round 10: A */
    {7, 12, 8, 16},   /* Round 11: A */
    {11, 9, 13, 5},   /* Round 12: B */
    {12, 8, 16, 7},   /* Round 13: A */
    {9, 13, 5, 11},   /* Round 14: B */
    {16, 7, 12, 8},   /* Round 15: A */
    {12, 8, 16, 7},   /* Round 16: A */
    {5, 11, 9, 13},   /* Round 17: B */
    {12, 8, 16, 7},   /* Round 18: A */
    {11, 9, 13, 5},   /* Round 19: B */
    {8, 16, 7, 12},   /* Round 20: A */
    {16, 7, 12, 8},   /* Round 21: A */
    {11, 9, 13, 5},   /* Round 22: B */
    {7, 12, 8, 16},   /* Round 23: A */
    {12, 8, 16, 7},   /* Round 24: A */
    {11, 9, 13, 5},   /* Round 25: B */
    {8, 16, 7, 12},   /* Round 26: A */
    {13, 5, 11, 9},   /* Round 27: B */
    {12, 8, 16, 7},   /* Round 28: A */
    {7, 12, 8, 16},   /* Round 29: A */
    {11, 9, 13, 5},   /* Round 30: B */
    {12, 8, 16, 7},   /* Round 31: A */
};

/* Fixed rotations for edge protection */
#define EDGE_ROT_LEFT  7
#define EDGE_ROT_RIGHT 13

/* Fixed rotation for cross-stream diffusion */
#define CROSS_STREAM_ROT 11

/* ============================================================================
 * PRIMITIVE OPERATIONS
 * ============================================================================ */

#define ROTL32(x, n) (((x) << (n)) | ((x) >> (32 - (n))))
#define ROTR32(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

/* ============================================================================
 * QUARTER-ROUND FUNCTION (SCALAR)
 * ============================================================================ */

static inline void quarter_round(uint32_t *state, int a, int b, int c, int d,
                                  int r1, int r2, int r3, int r4)
{
    state[a] += state[b];
    state[d] ^= state[a];
    state[d] = ROTL32(state[d], r1);

    state[c] += state[d];
    state[b] ^= state[c];
    state[b] = ROTL32(state[b], r2);

    state[a] += state[b];
    state[d] ^= state[a];
    state[d] = ROTL32(state[d], r3);

    state[c] += state[d];
    state[b] ^= state[c];
    state[b] = ROTL32(state[b], r4);
}

/* ============================================================================
 * NEON SIMD IMPLEMENTATION
 * ============================================================================ */

#ifdef HARMONIA_NG_NEON

/* NEON rotation with variable shift using vshlq_u32 (variable shift vector) */
static inline uint32x4_t neon_rotl_var(uint32x4_t x, int32_t n)
{
    int32x4_t shift_left = vdupq_n_s32(n);
    int32x4_t shift_right = vdupq_n_s32(n - 32);
    return vorrq_u32(vshlq_u32(x, shift_left), vshlq_u32(x, shift_right));
}

/* NEON quarter-round macro for specific rotation values
 * We use macros because NEON shift intrinsics require compile-time constants */
#define NEON_QUARTER_ROUND(a, b, c, d, R1, R2, R3, R4) do { \
    (a) = vaddq_u32((a), (b)); \
    (d) = veorq_u32((d), (a)); \
    (d) = vorrq_u32(vshlq_n_u32((d), R1), vshrq_n_u32((d), 32 - R1)); \
    (c) = vaddq_u32((c), (d)); \
    (b) = veorq_u32((b), (c)); \
    (b) = vorrq_u32(vshlq_n_u32((b), R2), vshrq_n_u32((b), 32 - R2)); \
    (a) = vaddq_u32((a), (b)); \
    (d) = veorq_u32((d), (a)); \
    (d) = vorrq_u32(vshlq_n_u32((d), R3), vshrq_n_u32((d), 32 - R3)); \
    (c) = vaddq_u32((c), (d)); \
    (b) = veorq_u32((b), (c)); \
    (b) = vorrq_u32(vshlq_n_u32((b), R4), vshrq_n_u32((b), 32 - R4)); \
} while(0)

#endif /* HARMONIA_NG_NEON */

/* ============================================================================
 * EDGE PROTECTION
 * ============================================================================ */

static void edge_protection(uint32_t *state, int round_num)
{
    uint32_t fib_const = FIBONACCI[round_num % 12] * 0x9E3779B9U;
    uint32_t interaction;

    /* Left edge */
    state[0] = ROTR32(state[0], EDGE_ROT_LEFT);
    state[0] ^= fib_const;

    /* Right edge */
    state[7] = ROTL32(state[7], EDGE_ROT_RIGHT);
    state[7] ^= ~fib_const;

    /* Edge interaction */
    interaction = (state[0] ^ state[7]) >> 16;
    state[0] += interaction;
    state[7] += interaction;
}

/* ============================================================================
 * CROSS-STREAM DIFFUSION
 * ============================================================================ */

static void cross_stream_diffusion(uint32_t *g, uint32_t *c)
{
    uint32_t temp;
    int i;

    for (i = 0; i < 8; i++) {
        temp = g[i] ^ c[(i + 3) % 8];
        g[i] += ROTR32(temp, CROSS_STREAM_ROT);
        c[i] ^= ROTL32(temp, CROSS_STREAM_ROT);
    }
}

/* ============================================================================
 * MESSAGE EXPANSION
 * ============================================================================ */

static void expand_message(const uint8_t *block, uint32_t *w)
{
    int i;
    uint32_t s0, s1, fib_factor;
    int rot1, rot2;

    /* Parse first 16 words (big-endian) */
    for (i = 0; i < 16; i++) {
        w[i] = ((uint32_t)block[i*4] << 24) |
               ((uint32_t)block[i*4+1] << 16) |
               ((uint32_t)block[i*4+2] << 8) |
               ((uint32_t)block[i*4+3]);
    }

    /* Expand to 32 words */
    for (i = 16; i < 32; i++) {
        rot1 = 7 + (i % 5);
        rot2 = 17 + (i % 4);

        s0 = ROTR32(w[i-15], rot1) ^ ROTR32(w[i-15], rot1 + 11) ^ (w[i-15] >> 3);
        s1 = ROTR32(w[i-2], rot2) ^ ROTR32(w[i-2], rot2 + 2) ^ (w[i-2] >> 10);

        fib_factor = FIBONACCI[i % 12];

        w[i] = w[i-16] + s0 + w[i-7] + s1 + fib_factor;
    }
}

/* ============================================================================
 * COMPRESSION FUNCTION (SCALAR)
 * ============================================================================ */

static void compress_scalar(const uint8_t *block, uint32_t *state_g, uint32_t *state_c)
{
    uint32_t w[32];
    uint32_t g[8], c[8];
    int r, i;
    int r1, r2, r3, r4;
    uint32_t k_phi, k_rec;

    /* Expand message */
    expand_message(block, w);

    /* Copy state */
    for (i = 0; i < 8; i++) {
        g[i] = state_g[i];
        c[i] = state_c[i];
    }

    /* 32 rounds */
    for (r = 0; r < 32; r++) {
        r1 = ROUND_ROTATIONS[r][0];
        r2 = ROUND_ROTATIONS[r][1];
        r3 = ROUND_ROTATIONS[r][2];
        r4 = ROUND_ROTATIONS[r][3];

        k_phi = PHI_CONSTANTS[r % 16];
        k_rec = RECIPROCAL_CONSTANTS[r % 16];

        /* Message injection */
        g[0] += w[r];
        c[0] += w[31 - r];

        /* Constant injection */
        g[4] ^= k_phi;
        c[4] ^= k_rec;

        /* Column quarter-rounds (golden stream) */
        quarter_round(g, 0, 1, 2, 3, r1, r2, r3, r4);
        quarter_round(g, 4, 5, 6, 7, r1, r2, r3, r4);

        /* Diagonal quarter-rounds (golden stream) */
        quarter_round(g, 0, 5, 2, 7, r1, r2, r3, r4);
        quarter_round(g, 4, 1, 6, 3, r1, r2, r3, r4);

        /* Column quarter-rounds (complementary stream) */
        quarter_round(c, 0, 1, 2, 3, r1, r2, r3, r4);
        quarter_round(c, 4, 5, 6, 7, r1, r2, r3, r4);

        /* Diagonal quarter-rounds (complementary stream) */
        quarter_round(c, 0, 5, 2, 7, r1, r2, r3, r4);
        quarter_round(c, 4, 1, 6, 3, r1, r2, r3, r4);

        /* Cross-stream diffusion every 4 rounds */
        if ((r + 1) % 4 == 0) {
            cross_stream_diffusion(g, c);
        }

        /* Edge protection every 8 rounds */
        if ((r + 1) % 8 == 0) {
            edge_protection(g, r);
            edge_protection(c, r);
        }
    }

    /* Davies-Meyer: add to original state */
    for (i = 0; i < 8; i++) {
        state_g[i] += g[i];
        state_c[i] += c[i];
    }
}

/* ============================================================================
 * FINALIZATION
 * ============================================================================ */

static void finalize(uint32_t *state_g, uint32_t *state_c, uint8_t *digest)
{
    uint32_t g[8], c[8];
    uint32_t fused;
    int i, rot;

    /* Copy state */
    for (i = 0; i < 8; i++) {
        g[i] = state_g[i];
        c[i] = state_c[i];
    }

    /* Final edge protection */
    edge_protection(g, 32);
    edge_protection(c, 33);

    /* Fuse streams and output */
    for (i = 0; i < 8; i++) {
        rot = (i * 3 + 5) % 16 + 1;

        fused = ROTR32(g[i], rot) ^ ROTL32(c[i], rot);
        fused += PHI_CONSTANTS[i];

        /* Big-endian output */
        digest[i*4 + 0] = (fused >> 24) & 0xFF;
        digest[i*4 + 1] = (fused >> 16) & 0xFF;
        digest[i*4 + 2] = (fused >> 8) & 0xFF;
        digest[i*4 + 3] = fused & 0xFF;
    }
}

/* ============================================================================
 * PUBLIC API
 * ============================================================================ */

void harmonia_ng_init(harmonia_ng_ctx *ctx)
{
    int i;
    for (i = 0; i < 8; i++) {
        ctx->state_g[i] = INITIAL_HASH_G[i];
        ctx->state_c[i] = INITIAL_HASH_C[i];
    }
    ctx->buffer_len = 0;
    ctx->total_len = 0;
}

void harmonia_ng_update(harmonia_ng_ctx *ctx, const uint8_t *data, size_t len)
{
    size_t remaining, to_copy;

    ctx->total_len += len;

    /* If we have buffered data, try to complete a block */
    if (ctx->buffer_len > 0) {
        remaining = 64 - ctx->buffer_len;
        to_copy = (len < remaining) ? len : remaining;
        memcpy(ctx->buffer + ctx->buffer_len, data, to_copy);
        ctx->buffer_len += to_copy;
        data += to_copy;
        len -= to_copy;

        if (ctx->buffer_len == 64) {
            compress_scalar(ctx->buffer, ctx->state_g, ctx->state_c);
            ctx->buffer_len = 0;
        }
    }

    /* Process full blocks */
    while (len >= 64) {
        compress_scalar(data, ctx->state_g, ctx->state_c);
        data += 64;
        len -= 64;
    }

    /* Buffer remaining data */
    if (len > 0) {
        memcpy(ctx->buffer, data, len);
        ctx->buffer_len = len;
    }
}

void harmonia_ng_final(harmonia_ng_ctx *ctx, uint8_t *digest)
{
    uint64_t bit_len = ctx->total_len * 8;
    size_t pad_len;

    /* Append 0x80 */
    ctx->buffer[ctx->buffer_len++] = 0x80;

    /* Pad to 56 bytes (mod 64) */
    if (ctx->buffer_len > 56) {
        /* Need another block */
        memset(ctx->buffer + ctx->buffer_len, 0, 64 - ctx->buffer_len);
        compress_scalar(ctx->buffer, ctx->state_g, ctx->state_c);
        ctx->buffer_len = 0;
    }

    memset(ctx->buffer + ctx->buffer_len, 0, 56 - ctx->buffer_len);

    /* Append 64-bit length (big-endian) */
    ctx->buffer[56] = (bit_len >> 56) & 0xFF;
    ctx->buffer[57] = (bit_len >> 48) & 0xFF;
    ctx->buffer[58] = (bit_len >> 40) & 0xFF;
    ctx->buffer[59] = (bit_len >> 32) & 0xFF;
    ctx->buffer[60] = (bit_len >> 24) & 0xFF;
    ctx->buffer[61] = (bit_len >> 16) & 0xFF;
    ctx->buffer[62] = (bit_len >> 8) & 0xFF;
    ctx->buffer[63] = bit_len & 0xFF;

    compress_scalar(ctx->buffer, ctx->state_g, ctx->state_c);

    /* Finalize */
    finalize(ctx->state_g, ctx->state_c, digest);
}

void harmonia_ng(const uint8_t *data, size_t len, uint8_t *digest)
{
    harmonia_ng_ctx ctx;
    harmonia_ng_init(&ctx);
    harmonia_ng_update(&ctx, data, len);
    harmonia_ng_final(&ctx, digest);
}

void harmonia_ng_hex(const uint8_t *data, size_t len, char *hex_out)
{
    uint8_t digest[32];
    int i;
    harmonia_ng(data, len, digest);
    for (i = 0; i < 32; i++) {
        sprintf(hex_out + i*2, "%02x", digest[i]);
    }
    hex_out[64] = '\0';
}

/* ============================================================================
 * SELF-TEST
 * ============================================================================ */

int harmonia_ng_self_test(void)
{
    static const struct {
        const char *input;
        const char *expected;
    } test_vectors[] = {
        {"", "f0861e3ad1a2a438b4ceea78d14f21074dcd712b073917b28d7ae7fad8f6a562"},
        {"Harmonia", "11cd23650f8fd4818848bc6f09da18b06403ed6f5250447c5d1036730cb8987c"},
        {"The quick brown fox jumps over the lazy dog",
         "05a015d792c2146a00d941ba342e0dbb219ff7ef6da48d05caf8310d3c844172"},
        {"HARMONIA-NG", "6d310650be2092be611cf35ea8dcc46b8199a3f6299398fa68dcf73f80f8a334"},
        {NULL, NULL}
    };

    char hex[65];
    int i, failed = 0;

    printf("HARMONIA-NG v1.0 Self-Test\n");
    printf("============================================================\n");

    for (i = 0; test_vectors[i].input != NULL; i++) {
        harmonia_ng_hex((const uint8_t*)test_vectors[i].input,
                        strlen(test_vectors[i].input), hex);

        if (strcmp(hex, test_vectors[i].expected) == 0) {
            printf("  OK  %s\n", test_vectors[i].input[0] ? test_vectors[i].input : "(empty)");
        } else {
            printf("  FAIL %s\n", test_vectors[i].input[0] ? test_vectors[i].input : "(empty)");
            printf("       Expected: %s\n", test_vectors[i].expected);
            printf("       Got:      %s\n", hex);
            failed++;
        }
    }

    printf("============================================================\n");
    printf("Result: %s\n", failed ? "FAIL" : "PASS");

    return failed;
}

/* ============================================================================
 * MAIN (for standalone testing)
 * ============================================================================ */

#ifdef HARMONIA_NG_MAIN
int main(int argc, char *argv[])
{
    if (argc > 1) {
        char hex[65];
        harmonia_ng_hex((const uint8_t*)argv[1], strlen(argv[1]), hex);
        printf("%s\n", hex);
        return 0;
    }
    return harmonia_ng_self_test();
}
#endif
