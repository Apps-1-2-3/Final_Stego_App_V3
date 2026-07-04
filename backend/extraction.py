"""Extract payload using same adaptive ranking + key-seeded order."""
import numpy as np
from PIL import Image
from .embedding import _rank_positions, _key_seed, HEADER_BITS


def extract(image: Image.Image, password: str) -> bytes:
    arr = np.array(image.convert("RGB"))
    H, W, _ = arr.shape
    flat = arr.reshape(-1, 3)

    pixel_order = _rank_positions(arr)

    # Read header first: need ceil(32/3)=11 pixels — but those 11 pixels were
    # written in the PERMUTED order. We must reconstruct the same permutation
    # length, which depends on total bits. So we extract progressively.

    # Strategy: first compute the rng permutation for the MAX possible pixels
    # (we don't know n yet). Permute all pixels, then read bit-by-bit.
    rng = np.random.default_rng(_key_seed(password))
    perm = rng.permutation(len(pixel_order))
    ordered = pixel_order[perm]

    # Read header (32 bits)
    bits = []
    pi = 0
    while len(bits) < HEADER_BITS:
        p = ordered[pi]; pi += 1
        for c in range(3):
            bits.append(flat[p, c] & 1)
            if len(bits) >= HEADER_BITS:
                break

    header_bits = np.array(bits[:HEADER_BITS], dtype=np.uint8)
    n = int(np.packbits(header_bits).view(">u4")[0])
    if n <= 0 or n > (len(ordered) * 3 - HEADER_BITS):
        raise ValueError("invalid payload length in header (wrong key?)")

    # Continue reading n payload bits
    payload_bits = []
    # account for bits already consumed beyond header in last pixel
    consumed_in_last = HEADER_BITS % 3
    if consumed_in_last != 0:
        p = ordered[pi - 1]
        for c in range(consumed_in_last, 3):
            payload_bits.append(flat[p, c] & 1)
            if len(payload_bits) >= n:
                break

    while len(payload_bits) < n:
        p = ordered[pi]; pi += 1
        for c in range(3):
            payload_bits.append(flat[p, c] & 1)
            if len(payload_bits) >= n:
                break

    arr_bits = np.array(payload_bits[:n], dtype=np.uint8)
    # pad to byte boundary
    if len(arr_bits) % 8 != 0:
        arr_bits = np.concatenate([arr_bits, np.zeros(8 - len(arr_bits) % 8, dtype=np.uint8)])
    return bytes(np.packbits(arr_bits))
