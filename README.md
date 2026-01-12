# HARMONIA

**A 256-bit Cryptographic Hash Function Based on Golden Ratio Dynamics and Temporal Quasicrystals**

[![Version](https://img.shields.io/badge/version-2.2-blue.svg)](https://github.com/faustodas-afk/harmonia-crypto)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![C](https://img.shields.io/badge/C-C99-orange.svg)](https://en.wikipedia.org/wiki/C99)

## Overview

HARMONIA is an experimental cryptographic hash function that explores novel mathematical structures for bit diffusion:

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

> ⚠️ **Disclaimer**: HARMONIA is experimental and has not undergone formal cryptanalysis. Do not use in production systems requiring proven security.

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

| Implementation | Throughput | Notes |
|---------------|------------|-------|
| Python | ~0.2 MB/s | Reference implementation |
| C (scalar) | ~80 MB/s | Optimized with -O3 -march=native |
| SHA-256 (OpenSSL) | ~500 MB/s | Hardware-accelerated |

HARMONIA prioritizes novel cryptographic structure over raw speed.

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

- Boneh, D. et al. "Random Oracles are Practical" (1993)
- Daemen, J. & Rijmen, V. "The Design of Rijndael" (2002)
- Bertoni, G. et al. "Keccak" (SHA-3) (2012)
- Aumasson, J.P. "Serious Cryptography" (2017)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Authors

- **Fausto Das** - Initial design and implementation

---

*HARMONIA: Where mathematics meets cryptography through the lens of quasicrystals.*
