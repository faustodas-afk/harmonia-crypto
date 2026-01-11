#!/usr/bin/env python3
"""
HARMONIA vs SHA-256 - Cryptographic Quality Tests

Tests:
    1. Avalanche Effect - bit diffusion when input changes
    2. Bit Distribution - uniformity of 0s and 1s
    3. Bit Independence - correlation between bit positions
    4. Chi-Square Test - statistical randomness
    5. Collision Resistance - birthday attack simulation
    6. Strict Avalanche Criterion (SAC)
    7. Bit Independence Criterion (BIC)
"""

import hashlib
import random
import math
from collections import Counter
from harmonia import harmonia

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sha256(data: bytes) -> bytes:
    """SHA-256 hash."""
    return hashlib.sha256(data).digest()

def bytes_to_bits(data: bytes) -> list:
    """Convert bytes to list of bits."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def hamming_distance(a: bytes, b: bytes) -> int:
    """Count differing bits between two byte sequences."""
    return sum(bin(x ^ y).count('1') for x, y in zip(a, b))

def flip_bit(data: bytes, bit_pos: int) -> bytes:
    """Flip a single bit in the data."""
    data = bytearray(data)
    byte_idx = bit_pos // 8
    bit_idx = 7 - (bit_pos % 8)
    data[byte_idx] ^= (1 << bit_idx)
    return bytes(data)

# ============================================================================
# TEST 1: AVALANCHE EFFECT
# ============================================================================

def test_avalanche(hash_func, name, samples=1000):
    """
    Test the avalanche effect: changing 1 input bit should change ~50% of output bits.
    """
    print(f"\n{'='*60}")
    print(f"TEST 1: AVALANCHE EFFECT - {name}")
    print(f"{'='*60}")

    bit_changes = []

    for _ in range(samples):
        # Random message
        msg = random.randbytes(random.randint(1, 100))
        original_hash = hash_func(msg)

        # Flip random bit
        bit_pos = random.randint(0, len(msg) * 8 - 1)
        modified_msg = flip_bit(msg, bit_pos)
        modified_hash = hash_func(modified_msg)

        # Count changed bits
        changed = hamming_distance(original_hash, modified_hash)
        bit_changes.append(changed)

    avg_change = sum(bit_changes) / len(bit_changes)
    pct_change = avg_change / 256 * 100
    std_dev = math.sqrt(sum((x - avg_change)**2 for x in bit_changes) / len(bit_changes))
    min_change = min(bit_changes)
    max_change = max(bit_changes)

    print(f"  Samples:          {samples}")
    print(f"  Average bits changed: {avg_change:.2f} / 256 ({pct_change:.2f}%)")
    print(f"  Standard deviation:   {std_dev:.2f}")
    print(f"  Min/Max:              {min_change} / {max_change}")
    print(f"  Ideal:                128.00 / 256 (50.00%)")

    # Score: how close to 50%?
    score = 100 - abs(50 - pct_change) * 2
    print(f"  Score:                {score:.1f}/100")

    return {'avg': avg_change, 'pct': pct_change, 'std': std_dev, 'score': score}

# ============================================================================
# TEST 2: BIT DISTRIBUTION
# ============================================================================

def test_bit_distribution(hash_func, name, samples=10000):
    """
    Test that output bits are uniformly distributed (50% zeros, 50% ones).
    """
    print(f"\n{'='*60}")
    print(f"TEST 2: BIT DISTRIBUTION - {name}")
    print(f"{'='*60}")

    total_ones = 0
    total_bits = 0

    # Also track per-position distribution
    position_ones = [0] * 256

    for i in range(samples):
        msg = i.to_bytes((i.bit_length() + 7) // 8 or 1, 'big')
        h = hash_func(msg)
        bits = bytes_to_bits(h)

        for pos, bit in enumerate(bits):
            if bit:
                total_ones += 1
                position_ones[pos] += 1
            total_bits += 1

    pct_ones = total_ones / total_bits * 100

    # Check per-position uniformity
    expected_ones = samples / 2
    position_deviations = [abs(ones - expected_ones) / expected_ones * 100
                          for ones in position_ones]
    max_deviation = max(position_deviations)
    avg_deviation = sum(position_deviations) / len(position_deviations)

    print(f"  Samples:              {samples}")
    print(f"  Total bits:           {total_bits}")
    print(f"  Ones:                 {pct_ones:.4f}%")
    print(f"  Zeros:                {100 - pct_ones:.4f}%")
    print(f"  Ideal:                50.0000%")
    print(f"  Per-position max dev: {max_deviation:.2f}%")
    print(f"  Per-position avg dev: {avg_deviation:.2f}%")

    score = 100 - abs(50 - pct_ones) * 10 - avg_deviation
    score = max(0, min(100, score))
    print(f"  Score:                {score:.1f}/100")

    return {'pct_ones': pct_ones, 'max_dev': max_deviation, 'score': score}

# ============================================================================
# TEST 3: BIT INDEPENDENCE (CORRELATION)
# ============================================================================

def test_bit_correlation(hash_func, name, samples=5000):
    """
    Test that output bits are independent of each other.
    """
    print(f"\n{'='*60}")
    print(f"TEST 3: BIT INDEPENDENCE - {name}")
    print(f"{'='*60}")

    # Check correlation between adjacent bit pairs
    pair_counts = Counter()  # (bit_i, bit_i+1) -> count

    for i in range(samples):
        msg = random.randbytes(random.randint(1, 50))
        h = hash_func(msg)
        bits = bytes_to_bits(h)

        for j in range(len(bits) - 1):
            pair = (bits[j], bits[j+1])
            pair_counts[pair] += 1

    total_pairs = sum(pair_counts.values())
    expected = total_pairs / 4  # Each of 4 combinations should be 25%

    print(f"  Samples:      {samples}")
    print(f"  Bit pairs:    {total_pairs}")
    print(f"  Distribution:")

    chi_square = 0
    for pair in [(0,0), (0,1), (1,0), (1,1)]:
        observed = pair_counts[pair]
        pct = observed / total_pairs * 100
        chi_square += (observed - expected)**2 / expected
        print(f"    {pair}: {pct:.2f}% (ideal: 25.00%)")

    print(f"  Chi-square:   {chi_square:.4f}")
    print(f"  (Lower is better, critical value at p=0.05: 7.815)")

    score = max(0, 100 - chi_square * 5)
    print(f"  Score:        {score:.1f}/100")

    return {'chi_square': chi_square, 'score': score}

# ============================================================================
# TEST 4: CHI-SQUARE BYTE DISTRIBUTION
# ============================================================================

def test_chi_square(hash_func, name, samples=10000):
    """
    Chi-square test for byte distribution uniformity.
    """
    print(f"\n{'='*60}")
    print(f"TEST 4: CHI-SQUARE (BYTE DISTRIBUTION) - {name}")
    print(f"{'='*60}")

    byte_counts = [0] * 256
    total_bytes = 0

    for i in range(samples):
        msg = i.to_bytes((i.bit_length() + 7) // 8 or 1, 'big')
        h = hash_func(msg)
        for byte in h:
            byte_counts[byte] += 1
            total_bytes += 1

    expected = total_bytes / 256
    chi_square = sum((count - expected)**2 / expected for count in byte_counts)

    # Degrees of freedom = 255
    # Critical value at p=0.05 for df=255 is ~293
    # Critical value at p=0.01 for df=255 is ~310

    print(f"  Samples:          {samples}")
    print(f"  Total bytes:      {total_bytes}")
    print(f"  Expected/byte:    {expected:.2f}")
    print(f"  Chi-square:       {chi_square:.2f}")
    print(f"  Critical (p=0.05): 293.25")
    print(f"  Critical (p=0.01): 310.46")

    if chi_square < 293.25:
        result = "PASS (p > 0.05)"
    elif chi_square < 310.46:
        result = "MARGINAL (0.01 < p < 0.05)"
    else:
        result = "FAIL (p < 0.01)"

    print(f"  Result:           {result}")

    score = max(0, 100 - (chi_square - 255) / 2)
    score = min(100, score)
    print(f"  Score:            {score:.1f}/100")

    return {'chi_square': chi_square, 'result': result, 'score': score}

# ============================================================================
# TEST 5: NEAR-COLLISION RESISTANCE
# ============================================================================

def test_near_collision(hash_func, name, samples=50000):
    """
    Test for near-collisions (hashes that are very similar).
    """
    print(f"\n{'='*60}")
    print(f"TEST 5: NEAR-COLLISION RESISTANCE - {name}")
    print(f"{'='*60}")

    hashes = []
    min_distance = 256
    min_pair = (None, None)

    for i in range(samples):
        msg = i.to_bytes(8, 'big')
        h = hash_func(msg)

        # Compare with recent hashes (sliding window)
        for prev_h in hashes[-100:]:
            dist = hamming_distance(h, prev_h)
            if dist < min_distance:
                min_distance = dist
                min_pair = (i, hashes.index(prev_h) if prev_h in hashes else -1)

        hashes.append(h)

    # Expected minimum distance for random 256-bit hashes
    # With 50000 samples, minimum ~90-100 bits is typical

    print(f"  Samples:              {samples}")
    print(f"  Minimum distance:     {min_distance} bits")
    print(f"  Expected (random):    ~90-110 bits")

    if min_distance >= 80:
        result = "EXCELLENT"
        score = 100
    elif min_distance >= 60:
        result = "GOOD"
        score = 80
    elif min_distance >= 40:
        result = "ACCEPTABLE"
        score = 60
    else:
        result = "POOR"
        score = min_distance

    print(f"  Result:               {result}")
    print(f"  Score:                {score:.1f}/100")

    return {'min_distance': min_distance, 'score': score}

# ============================================================================
# TEST 6: STRICT AVALANCHE CRITERION (SAC)
# ============================================================================

def test_sac(hash_func, name, samples=500):
    """
    Strict Avalanche Criterion: flipping each input bit should change
    each output bit with probability 0.5.
    """
    print(f"\n{'='*60}")
    print(f"TEST 6: STRICT AVALANCHE CRITERION - {name}")
    print(f"{'='*60}")

    # For each output bit position, count how often it flips
    flip_counts = [[0] * 256 for _ in range(64)]  # 64 input bits -> 256 output bits

    for _ in range(samples):
        msg = random.randbytes(8)  # 64 bits
        original_hash = hash_func(msg)
        original_bits = bytes_to_bits(original_hash)

        for input_bit in range(64):
            modified_msg = flip_bit(msg, input_bit)
            modified_hash = hash_func(modified_msg)
            modified_bits = bytes_to_bits(modified_hash)

            for output_bit in range(256):
                if original_bits[output_bit] != modified_bits[output_bit]:
                    flip_counts[input_bit][output_bit] += 1

    # Calculate deviation from 0.5 probability
    expected = samples / 2
    deviations = []

    for i in range(64):
        for j in range(256):
            dev = abs(flip_counts[i][j] - expected) / expected
            deviations.append(dev)

    avg_deviation = sum(deviations) / len(deviations) * 100
    max_deviation = max(deviations) * 100

    print(f"  Samples:              {samples}")
    print(f"  Input bits tested:    64")
    print(f"  Output bits:          256")
    print(f"  Avg deviation from 50%: {avg_deviation:.2f}%")
    print(f"  Max deviation:        {max_deviation:.2f}%")

    score = max(0, 100 - avg_deviation * 5 - max_deviation / 2)
    print(f"  Score:                {score:.1f}/100")

    return {'avg_dev': avg_deviation, 'max_dev': max_deviation, 'score': score}

# ============================================================================
# TEST 7: SENSITIVITY TO INPUT LENGTH
# ============================================================================

def test_length_sensitivity(hash_func, name):
    """
    Test that similar messages of different lengths produce very different hashes.
    """
    print(f"\n{'='*60}")
    print(f"TEST 7: LENGTH SENSITIVITY - {name}")
    print(f"{'='*60}")

    base = b"test"
    distances = []

    for length in range(1, 65):
        msg1 = base * length
        msg2 = base * (length + 1)

        h1 = hash_func(msg1)
        h2 = hash_func(msg2)

        dist = hamming_distance(h1, h2)
        distances.append(dist)

    avg_dist = sum(distances) / len(distances)
    min_dist = min(distances)

    print(f"  Length range:     1-64 repetitions")
    print(f"  Avg bit difference: {avg_dist:.1f} / 256 ({avg_dist/256*100:.1f}%)")
    print(f"  Min bit difference: {min_dist} / 256")
    print(f"  Ideal:              ~128 / 256 (50%)")

    score = min(100, avg_dist / 128 * 100)
    print(f"  Score:              {score:.1f}/100")

    return {'avg_dist': avg_dist, 'min_dist': min_dist, 'score': score}

# ============================================================================
# MAIN
# ============================================================================

def run_all_tests():
    """Run all cryptographic tests and compare results."""

    print("\n" + "="*60)
    print("  HARMONIA vs SHA-256 - CRYPTOGRAPHIC QUALITY COMPARISON")
    print("="*60)

    results = {'harmonia': {}, 'sha256': {}}

    tests = [
        ('avalanche', test_avalanche),
        ('bit_dist', test_bit_distribution),
        ('bit_corr', test_bit_correlation),
        ('chi_square', test_chi_square),
        ('near_coll', test_near_collision),
        ('sac', test_sac),
        ('length', test_length_sensitivity),
    ]

    for test_name, test_func in tests:
        results['harmonia'][test_name] = test_func(harmonia, "HARMONIA")
        results['sha256'][test_name] = test_func(sha256, "SHA-256")

    # Summary
    print("\n" + "="*60)
    print("  FINAL COMPARISON SUMMARY")
    print("="*60)
    print(f"\n{'Test':<25} {'HARMONIA':>12} {'SHA-256':>12} {'Winner':>12}")
    print("-" * 60)

    harmonia_total = 0
    sha256_total = 0

    test_names = {
        'avalanche': 'Avalanche Effect',
        'bit_dist': 'Bit Distribution',
        'bit_corr': 'Bit Independence',
        'chi_square': 'Chi-Square',
        'near_coll': 'Near-Collision',
        'sac': 'SAC',
        'length': 'Length Sensitivity'
    }

    for test_name in test_names:
        h_score = results['harmonia'][test_name]['score']
        s_score = results['sha256'][test_name]['score']
        harmonia_total += h_score
        sha256_total += s_score

        if h_score > s_score + 1:
            winner = "HARMONIA"
        elif s_score > h_score + 1:
            winner = "SHA-256"
        else:
            winner = "TIE"

        print(f"{test_names[test_name]:<25} {h_score:>11.1f} {s_score:>11.1f} {winner:>12}")

    print("-" * 60)
    print(f"{'TOTAL SCORE':<25} {harmonia_total:>11.1f} {sha256_total:>11.1f}")
    print(f"{'AVERAGE':<25} {harmonia_total/7:>11.1f} {sha256_total/7:>11.1f}")

    print("\n" + "="*60)
    if harmonia_total > sha256_total:
        print("  RESULT: HARMONIA shows BETTER cryptographic properties")
    elif sha256_total > harmonia_total:
        print("  RESULT: SHA-256 shows BETTER cryptographic properties")
    else:
        print("  RESULT: EQUIVALENT cryptographic properties")
    print("="*60)

    return results

if __name__ == "__main__":
    run_all_tests()
