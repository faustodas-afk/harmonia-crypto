# HARMONIA

**A 256-bit Cryptographic Hash Function Based on Golden Ratio Dynamics and Temporal Quasicrystals**

[![Version](https://img.shields.io/badge/version-2.2-blue.svg)](https://github.com/faustodas-afk/harmonia-crypto)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![C](https://img.shields.io/badge/C-C99-orange.svg)](https://en.wikipedia.org/wiki/C99)

## Overview

HARMONIA is an experimental cryptographic hash function that explores **cryptographic biodiversity** — whether fundamentally different mathematical foundations can yield viable cryptographic constructions.

### Why HARMONIA?

Modern cryptography relies on a small set of algorithms sharing common foundations (SHA-256, SHA-3, BLAKE). If a breakthrough in cryptanalysis targets these shared foundations, the entire ecosystem could be vulnerable. HARMONIA deliberately uses **different mathematical foundations** as a research exploration and potential backup option.

| Aspect | Traditional (SHA-256) | HARMONIA |
|--------|----------------------|----------|
| Constants | √2, √3 fractional parts | Golden ratio (φ) powers |
| Scheduling | Linear/periodic | Fibonacci word (quasi-periodic) |
| Rotations | Fixed per round | Quasicrystal projection (variable) |
| State | Single stream | Dual stream (φ and 1/φ) |

### Key Features

- **Golden Ratio Constants** - State initialization and mixing based on φ = (1+√5)/2
- **Fibonacci Word Scheduling** - Quasi-periodic round selection using the infinite Fibonacci word
- **Quasicrystalline Rotations** - Rotation amounts derived from 2D Penrose tiling projections
- **Dual-Stream Architecture** - Parallel golden (φ) and complementary (ψ) state processing
- **Edge Protection** - Boundary mixing inspired by topological quantum phases

## Cryptographic Properties

Tested against SHA-256 on standard cryptographic metrics:

| Test | HARMONIA | SHA-256 |
|------|----------|---------|
| Avalanche Effect | 50.02% | 49.97% |
| Bit Distribution | 49.97% | 50.01% |
| Bit Independence (χ²) | 0.31 | 3.03 |
| Byte Distribution (χ²) | 240.65 | 293.70 |
| Near-Collision (min bits) | 84 | 90 |
| SAC Deviation | 3.51% | 3.57% |

**Total Score: HARMONIA 670.0 vs SHA-256 637.7**

> ⚠️ **Security Status**: HARMONIA is an experimental algorithm for **research purposes only**. It has NOT undergone formal cryptanalysis by the cryptographic community. Production systems **must** use established algorithms (SHA-256, SHA-3, BLAKE3) until HARMONIA receives thorough independent analysis. The value lies in exploring alternative mathematical foundations, not in replacing proven algorithms today.

## Quick Start

### Python

```python
from harmonia import harmonia

# Hash bytes
digest = harmonia(b"Hello, World!")
print(digest.hex())

# Hash string
digest = harmonia("your message".encode())
```

### C

```c
#include "harmonia.h"

uint8_t digest[32];
harmonia((uint8_t*)"Hello, World!", 13, digest);

// Or use hex output
char hex[65];
harmonia_hex((uint8_t*)"Hello, World!", 13, hex);
printf("%s\n", hex);
```

Build:
```bash
make
./harmonia_test --test
```

## Test Vectors

```
Input: "" (empty)
HARMONIA: 3acc512691bd37d475cec1695d99503b4a3401aa9366b312951ba200190bfe3d

Input: "abc"
HARMONIA: a165d969cbc672777da6746c4e1462dead0d2fa7f75a75fef4fb33afd07bc1ff

Input: "The quick brown fox jumps over the lazy dog"
HARMONIA: 39661e930dae99563e597b155d177e331d3016fa65405624c3b2159b9c86b4aa

Input: "HARMONIA"
HARMONIA: 4ad655d4614e11f2e839bfa5f0f2cce13bde89ea9327434a941411f21b65fad3
```

## Installation

### Python
```bash
# No dependencies required
cp harmonia.py your_project/
```

### C
```bash
git clone https://github.com/faustodas-afk/harmonia-crypto.git
cd harmonia-crypto
make
```

## Performance

**HARMONIA is slow.** This is a deliberate trade-off for cryptographic diversity.

| Algorithm | Throughput | Relative |
|-----------|------------|----------|
| SHA-256 (OpenSSL, SHA-NI) | ~2,500 MB/s | 31x |
| BLAKE3 (optimized) | ~4,000 MB/s | 50x |
| SHA-3-256 | ~800 MB/s | 10x |
| **HARMONIA-Fast** (32 rounds) | ~173 MB/s | 2.1x |
| **HARMONIA-64** | ~80 MB/s | 1x (baseline) |
| Python (reference) | ~0.2 MB/s | — |

The performance gap exists because:
- No hardware acceleration (unlike SHA-NI for SHA-256)
- Variable rotations prevent SIMD optimization
- Dual-stream architecture doubles state operations

**Implications:** HARMONIA is unsuitable for high-throughput applications. It may be acceptable for key derivation, digital signatures on small messages, or defense-in-depth scenarios.

## Project Structure

```
harmonia-crypto/
├── harmonia.py           # Python reference implementation
├── harmonia_xof.py       # HARMONIA-XOF (Sponge/XOF variant)
├── harmonia.c            # C implementation
├── harmonia.h            # C header
├── harmonia_simd.c       # SIMD experimental (ARM NEON)
├── main.c                # C test driver and benchmarks
├── Makefile              # Build system
├── crypto_tests.py       # Cryptographic quality tests
├── reduced_rounds_test.py # Security margin analysis
├── HARMONIA_Whitepaper.md # Technical specification
└── LICENSE               # MIT License
```

## HARMONIA-XOF (Extendable Output)

Sponge construction for arbitrary-length output:

```python
from harmonia_xof import harmonia_xof, HarmoniaXOF

# Fixed length output
digest = harmonia_xof(b"message", output_length=64)

# Streaming
xof = HarmoniaXOF()
xof.absorb(b"message")
output = xof.squeeze(1024)  # 1024 bytes
```

| Parameter | Value |
|-----------|-------|
| Rate | 256 bits |
| Capacity | 256 bits |
| Security | 128 bits |
| Rounds | 24 |

## HARMONIA-Fast (32-Round Variant)

Performance-optimized variant with 2x speedup:

```python
from harmonia_fast import harmonia_fast

digest = harmonia_fast(b"message")  # 173 MB/s vs 80 MB/s
```

| Variant | Throughput | Security Margin |
|---------|------------|-----------------|
| HARMONIA-64 | ~80 MB/s | 56 rounds (7x) |
| HARMONIA-Fast | ~173 MB/s | 24 rounds (4x) |

## Algorithm Summary

```
┌─────────────────────────────────────────────────────────┐
│                    HARMONIA v2.2                        │
├─────────────────────────────────────────────────────────┤
│  Block Size:     512 bits (64 bytes)                    │
│  Digest Size:    256 bits (32 bytes)                    │
│  Word Size:      32 bits                                │
│  Rounds:         64 (56 security margin)                │
│  Construction:   Davies-Meyer + Merkle-Damgård          │
└─────────────────────────────────────────────────────────┘

Round Function:
  1. Select mixing type via Fibonacci word (golden/complementary)
  2. Apply ARX operations with φ-derived constants
  3. Quasicrystalline rotation from Penrose projection
  4. Cross-stream diffusion every 8 rounds
  5. Edge protection at boundaries
```

## Running Tests

### Correctness Tests
```bash
# Python
python3 harmonia.py

# C
make test
```

### Cryptographic Quality Tests
```bash
python3 crypto_tests.py
```

### Benchmarks
```bash
make benchmark
```

## Contributing

Contributions welcome, especially:

- **Cryptanalysis** - Differential, linear, algebraic attacks
- **Security Proofs** - Formal verification of claimed properties
- **Optimizations** - SIMD, GPU implementations
- **Test Vectors** - Extended test suites

Please open an issue or pull request.

## References

- [Whitepaper (PDF)](HARMONIA_Whitepaper.pdf) - Full technical specification
- [Whitepaper (Markdown)](HARMONIA_Whitepaper.md) - Source document

### Related Work

- Dumitrescu, P.T. et al. "Dynamical topological phase realized in a trapped-ion quantum simulator" Nature 607, 463–467 (2022) — *Inspiration for quasi-periodic structures*
- Bertoni, G. et al. "Keccak" (SHA-3) (2012)
- Aumasson, J.-P. & Bernstein, D.J. "SipHash: a fast short-input PRF" (2012)
- Biham, E. & Shamir, A. "Differential cryptanalysis of DES-like cryptosystems" (1991)
- Matsui, M. "Linear cryptanalysis method for DES cipher" (1993)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Authors

- **Fausto Das** - Initial design and implementation

---

*HARMONIA: Where mathematics meets cryptography through the lens of quasicrystals.*
