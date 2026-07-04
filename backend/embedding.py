"""Adaptive LSB embedding with key-seeded randomized order."""
import hashlib
import numpy as np
from PIL import Image

HEADER_BITS = 32  # uint32 payload bit length
RANKED_PIXEL_LIMIT = 300_000


def _key_seed(password: str) -> int:
    h = hashlib.sha256(("stego-order::" + password).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def _rank_positions(arr: np.ndarray) -> np.ndarray:
    """Rank pixel positions by 3x3 local variance of LSB-masked grayscale.
    Returns flat indices into (H*W) ordered from highest variance to lowest.
    Computed on the LSB-masked image so ranking is stable before/after embedding.
    """
    masked = (arr & 0xFE).astype(np.float32)
    gray = masked.mean(axis=2)  # H x W
    H, W = gray.shape
    # 3x3 local variance via integral approach
    pad = np.pad(gray, 1, mode="edge")
    s = np.zeros_like(gray); s2 = np.zeros_like(gray)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            patch = pad[1+dy:1+dy+H, 1+dx:1+dx+W]
            s += patch
            s2 += patch * patch
    mean = s / 9.0
    var = s2 / 9.0 - mean * mean
    flat = var.flatten()
    if flat.size <= RANKED_PIXEL_LIMIT:
        return np.argsort(-flat, kind="stable")

    candidate_idx = np.argpartition(flat, -RANKED_PIXEL_LIMIT)[-RANKED_PIXEL_LIMIT:]
    ranked = candidate_idx[np.argsort(-flat[candidate_idx], kind="stable")]
    return ranked


def capacity_bits(image: Image.Image) -> int:
    arr = np.array(image.convert("RGB"))
    H, W, _ = arr.shape
    ranked_pixels = min(H * W, RANKED_PIXEL_LIMIT)
    return ranked_pixels * 3 - HEADER_BITS


def embed(image: Image.Image, payload: bytes, password: str) -> Image.Image:
    arr = np.array(image.convert("RGB")).copy()
    H, W, _ = arr.shape
    payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    n = len(payload_bits)
    header = np.unpackbits(np.array([n], dtype=">u4").view(np.uint8))
    all_bits = np.concatenate([header, payload_bits])

    cap = capacity_bits(image)
    if len(payload_bits) > cap:
        raise ValueError(f"payload too large: {len(payload_bits)} bits > capacity {cap}")

    pixel_order = _rank_positions(arr)  # length H*W
    # Permute the FULL ranked order with key-seeded PRNG so extractor (which
    # doesn't know payload length up front) can reproduce the same sequence.
    rng = np.random.default_rng(_key_seed(password))
    perm = rng.permutation(len(pixel_order))
    chosen = pixel_order[perm]
    needed_pixels = (len(all_bits) + 2) // 3
    chosen = chosen[:needed_pixels]

    # write bits across R,G,B of each chosen pixel
    flat = arr.reshape(-1, 3)
    bit_idx = 0
    for p in chosen:
        for c in range(3):
            if bit_idx >= len(all_bits):
                break
            flat[p, c] = (flat[p, c] & 0xFE) | int(all_bits[bit_idx])
            bit_idx += 1
        if bit_idx >= len(all_bits):
            break

    out = flat.reshape(H, W, 3).astype(np.uint8)
    return Image.fromarray(out, "RGB")
