#!/usr/bin/env python3
"""
HARMONIA-XOF: Extendable Output Function based on HARMONIA

Sponge construction providing:
- Arbitrary length output (XOF)
- 128-bit security level
- Rate: 256 bits (32 bytes)
- Capacity: 256 bits (32 bytes)
- Total state: 512 bits (dual stream)

Usage:
    # Fixed length hash (like SHAKE)
    digest = harmonia_xof(b"message", output_length=64)

    # Streaming output
    xof = HarmoniaXOF()
    xof.absorb(b"message")
    output = xof.squeeze(1024)  # Get 1024 bytes
"""

import struct
from typing import List, Tuple

# Import core HARMONIA functions
from harmonia import (
    _rotr, _rotl, _quasicrystal_rotation, _penrose_index,
    _mix_golden, _mix_complementary, _edge_protection,
    PHI_CONSTANTS, RECIPROCAL_CONSTANTS, FIBONACCI_WORD, FIBONACCI
)

VERSION = "1.0"
RATE = 32        # 256 bits - bytes absorbed/squeezed per permutation
CAPACITY = 32    # 256 bits - security parameter (128-bit security)
STATE_SIZE = 64  # 512 bits total
ROUNDS = 24      # Reduced rounds for XOF (still secure per analysis)

MASK32 = 0xFFFFFFFF


def _permutation(state_g: List[int], state_c: List[int], rounds: int = ROUNDS) -> Tuple[List[int], List[int]]:
    """
    HARMONIA permutation function for Sponge construction.
    Processes the full 512-bit state without message injection.
    """
    g = state_g[:]
    c = state_c[:]

    for r in range(rounds):
        round_type = FIBONACCI_WORD[r % 64]
        k_phi = PHI_CONSTANTS[r % 16]
        k_rec = RECIPROCAL_CONSTANTS[r % 16]

        # Mix based on round type
        if round_type == 'A':
            for idx in range(4):
                i = idx
                j = (idx + 4) % 8
                g[i], g[j] = _mix_golden(g[i], g[j], k_phi, r, i)
                c[i], c[j] = _mix_golden(c[i], c[j], k_rec, r, j)
        else:
            for idx in range(4):
                i = idx
                j = (idx + 4) % 8
                g[i], g[j] = _mix_complementary(g[i], g[j], k_phi, r, i)
                c[i], c[j] = _mix_complementary(c[i], c[j], k_rec, r, j)

        # Edge protection every 8 rounds
        if r > 0 and r % 8 == 0:
            g = _edge_protection(g, r)
            c = _edge_protection(c, r)

        # Cross-stream diffusion every 4 rounds
        if r > 0 and r % 4 == 0:
            rot = _quasicrystal_rotation(r, 4)
            for i in range(8):
                temp = (g[i] ^ c[(i + 3) % 8]) & MASK32
                g[i] = (g[i] + _rotr(temp, rot)) & MASK32
                c[i] = (c[i] ^ _rotl(temp, rot)) & MASK32

    return g, c


class HarmoniaXOF:
    """
    HARMONIA-XOF: Sponge-based Extendable Output Function.

    Security level: 128 bits (capacity = 256 bits)
    Rate: 256 bits (32 bytes per absorption/squeeze)
    """

    def __init__(self):
        """Initialize XOF with zero state."""
        self._state_g = [0] * 8  # 256 bits
        self._state_c = [0] * 8  # 256 bits (capacity)
        self._buffer = bytearray()
        self._absorbing = True
        self._squeeze_buffer = bytearray()

    def _absorb_block(self, block: bytes):
        """Absorb a RATE-sized block into the state."""
        # XOR block into rate portion (state_g)
        words = struct.unpack('>8I', block)
        for i in range(8):
            self._state_g[i] ^= words[i]

        # Apply permutation
        self._state_g, self._state_c = _permutation(self._state_g, self._state_c)

    def absorb(self, data: bytes) -> 'HarmoniaXOF':
        """
        Absorb data into the sponge.

        Args:
            data: Bytes to absorb

        Returns:
            self for chaining
        """
        if not self._absorbing:
            raise RuntimeError("Cannot absorb after squeezing has started")

        self._buffer.extend(data)

        # Process complete blocks
        while len(self._buffer) >= RATE:
            self._absorb_block(bytes(self._buffer[:RATE]))
            del self._buffer[:RATE]

        return self

    def _finalize_absorb(self):
        """Finalize absorption phase with padding."""
        if not self._absorbing:
            return

        # Pad: append 0x1F, then zeros, then 0x80
        # (Sponge domain separation + padding)
        pad_len = RATE - len(self._buffer)
        if pad_len == 1:
            self._buffer.append(0x9F)  # 0x1F | 0x80
        else:
            self._buffer.append(0x1F)  # Domain separator for XOF
            self._buffer.extend(b'\x00' * (pad_len - 2))
            self._buffer.append(0x80)

        self._absorb_block(bytes(self._buffer))
        self._buffer.clear()
        self._absorbing = False

    def squeeze(self, length: int) -> bytes:
        """
        Squeeze output from the sponge.

        Args:
            length: Number of bytes to squeeze

        Returns:
            Output bytes
        """
        self._finalize_absorb()

        output = bytearray()

        # Use any remaining squeeze buffer
        if self._squeeze_buffer:
            take = min(len(self._squeeze_buffer), length)
            output.extend(self._squeeze_buffer[:take])
            del self._squeeze_buffer[:take]
            length -= take

        # Squeeze more blocks as needed
        while length > 0:
            # Extract rate portion
            block = struct.pack('>8I', *self._state_g)

            take = min(len(block), length)
            output.extend(block[:take])
            length -= take

            # Save excess for next squeeze
            if take < len(block):
                self._squeeze_buffer.extend(block[take:])

            # Apply permutation for next block
            if length > 0:
                self._state_g, self._state_c = _permutation(self._state_g, self._state_c)

        return bytes(output)

    def hexdigest(self, length: int) -> str:
        """Squeeze and return hex string."""
        return self.squeeze(length).hex()

    def copy(self) -> 'HarmoniaXOF':
        """Create a copy of current state."""
        new = HarmoniaXOF()
        new._state_g = self._state_g[:]
        new._state_c = self._state_c[:]
        new._buffer = self._buffer[:]
        new._absorbing = self._absorbing
        new._squeeze_buffer = self._squeeze_buffer[:]
        return new


# Convenience functions

def harmonia_xof(data: bytes, output_length: int = 32) -> bytes:
    """
    Compute HARMONIA-XOF hash with specified output length.

    Args:
        data: Input bytes
        output_length: Desired output length in bytes (default 32)

    Returns:
        Hash bytes of specified length
    """
    xof = HarmoniaXOF()
    xof.absorb(data)
    return xof.squeeze(output_length)


def harmonia_xof_hex(data: bytes, output_length: int = 32) -> str:
    """Compute HARMONIA-XOF and return hex string."""
    return harmonia_xof(data, output_length).hex()


# SHAKE-like aliases
def harmonia128(data: bytes, output_length: int = 32) -> bytes:
    """SHAKE128-like function with 128-bit security."""
    return harmonia_xof(data, output_length)


def harmonia256(data: bytes, output_length: int = 64) -> bytes:
    """SHAKE256-like function with default 512-bit output."""
    return harmonia_xof(data, output_length)


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print(f"HARMONIA-XOF v{VERSION} Self-Test")
    print("=" * 60)

    # Test vectors
    test_cases = [
        (b"", 32, "Empty string, 32 bytes"),
        (b"", 64, "Empty string, 64 bytes"),
        (b"HARMONIA", 32, "Short message, 32 bytes"),
        (b"HARMONIA", 128, "Short message, 128 bytes"),
        (b"The quick brown fox", 32, "Standard message"),
    ]

    print("\n### Test Vectors ###\n")
    for data, length, label in test_cases:
        h = harmonia_xof_hex(data, length)
        print(f"{label}:")
        print(f"  Input:  {data.decode() if data else '(empty)'}")
        print(f"  Length: {length} bytes")
        print(f"  Output: {h[:64]}{'...' if len(h) > 64 else ''}")
        print()

    # Test streaming
    print("### Streaming Test ###\n")
    xof1 = HarmoniaXOF()
    xof1.absorb(b"Hello, ")
    xof1.absorb(b"World!")
    result1 = xof1.hexdigest(32)

    xof2 = HarmoniaXOF()
    xof2.absorb(b"Hello, World!")
    result2 = xof2.hexdigest(32)

    print(f"Chunked absorb: {result1}")
    print(f"Single absorb:  {result2}")
    print(f"Match: {'PASS' if result1 == result2 else 'FAIL'}")

    # Test incremental squeeze
    print("\n### Incremental Squeeze Test ###\n")
    xof = HarmoniaXOF()
    xof.absorb(b"test")

    # Squeeze in parts
    part1 = xof.squeeze(16).hex()
    part2 = xof.squeeze(16).hex()

    # Squeeze all at once
    xof2 = HarmoniaXOF()
    xof2.absorb(b"test")
    full = xof2.squeeze(32).hex()

    print(f"Part 1 (16 bytes): {part1}")
    print(f"Part 2 (16 bytes): {part2}")
    print(f"Combined:          {part1 + part2}")
    print(f"Full (32 bytes):   {full}")
    print(f"Match: {'PASS' if part1 + part2 == full else 'FAIL'}")

    print("\n" + "=" * 60)
    print("HARMONIA-XOF: Sponge construction with 128-bit security")
    print("Rate: 256 bits | Capacity: 256 bits | Rounds: 24")
    print("=" * 60)
