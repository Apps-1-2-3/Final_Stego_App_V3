"""Traditional sequential LSB steganography (plaintext, no encryption).

Used as a baseline to compare against the proposed AES + randomized
adaptive LSB pipeline.
"""
import numpy as np
from PIL import Image

HEADER_BITS = 32  # uint32 payload bit length


def capacity_bits(image: Image.Image) -> int:
    arr = np.array(image.convert("RGB"))
    return arr.size - HEADER_BITS


def embed_sequential(image: Image.Image, message: str) -> Image.Image:
    """Sequential LSB embedding of UTF-8 plaintext message."""
    payload = message.encode("utf-8")
    arr = np.array(image.convert("RGB")).copy()
    flat = arr.reshape(-1)  # over R,G,B sequentially

    payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    n = len(payload_bits)
    header = np.unpackbits(np.array([n], dtype=">u4").view(np.uint8))
    all_bits = np.concatenate([header, payload_bits])

    if len(all_bits) > flat.size:
        raise ValueError("payload too large for traditional sequential embedding")

    # vectorized LSB write across the first len(all_bits) channels
    flat[: len(all_bits)] = (flat[: len(all_bits)] & 0xFE) | all_bits

    return Image.fromarray(flat.reshape(arr.shape).astype(np.uint8), "RGB")


def extract_sequential(image: Image.Image) -> str:
    """Read 32-bit length header then n payload bits, sequential order."""
    arr = np.array(image.convert("RGB"))
    flat = arr.reshape(-1)

    header_bits = flat[:HEADER_BITS] & 1
    n = int(np.packbits(header_bits.astype(np.uint8)).view(">u4")[0])
    if n <= 0 or n > flat.size - HEADER_BITS:
        raise ValueError("invalid traditional header")
    bits = (flat[HEADER_BITS: HEADER_BITS + n] & 1).astype(np.uint8)
    if len(bits) % 8 != 0:
        bits = np.concatenate([bits, np.zeros(8 - len(bits) % 8, dtype=np.uint8)])
    raw = bytes(np.packbits(bits))
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return raw.hex()
