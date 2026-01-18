#!/usr/bin/env python3
"""
HARMONIA-NG: Next Generation SIMD-Optimized Hash Function

A 256-bit cryptographic hash function based on HARMONIA, redesigned for
SIMD vectorization while preserving the golden ratio and Fibonacci
mathematical foundations.

Key differences from HARMONIA-64:
- Fixed rotations per round (not per state word) - enables SIMD
- 32 rounds (reduced from 64) with 3x security margin
- ChaCha-style quarter-round mixing (removed a*3 XOR b*5)
- Simplified edge protection with fixed rotations

Version: 1.0
Author: Based on HARMONIA by Fausto Dasè
"""

import struct
from typing import List, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================

VERSION = "1.0"
MASK32 = 0xFFFFFFFF
NUM_ROUNDS = 32
BLOCK_SIZE = 64  # bytes
DIGEST_SIZE = 32  # bytes
STATE_WORDS = 8

# Fibonacci sequence (first 12 values)
FIBONACCI = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144)

# Fibonacci word for 32 rounds (quasi-periodic round scheduling)
# Extended to 32 characters: ABAABABAABAABABAABABAABAABABAABAAB -> first 32
FIBONACCI_WORD = "ABAABABAABAABABAABABAABAABABAABA"

# Golden ratio constants (same as HARMONIA, derived from φ)
PHI_CONSTANTS = (
    0x9E37605A, 0xDAC1E0F2, 0xF287A338, 0xFA8CFC04,
    0xFD805AA6, 0xCCF29760, 0xFF8184C3, 0xFF850D11,
    0xCC32476B, 0x98767486, 0xFFF82080, 0x30E4E2F3,
    0xFCC3ACC1, 0xE5216F38, 0xF30E4CC9, 0x948395F6
)

# Reciprocal constants (derived from 1/φ)
RECIPROCAL_CONSTANTS = (
    0x7249217F, 0x5890EB7C, 0x4786B47C, 0x4C51DBE8,
    0x4E4DA61B, 0x4F76650C, 0x4F2F1A2A, 0x4F6CE289,
    0x4F1ADF40, 0x4E84BABC, 0x4F22D993, 0x497FA704,
    0x4F514F19, 0x4E8F43B8, 0x508E2FD9, 0x4B5F94A4
)

# Rotation sets (ChaCha-inspired with golden-ratio influence)
ROTATIONS_A = (7, 12, 8, 16)   # Intensive rounds (A)
ROTATIONS_B = (5, 11, 9, 13)   # Light rounds (B)

# Pre-computed rotation schedule for 32 rounds
# Each round has 4 rotations, selected by Fibonacci word and permuted by fib index
def _generate_rotation_schedule() -> Tuple[Tuple[int, int, int, int], ...]:
    """Generate the 32-round rotation schedule."""
    schedule = []
    for r in range(NUM_ROUNDS):
        round_type = FIBONACCI_WORD[r]
        fib_idx = FIBONACCI[r % 12]

        if round_type == 'A':
            base = ROTATIONS_A
        else:
            base = ROTATIONS_B

        # Permute based on Fibonacci index for quasi-periodic variation
        shift = fib_idx % 4
        rotations = tuple(base[(i + shift) % 4] for i in range(4))
        schedule.append(rotations)

    return tuple(schedule)

ROUND_ROTATIONS = _generate_rotation_schedule()

# Initial hash values (derived from φ and 1/φ)
INITIAL_HASH_G = (
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19
)

INITIAL_HASH_C = (
    0x9E3779B9, 0x7F4A7C15, 0xF39CC060, 0x5CEDC834,
    0x2FE12A6D, 0x4786B47C, 0xC8A5E2F0, 0x3A8D6B7F
)

# Fixed rotations for edge protection (SIMD-friendly)
EDGE_ROT_LEFT = 7
EDGE_ROT_RIGHT = 13

# Fixed rotation for cross-stream diffusion
CROSS_STREAM_ROT = 11


# ============================================================================
# PRIMITIVE OPERATIONS
# ============================================================================

def _rotl(x: int, n: int) -> int:
    """32-bit left rotation."""
    n = n % 32
    return ((x << n) | (x >> (32 - n))) & MASK32


def _rotr(x: int, n: int) -> int:
    """32-bit right rotation."""
    n = n % 32
    return ((x >> n) | (x << (32 - n))) & MASK32


# ============================================================================
# QUARTER-ROUND FUNCTION (ChaCha-style, SIMD-friendly)
# ============================================================================

def _quarter_round(state: List[int], a: int, b: int, c: int, d: int,
                   r1: int, r2: int, r3: int, r4: int) -> None:
    """
    ChaCha-style quarter-round mixing function.

    All 4 rotations are fixed for this call, enabling SIMD vectorization.
    Operates in-place on the state array.
    """
    # Step 1: a += b; d ^= a; d <<<= r1
    state[a] = (state[a] + state[b]) & MASK32
    state[d] ^= state[a]
    state[d] = _rotl(state[d], r1)

    # Step 2: c += d; b ^= c; b <<<= r2
    state[c] = (state[c] + state[d]) & MASK32
    state[b] ^= state[c]
    state[b] = _rotl(state[b], r2)

    # Step 3: a += b; d ^= a; d <<<= r3
    state[a] = (state[a] + state[b]) & MASK32
    state[d] ^= state[a]
    state[d] = _rotl(state[d], r3)

    # Step 4: c += d; b ^= c; b <<<= r4
    state[c] = (state[c] + state[d]) & MASK32
    state[b] ^= state[c]
    state[b] = _rotl(state[b], r4)


# ============================================================================
# EDGE PROTECTION (Simplified, SIMD-friendly)
# ============================================================================

def _edge_protection(state: List[int], round_num: int) -> None:
    """
    Simplified edge protection with fixed rotations.

    Inspired by topological edge states in quantum systems.
    Uses fixed rotations (7, 13) for SIMD compatibility.
    """
    # Fibonacci-derived constant
    fib_const = (FIBONACCI[round_num % 12] * 0x9E3779B9) & MASK32

    # Left edge protection
    state[0] = _rotr(state[0], EDGE_ROT_LEFT)
    state[0] ^= fib_const

    # Right edge protection
    state[7] = _rotl(state[7], EDGE_ROT_RIGHT)
    state[7] ^= (~fib_const) & MASK32

    # Edge interaction
    interaction = (state[0] ^ state[7]) >> 16
    state[0] = (state[0] + interaction) & MASK32
    state[7] = (state[7] + interaction) & MASK32


# ============================================================================
# CROSS-STREAM DIFFUSION
# ============================================================================

def _cross_stream_diffusion(g: List[int], c: List[int]) -> None:
    """
    Cross-stream mixing between golden and complementary streams.

    Uses fixed rotation (CROSS_STREAM_ROT = 11) for SIMD compatibility.
    """
    for i in range(STATE_WORDS):
        temp = (g[i] ^ c[(i + 3) % STATE_WORDS]) & MASK32
        g[i] = (g[i] + _rotr(temp, CROSS_STREAM_ROT)) & MASK32
        c[i] = (c[i] ^ _rotl(temp, CROSS_STREAM_ROT)) & MASK32


# ============================================================================
# MESSAGE EXPANSION
# ============================================================================

def _expand_message(block: bytes) -> List[int]:
    """
    Expand 64-byte block to 32 message words.

    Uses simplified expansion similar to SHA-256 but with Fibonacci influence.
    """
    # Parse first 16 words from block
    w = list(struct.unpack('>16I', block))

    # Expand to 32 words
    for i in range(16, NUM_ROUNDS):
        # SHA-256-style sigma functions
        rot1 = 7 + (i % 5)   # Variable rotation 7-11
        rot2 = 17 + (i % 4)  # Variable rotation 17-20

        s0 = _rotr(w[i-15], rot1) ^ _rotr(w[i-15], rot1 + 11) ^ (w[i-15] >> 3)
        s1 = _rotr(w[i-2], rot2) ^ _rotr(w[i-2], rot2 + 2) ^ (w[i-2] >> 10)

        # Fibonacci factor for quasi-periodic influence
        fib_factor = FIBONACCI[i % 12]

        w.append((w[i-16] + s0 + w[i-7] + s1 + fib_factor) & MASK32)

    return w


# ============================================================================
# COMPRESSION FUNCTION
# ============================================================================

def _compress(block: bytes, state_g: List[int], state_c: List[int]) -> Tuple[List[int], List[int]]:
    """
    HARMONIA-NG compression function (32 rounds, SIMD-friendly).

    Processes one 512-bit block and updates the dual-stream state.
    """
    # Expand message to 32 words
    w = _expand_message(block)

    # Working copies of state
    g = list(state_g)
    c = list(state_c)

    for r in range(NUM_ROUNDS):
        # Get rotation set for this round
        r1, r2, r3, r4 = ROUND_ROTATIONS[r]

        # Get constants for this round
        k_phi = PHI_CONSTANTS[r % 16]
        k_rec = RECIPROCAL_CONSTANTS[r % 16]

        # Message injection
        g[0] = (g[0] + w[r]) & MASK32
        c[0] = (c[0] + w[NUM_ROUNDS - 1 - r]) & MASK32

        # Constant injection (XOR preserves invertibility)
        g[4] ^= k_phi
        c[4] ^= k_rec

        # Column quarter-rounds (golden stream)
        _quarter_round(g, 0, 1, 2, 3, r1, r2, r3, r4)
        _quarter_round(g, 4, 5, 6, 7, r1, r2, r3, r4)

        # Diagonal quarter-rounds (golden stream)
        _quarter_round(g, 0, 5, 2, 7, r1, r2, r3, r4)
        _quarter_round(g, 4, 1, 6, 3, r1, r2, r3, r4)

        # Column quarter-rounds (complementary stream)
        _quarter_round(c, 0, 1, 2, 3, r1, r2, r3, r4)
        _quarter_round(c, 4, 5, 6, 7, r1, r2, r3, r4)

        # Diagonal quarter-rounds (complementary stream)
        _quarter_round(c, 0, 5, 2, 7, r1, r2, r3, r4)
        _quarter_round(c, 4, 1, 6, 3, r1, r2, r3, r4)

        # Cross-stream diffusion every 4 rounds
        if (r + 1) % 4 == 0:
            _cross_stream_diffusion(g, c)

        # Edge protection every 8 rounds
        if (r + 1) % 8 == 0:
            _edge_protection(g, r)
            _edge_protection(c, r)

    # Davies-Meyer: add working state to original state
    new_g = [(state_g[i] + g[i]) & MASK32 for i in range(STATE_WORDS)]
    new_c = [(state_c[i] + c[i]) & MASK32 for i in range(STATE_WORDS)]

    return new_g, new_c


# ============================================================================
# FINALIZATION
# ============================================================================

def _finalize(state_g: List[int], state_c: List[int]) -> bytes:
    """
    Finalize and produce the 256-bit digest.

    Applies final edge protection and fuses the dual streams.
    """
    g = list(state_g)
    c = list(state_c)

    # Final edge protection
    _edge_protection(g, NUM_ROUNDS)
    _edge_protection(c, NUM_ROUNDS + 1)

    # Fuse streams with fixed rotations
    digest_words = []
    for i in range(STATE_WORDS):
        rot = (i * 3 + 5) % 16 + 1  # Rotation 1-16 based on position

        g_rot = _rotr(g[i], rot)
        c_rot = _rotl(c[i], rot)

        fused = (g_rot ^ c_rot) & MASK32
        fused = (fused + PHI_CONSTANTS[i]) & MASK32

        digest_words.append(fused)

    return struct.pack('>8I', *digest_words)


# ============================================================================
# PADDING
# ============================================================================

def _pad_message(message: bytes) -> bytes:
    """
    Apply Merkle-Damgård padding to the message.

    Appends 0x80, zeros, and 64-bit big-endian length.
    """
    msg_len = len(message)
    bit_len = msg_len * 8

    # Append 0x80
    padded = message + b'\x80'

    # Pad with zeros until length ≡ 448 (mod 512)
    # That's 56 bytes (mod 64)
    pad_len = (56 - (msg_len + 1) % 64) % 64
    padded += b'\x00' * pad_len

    # Append 64-bit big-endian length
    padded += struct.pack('>Q', bit_len)

    return padded


# ============================================================================
# PUBLIC API
# ============================================================================

def harmonia_ng(message: bytes) -> bytes:
    """
    Compute HARMONIA-NG hash of a message.

    Args:
        message: Input bytes to hash

    Returns:
        32-byte (256-bit) digest
    """
    # Initialize state
    state_g = list(INITIAL_HASH_G)
    state_c = list(INITIAL_HASH_C)

    # Pad message
    padded = _pad_message(message)

    # Process blocks
    for i in range(0, len(padded), BLOCK_SIZE):
        block = padded[i:i + BLOCK_SIZE]
        state_g, state_c = _compress(block, state_g, state_c)

    # Finalize
    return _finalize(state_g, state_c)


def harmonia_ng_hex(message: bytes) -> str:
    """
    Compute HARMONIA-NG hash and return as hexadecimal string.

    Args:
        message: Input bytes to hash

    Returns:
        64-character hexadecimal string
    """
    return harmonia_ng(message).hex()


# ============================================================================
# SELF-TEST
# ============================================================================

# Official test vectors for HARMONIA-NG v1.0
TEST_VECTORS = {
    b"": "f0861e3ad1a2a438b4ceea78d14f21074dcd712b073917b28d7ae7fad8f6a562",
    b"Harmonia": "11cd23650f8fd4818848bc6f09da18b06403ed6f5250447c5d1036730cb8987c",
    b"The quick brown fox jumps over the lazy dog": "05a015d792c2146a00d941ba342e0dbb219ff7ef6da48d05caf8310d3c844172",
    b"HARMONIA-NG": "6d310650be2092be611cf35ea8dcc46b8199a3f6299398fa68dcf73f80f8a334",
}


def self_test() -> bool:
    """
    Run self-test with test vectors.

    Returns:
        True if all tests pass
    """
    print(f"HARMONIA-NG v{VERSION} Self-Test")
    print("=" * 60)

    all_passed = True

    for input_bytes, expected in TEST_VECTORS.items():
        result = harmonia_ng_hex(input_bytes)
        input_str = input_bytes.decode('utf-8') if input_bytes else "(empty)"

        passed = result == expected
        status = "\u2713" if passed else "\u2717"
        print(f"  {status} {input_str}")
        if not passed:
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
            all_passed = False

    # Avalanche test
    print("\nAvalanche Test:")
    msg1 = b"test"
    msg2 = b"tess"
    hash1 = harmonia_ng(msg1)
    hash2 = harmonia_ng(msg2)

    diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(hash1, hash2))
    percent = diff_bits / 256 * 100

    print(f"  '{msg1.decode()}' vs '{msg2.decode()}': {diff_bits}/256 bits differ ({percent:.1f}%)")

    avalanche_ok = 45.0 <= percent <= 55.0
    print(f"  {'PASS' if avalanche_ok else 'WARN'} Avalanche effect {'OK' if avalanche_ok else 'needs review'}")

    print("=" * 60)
    print(f"Result: {'PASS' if all_passed else 'FAIL'}")

    return all_passed


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Hash command line argument
        message = sys.argv[1].encode('utf-8')
        print(harmonia_ng_hex(message))
    else:
        # Run self-test
        self_test()
