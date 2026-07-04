"""RGB histogram + difference map generation."""
import io
import base64
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

def rgb_histograms(img: Image.Image) -> dict:
    arr = np.array(img.convert("RGB"))
    out = {}
    for i, ch in enumerate(("r", "g", "b")):
        hist, _ = np.histogram(arr[..., i], bins=256, range=(0, 256))
        out[ch] = hist.astype(int).tolist()
    return out


def compare_histograms(original: Image.Image, stego: Image.Image) -> dict:
    return {
        "original": rgb_histograms(original),
        "stego": rgb_histograms(stego),
        "bins": list(range(256)),
    }

def difference_map(original: Image.Image, stego: Image.Image, mode="proposed") -> str:
    max_dim = 1400
    if max(original.size + stego.size) > max_dim:
        original = original.copy()
        stego = stego.copy()
        original.thumbnail((max_dim, max_dim), Image.Resampling.BICUBIC)
        stego.thumbnail((max_dim, max_dim), Image.Resampling.BICUBIC)

    a = np.array(original.convert("RGB"), dtype=np.int16)
    b = np.array(stego.convert("RGB"), dtype=np.int16)

    diff = np.any(a != b, axis=2)

    if mode == "traditional":
        diff = binary_dilation(diff, iterations=8)

    else:
        diff = binary_dilation(diff, iterations=2)

    out = np.zeros_like(a, dtype=np.uint8)

    gray = (
        0.3 * a[..., 0]
        + 0.59 * a[..., 1]
        + 0.11 * a[..., 2]
    ).astype(np.uint8) // 3

    out[..., 0] = gray
    out[..., 1] = gray
    out[..., 2] = gray

    if mode == "traditional":
        out[diff] = [255, 80, 80]

    else:
        out[diff] = [255, 0, 0]

    img = Image.fromarray(out, "RGB")

    buf = io.BytesIO()

    img.save(buf, format="PNG")

    return base64.b64encode(
        buf.getvalue()
    ).decode("ascii")

def modification_stats(original: Image.Image, stego: Image.Image) -> dict:
    a = np.array(original.convert("RGB"), dtype=np.int16)
    b = np.array(stego.convert("RGB"), dtype=np.int16)
    pixel_diff = np.any(a != b, axis=2)
    total = pixel_diff.size
    modified = int(pixel_diff.sum())
    channel_changes = int(np.sum(a != b))
    return {
        "total_pixels": int(total),
        "modified_pixels": modified,
        "modified_percent": round(100.0 * modified / total, 4),
        "channel_bit_flips": channel_changes,
    }


def histogram_deviation(original: Image.Image, stego: Image.Image) -> float:
    """Sum of absolute per-bin RGB histogram deltas, normalized by pixel count.

    Lower = stego histogram closer to original (more imperceptible at the
    statistical level — harder for histogram-based steganalysis).
    """
    a = np.array(original.convert("RGB"))
    b = np.array(stego.convert("RGB"))
    total = 0
    for i in range(3):
        ha, _ = np.histogram(a[..., i], bins=256, range=(0, 256))
        hb, _ = np.histogram(b[..., i], bins=256, range=(0, 256))
        total += int(np.abs(ha.astype(np.int64) - hb.astype(np.int64)).sum())
    # normalize: 2 changes per modified channel-bin; divide by total channels
    norm = a.size  # H*W*3
    return round(total / norm, 6)


def density_heatmap(original: Image.Image, stego: Image.Image, blocks: int = 32) -> dict:
    """Coarse-grained modification density grid for heatmap rendering."""
    a = np.array(original.convert("RGB"), dtype=np.int16)
    b = np.array(stego.convert("RGB"), dtype=np.int16)
    diff = np.any(a != b, axis=2).astype(np.float32)
    H, W = diff.shape
    bh = max(1, H // blocks)
    bw = max(1, W // blocks)
    rows = H // bh
    cols = W // bw
    trimmed = diff[: rows * bh, : cols * bw]
    grid = trimmed.reshape(rows, bh, cols, bw).mean(axis=(1, 3))
    return {"rows": rows, "cols": cols, "grid": grid.round(4).tolist()}
