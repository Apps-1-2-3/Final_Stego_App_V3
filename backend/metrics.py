"""Image quality metrics: PSNR, MSE, SSIM."""
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim_fn


def _to_arr(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"), dtype=np.float64)


def mse(a: Image.Image, b: Image.Image) -> float:
    x = _to_arr(a); y = _to_arr(b)
    return float(np.mean((x - y) ** 2))


def psnr(a: Image.Image, b: Image.Image) -> float:
    m = mse(a, b)
    if m == 0:
        return float("inf")
    return float(20 * np.log10(255.0 / np.sqrt(m)))


def ssim(a: Image.Image, b: Image.Image) -> float:
    max_dim = 1024
    if max(a.size + b.size) > max_dim:
        a = a.copy()
        b = b.copy()
        a.thumbnail((max_dim, max_dim), Image.Resampling.BICUBIC)
        b.thumbnail((max_dim, max_dim), Image.Resampling.BICUBIC)
    x = np.array(a.convert("RGB"))
    y = np.array(b.convert("RGB"))
    return float(ssim_fn(x, y, channel_axis=2, data_range=255))


def compute_all(original: Image.Image, stego: Image.Image) -> dict:
    m = mse(original, stego)
    p = psnr(original, stego)
    s = ssim(original, stego)
    return {
        "mse": round(m, 6),
        "psnr": round(p, 4) if p != float("inf") else 999.0,
        "ssim": round(s, 6),
        "interpretation": {
            "psnr": "excellent" if p > 50 else "good" if p > 40 else "moderate" if p > 30 else "poor",
            "mse": "excellent" if m < 1 else "good" if m < 5 else "moderate" if m < 20 else "poor",
            "ssim": "excellent" if s > 0.99 else "good" if s > 0.95 else "moderate" if s > 0.85 else "poor",
        },
    }
