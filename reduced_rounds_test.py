#!/usr/bin/env python3
"""
HARMONIA - Reduced Rounds Security Analysis

Tests avalanche effect and bit distribution with varying round counts
to determine minimum secure round count.
"""

import random
import math
import struct
from harmonia import (
    _rotr, _rotl, _quasicrystal_rotation, _penrose_index,
    _mix_golden, _mix_complementary, _edge_protection,
    _pad_message, _finalize, _init_state,
    PHI_CONSTANTS, RECIPROCAL_CONSTANTS, FIBONACCI_WORD, FIBONACCI
)

# Initial states are first 8 constants
INITIAL_STATE_G = PHI_CONSTANTS[:8]
INITIAL_STATE_C = RECIPROCAL_CONSTANTS[:8]


def _expand_message_reduced(block: bytes) -> list:
    """Expand 64-byte block to 64 words."""
    w = list(struct.unpack('>16I', block))

    for i in range(16, 64):
        rot1 = _quasicrystal_rotation(i, 0)
        rot2 = _quasicrystal_rotation(i, 1)

        s0 = _rotr(w[i-15], rot1) ^ _rotr(w[i-15], rot1 + 5) ^ (w[i-15] >> 3)
        s1 = _rotr(w[i-2], rot2) ^ _rotr(w[i-2], rot2 + 7) ^ (w[i-2] >> 10)

        fib_idx = _penrose_index(i)
        fib_factor = FIBONACCI[fib_idx % 12]

        w.append((w[i-16] + s0 + w[i-7] + s1 + fib_factor) & 0xFFFFFFFF)

    return w


def _cross_stream_diffusion_reduced(g: list, c: list, r: int) -> tuple:
    """Cross-stream diffusion."""
    rot = _quasicrystal_rotation(r, 4)

    for i in range(8):
        temp = (g[i] ^ c[(i + 3) % 8]) & 0xFFFFFFFF
        g[i] = (g[i] + _rotr(temp, rot)) & 0xFFFFFFFF
        c[i] = (c[i] ^ _rotl(temp, rot)) & 0xFFFFFFFF

    return g, c


def compress_reduced(block: bytes, state_g: list, state_c: list, num_rounds: int):
    """Compression function with configurable rounds."""
    w = _expand_message_reduced(block)

    g = state_g[:]
    c = state_c[:]

    for r in range(num_rounds):
        round_type = FIBONACCI_WORD[r % 64]
        k_phi = PHI_CONSTANTS[r % 16]
        k_rec = RECIPROCAL_CONSTANTS[r % 16]

        if round_type == 'A':
            for idx in range(4):
                i = idx
                j = (idx + 4) % 8
                g[i], g[j] = _mix_golden(g[i], g[j], k_phi ^ w[r % 64], r, i)
                c[i], c[j] = _mix_golden(c[i], c[j], k_rec ^ w[(r + 1) % 64], r, j)
        else:
            for idx in range(4):
                i = idx
                j = (idx + 4) % 8
                g[i], g[j] = _mix_complementary(g[i], g[j], k_phi ^ w[r % 64], r, i)
                c[i], c[j] = _mix_complementary(c[i], c[j], k_rec ^ w[(r + 1) % 64], r, j)

        if r > 0 and r % 8 == 0:
            g = _edge_protection(g, r)
            c = _edge_protection(c, r)

        if r > 0 and r % 4 == 0:
            g, c = _cross_stream_diffusion_reduced(g, c, r)

    new_g = [(state_g[i] + g[i]) & 0xFFFFFFFF for i in range(8)]
    new_c = [(state_c[i] + c[i]) & 0xFFFFFFFF for i in range(8)]

    return new_g, new_c


def harmonia_reduced(data: bytes, num_rounds: int) -> bytes:
    """HARMONIA hash with reduced rounds."""
    padded = _pad_message(data)
    state_g = list(INITIAL_STATE_G)
    state_c = list(INITIAL_STATE_C)

    for i in range(0, len(padded), 64):
        block = padded[i:i+64]
        state_g, state_c = compress_reduced(block, state_g, state_c, num_rounds)

    return _finalize(state_g, state_c)


def hamming_distance(a: bytes, b: bytes) -> int:
    """Count differing bits."""
    return sum(bin(x ^ y).count('1') for x, y in zip(a, b))


def flip_bit(data: bytes, bit_pos: int) -> bytes:
    """Flip a single bit."""
    data = bytearray(data)
    byte_idx = bit_pos // 8
    bit_idx = 7 - (bit_pos % 8)
    data[byte_idx] ^= (1 << bit_idx)
    return bytes(data)


def bytes_to_bits(data: bytes) -> list:
    """Convert bytes to bit list."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def test_avalanche_reduced(num_rounds: int, samples: int = 300) -> dict:
    """Test avalanche effect with reduced rounds."""
    bit_changes = []

    for _ in range(samples):
        msg = random.randbytes(random.randint(8, 64))
        original_hash = harmonia_reduced(msg, num_rounds)

        bit_pos = random.randint(0, len(msg) * 8 - 1)
        modified_msg = flip_bit(msg, bit_pos)
        modified_hash = harmonia_reduced(modified_msg, num_rounds)

        changed = hamming_distance(original_hash, modified_hash)
        bit_changes.append(changed)

    avg_change = sum(bit_changes) / len(bit_changes)
    pct_change = avg_change / 256 * 100
    std_dev = math.sqrt(sum((x - avg_change)**2 for x in bit_changes) / len(bit_changes))
    min_change = min(bit_changes)

    return {
        'rounds': num_rounds,
        'avg_bits': avg_change,
        'pct': pct_change,
        'std': std_dev,
        'min': min_change,
        'secure': pct_change >= 45 and min_change >= 60
    }


def test_bit_distribution_reduced(num_rounds: int, samples: int = 500) -> dict:
    """Test bit distribution with reduced rounds."""
    total_ones = 0
    total_bits = 0

    for i in range(samples):
        msg = i.to_bytes((i.bit_length() + 7) // 8 or 1, 'big')
        h = harmonia_reduced(msg, num_rounds)
        bits = bytes_to_bits(h)
        total_ones += sum(bits)
        total_bits += len(bits)

    pct_ones = total_ones / total_bits * 100
    deviation = abs(50 - pct_ones)

    return {
        'rounds': num_rounds,
        'pct_ones': pct_ones,
        'deviation': deviation,
        'secure': deviation < 2.0
    }


def main():
    print("=" * 70)
    print("HARMONIA - REDUCED ROUNDS SECURITY ANALYSIS")
    print("=" * 70)

    round_counts = [8, 16, 24, 32, 40, 48, 56, 64]

    print("\n### AVALANCHE EFFECT TEST ###\n")
    print(f"{'Rounds':<8} {'Avg Bits':<12} {'Percent':<10} {'Min':<8} {'Std Dev':<10} {'Status':<10}")
    print("-" * 70)

    avalanche_results = []
    for rounds in round_counts:
        result = test_avalanche_reduced(rounds, samples=200)
        avalanche_results.append(result)
        status = "SECURE" if result['secure'] else "WEAK"
        print(f"{rounds:<8} {result['avg_bits']:<12.2f} {result['pct']:<10.2f}% {result['min']:<8} {result['std']:<10.2f} {status:<10}")

    print("\n### BIT DISTRIBUTION TEST ###\n")
    print(f"{'Rounds':<8} {'Ones %':<12} {'Deviation':<12} {'Status':<10}")
    print("-" * 50)

    dist_results = []
    for rounds in round_counts:
        result = test_bit_distribution_reduced(rounds, samples=300)
        dist_results.append(result)
        status = "SECURE" if result['secure'] else "BIASED"
        print(f"{rounds:<8} {result['pct_ones']:<12.4f} {result['deviation']:<12.4f} {status:<10}")

    # Find minimum secure rounds
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)

    min_secure_aval = None
    for r in avalanche_results:
        if r['secure']:
            min_secure_aval = r['rounds']
            break

    min_secure_dist = None
    for r in dist_results:
        if r['secure']:
            min_secure_dist = r['rounds']
            break

    if min_secure_aval and min_secure_dist:
        min_secure = max(min_secure_aval, min_secure_dist)
        print(f"\nMinimum rounds for avalanche (>= 45%): {min_secure_aval}")
        print(f"Minimum rounds for distribution (<2% dev): {min_secure_dist}")
        print(f"Minimum secure rounds (combined): {min_secure}")
        print(f"Current rounds: 64")
        print(f"Security margin: {64 - min_secure} rounds ({(64 - min_secure) / 64 * 100:.1f}%)")

        recommended = min_secure + 16  # Add 16 rounds safety margin
        if recommended < 64:
            speedup = 64 / recommended
            print(f"\nRECOMMENDATION: Could reduce to {recommended} rounds")
            print(f"               Expected speedup: ~{speedup:.1f}x")
            print(f"               Security margin: 16 rounds")
    else:
        print("\nWARNING: Could not determine minimum secure configuration!")


if __name__ == "__main__":
    main()
