#!/usr/bin/env python3
"""
HARMONIA-NG Security Validation Test Suite

Comprehensive cryptographic quality tests for HARMONIA-NG:
- Avalanche effect analysis
- Bit distribution uniformity
- Reduced-rounds diffusion analysis
- Comparison with HARMONIA-64 and SHA-256
"""

import os
import random
import struct
import hashlib
import time
from typing import List, Tuple, Dict
from collections import Counter

# Import HARMONIA implementations
from harmonia_ng import harmonia_ng, harmonia_ng_hex, NUM_ROUNDS as NG_ROUNDS
from harmonia import harmonia, harmonia_hex


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def hamming_distance(a: bytes, b: bytes) -> int:
    """Count differing bits between two byte sequences."""
    return sum(bin(x ^ y).count('1') for x, y in zip(a, b))


def flip_bit(data: bytes, bit_pos: int) -> bytes:
    """Flip a single bit in the data."""
    byte_pos = bit_pos // 8
    bit_offset = bit_pos % 8

    data_list = list(data)
    data_list[byte_pos] ^= (1 << bit_offset)
    return bytes(data_list)


def sha256(data: bytes) -> bytes:
    """Reference SHA-256 implementation."""
    return hashlib.sha256(data).digest()


# ============================================================================
# AVALANCHE EFFECT TESTS
# ============================================================================

def test_avalanche_effect(hash_func, name: str, num_samples: int = 1000) -> Dict:
    """
    Test avalanche effect: single bit flip should change ~50% of output bits.
    """
    print(f"\n{'='*60}")
    print(f"Avalanche Effect Test: {name}")
    print(f"{'='*60}")

    bit_changes = []

    for _ in range(num_samples):
        # Generate random message
        msg_len = random.randint(1, 128)
        msg = os.urandom(msg_len)

        # Compute original hash
        hash1 = hash_func(msg)

        # Flip random bit
        bit_pos = random.randint(0, len(msg) * 8 - 1)
        msg_flipped = flip_bit(msg, bit_pos)

        # Compute hash of flipped message
        hash2 = hash_func(msg_flipped)

        # Count bit changes
        diff = hamming_distance(hash1, hash2)
        bit_changes.append(diff)

    # Statistics
    mean_diff = sum(bit_changes) / len(bit_changes)
    min_diff = min(bit_changes)
    max_diff = max(bit_changes)

    # Standard deviation
    variance = sum((x - mean_diff) ** 2 for x in bit_changes) / len(bit_changes)
    std_dev = variance ** 0.5

    # Percentage
    mean_percent = mean_diff / 256 * 100

    print(f"  Samples:     {num_samples}")
    print(f"  Mean diff:   {mean_diff:.2f}/256 bits ({mean_percent:.2f}%)")
    print(f"  Min diff:    {min_diff}/256 bits")
    print(f"  Max diff:    {max_diff}/256 bits")
    print(f"  Std dev:     {std_dev:.2f}")

    # Pass criteria: mean between 45% and 55%
    passed = 45.0 <= mean_percent <= 55.0
    print(f"  Status:      {'PASS' if passed else 'FAIL'}")

    return {
        'mean': mean_diff,
        'min': min_diff,
        'max': max_diff,
        'std_dev': std_dev,
        'percent': mean_percent,
        'passed': passed
    }


# ============================================================================
# BIT DISTRIBUTION TESTS
# ============================================================================

def test_bit_distribution(hash_func, name: str, num_samples: int = 1000) -> Dict:
    """
    Test that output bits are uniformly distributed (50% ones).
    """
    print(f"\n{'='*60}")
    print(f"Bit Distribution Test: {name}")
    print(f"{'='*60}")

    total_bits = 0
    total_ones = 0

    for i in range(num_samples):
        msg = os.urandom(random.randint(1, 256))
        digest = hash_func(msg)

        ones = sum(bin(b).count('1') for b in digest)
        total_ones += ones
        total_bits += 256

    percent_ones = total_ones / total_bits * 100
    deviation = abs(percent_ones - 50.0)

    print(f"  Samples:     {num_samples}")
    print(f"  Total bits:  {total_bits}")
    print(f"  Ones:        {total_ones} ({percent_ones:.2f}%)")
    print(f"  Deviation:   {deviation:.3f}%")

    # Pass criteria: within 1% of 50%
    passed = deviation < 1.0
    print(f"  Status:      {'PASS' if passed else 'FAIL'}")

    return {
        'percent_ones': percent_ones,
        'deviation': deviation,
        'passed': passed
    }


# ============================================================================
# REDUCED ROUNDS ANALYSIS
# ============================================================================

def test_reduced_rounds_ng() -> Dict:
    """
    Analyze diffusion at different round counts for HARMONIA-NG.

    This requires modifying the round count, so we re-implement
    a minimal version of the compression function.
    """
    print(f"\n{'='*60}")
    print(f"Reduced Rounds Diffusion Analysis: HARMONIA-NG")
    print(f"{'='*60}")

    from harmonia_ng import (
        _compress, _finalize, _pad_message,
        INITIAL_HASH_G, INITIAL_HASH_C,
        _quarter_round, _cross_stream_diffusion, _edge_protection,
        _expand_message, ROUND_ROTATIONS, PHI_CONSTANTS, RECIPROCAL_CONSTANTS,
        STATE_WORDS, MASK32
    )

    def compress_reduced(block: bytes, state_g: List[int], state_c: List[int],
                         rounds: int) -> Tuple[List[int], List[int]]:
        """Compression with variable round count."""
        w = _expand_message(block)

        g = list(state_g)
        c = list(state_c)

        for r in range(rounds):
            r1, r2, r3, r4 = ROUND_ROTATIONS[r % len(ROUND_ROTATIONS)]
            k_phi = PHI_CONSTANTS[r % 16]
            k_rec = RECIPROCAL_CONSTANTS[r % 16]

            g[0] = (g[0] + w[r % len(w)]) & MASK32
            c[0] = (c[0] + w[(len(w) - 1 - r) % len(w)]) & MASK32

            g[4] ^= k_phi
            c[4] ^= k_rec

            _quarter_round(g, 0, 1, 2, 3, r1, r2, r3, r4)
            _quarter_round(g, 4, 5, 6, 7, r1, r2, r3, r4)
            _quarter_round(g, 0, 5, 2, 7, r1, r2, r3, r4)
            _quarter_round(g, 4, 1, 6, 3, r1, r2, r3, r4)

            _quarter_round(c, 0, 1, 2, 3, r1, r2, r3, r4)
            _quarter_round(c, 4, 5, 6, 7, r1, r2, r3, r4)
            _quarter_round(c, 0, 5, 2, 7, r1, r2, r3, r4)
            _quarter_round(c, 4, 1, 6, 3, r1, r2, r3, r4)

            if (r + 1) % 4 == 0:
                _cross_stream_diffusion(g, c)

            if (r + 1) % 8 == 0:
                _edge_protection(g, r)
                _edge_protection(c, r)

        new_g = [(state_g[i] + g[i]) & MASK32 for i in range(STATE_WORDS)]
        new_c = [(state_c[i] + c[i]) & MASK32 for i in range(STATE_WORDS)]

        return new_g, new_c

    def hash_reduced(msg: bytes, rounds: int) -> bytes:
        """Hash with reduced rounds."""
        state_g = list(INITIAL_HASH_G)
        state_c = list(INITIAL_HASH_C)

        padded = _pad_message(msg)
        for i in range(0, len(padded), 64):
            block = padded[i:i+64]
            state_g, state_c = compress_reduced(block, state_g, state_c, rounds)

        return _finalize(state_g, state_c)

    results = {}
    round_counts = [1, 2, 4, 6, 8, 12, 16, 24, 32]

    print(f"  {'Rounds':<8} {'Mean Diff':<12} {'Min':<6} {'Status':<10}")
    print(f"  {'-'*40}")

    for rounds in round_counts:
        diffs = []
        num_samples = 100

        for _ in range(num_samples):
            msg = os.urandom(32)
            h1 = hash_reduced(msg, rounds)

            msg_flipped = flip_bit(msg, random.randint(0, 255))
            h2 = hash_reduced(msg_flipped, rounds)

            diffs.append(hamming_distance(h1, h2))

        mean_diff = sum(diffs) / len(diffs)
        min_diff = min(diffs)
        percent = mean_diff / 256 * 100

        status = "SECURE" if percent >= 45.0 else "WEAK"
        print(f"  {rounds:<8} {mean_diff:<12.1f} {min_diff:<6} {status:<10}")

        results[rounds] = {
            'mean': mean_diff,
            'min': min_diff,
            'percent': percent,
            'secure': percent >= 45.0
        }

    # Find saturation point
    saturation_round = None
    for rounds in sorted(results.keys()):
        if results[rounds]['percent'] >= 45.0:
            saturation_round = rounds
            break

    security_margin = 32 - saturation_round if saturation_round else 0

    print(f"\n  Saturation round: {saturation_round}")
    print(f"  Security margin:  {security_margin} rounds ({security_margin / 32 * 100:.0f}%)")

    return results


# ============================================================================
# COMPARISON TESTS
# ============================================================================

def compare_algorithms() -> None:
    """
    Compare HARMONIA-NG with HARMONIA-64 and SHA-256.
    """
    print(f"\n{'='*60}")
    print(f"Algorithm Comparison")
    print(f"{'='*60}")

    algorithms = [
        ("HARMONIA-NG", harmonia_ng),
        ("HARMONIA-64", harmonia),
        ("SHA-256", sha256),
    ]

    results = {}

    for name, func in algorithms:
        print(f"\nTesting {name}...")

        # Avalanche test
        av = test_avalanche_effect(func, name, num_samples=500)

        # Bit distribution test
        bd = test_bit_distribution(func, name, num_samples=500)

        results[name] = {
            'avalanche': av,
            'bit_distribution': bd
        }

    # Summary
    print(f"\n{'='*60}")
    print(f"Comparison Summary")
    print(f"{'='*60}")
    print(f"  {'Algorithm':<15} {'Avalanche':<12} {'Bit Dist':<12} {'Score':<8}")
    print(f"  {'-'*50}")

    for name in results:
        av_pass = "PASS" if results[name]['avalanche']['passed'] else "FAIL"
        bd_pass = "PASS" if results[name]['bit_distribution']['passed'] else "FAIL"
        score = (results[name]['avalanche']['passed'] +
                 results[name]['bit_distribution']['passed'])
        print(f"  {name:<15} {av_pass:<12} {bd_pass:<12} {score}/2")


# ============================================================================
# BENCHMARK
# ============================================================================

def benchmark() -> None:
    """
    Benchmark HARMONIA-NG vs other algorithms.
    """
    print(f"\n{'='*60}")
    print(f"Performance Benchmark")
    print(f"{'='*60}")

    algorithms = [
        ("HARMONIA-NG", harmonia_ng),
        ("HARMONIA-64", harmonia),
        ("SHA-256", sha256),
    ]

    data_sizes = [64, 1024, 10240]  # bytes
    iterations = 1000

    print(f"  {'Algorithm':<15} {'64B':<12} {'1KB':<12} {'10KB':<12}")
    print(f"  {'-'*55}")

    for name, func in algorithms:
        times = []

        for size in data_sizes:
            data = os.urandom(size)

            start = time.perf_counter()
            for _ in range(iterations):
                func(data)
            elapsed = time.perf_counter() - start

            throughput = (size * iterations) / elapsed / 1024 / 1024  # MB/s
            times.append(f"{throughput:.1f} MB/s")

        print(f"  {name:<15} {times[0]:<12} {times[1]:<12} {times[2]:<12}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 60)
    print("HARMONIA-NG Security Validation Test Suite")
    print("=" * 60)

    # Run all tests
    test_avalanche_effect(harmonia_ng, "HARMONIA-NG", num_samples=1000)
    test_bit_distribution(harmonia_ng, "HARMONIA-NG", num_samples=1000)
    test_reduced_rounds_ng()
    compare_algorithms()
    benchmark()

    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
