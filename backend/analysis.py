"""Security analysis: key validation, layer description, brute-force estimation."""
import math
from .embedding import capacity_bits


def security_report(password: str, image, payload_bytes: int) -> dict:
    # Entropy of password (rough): log2(charset^len). Estimate charset.
    charset = 0
    if any(c.islower() for c in password): charset += 26
    if any(c.isupper() for c in password): charset += 26
    if any(c.isdigit() for c in password): charset += 10
    if any(not c.isalnum() for c in password): charset += 32
    charset = max(charset, 1)
    entropy_bits = len(password) * math.log2(charset) if charset > 1 else 0

    cap = capacity_bits(image)
    used = payload_bytes * 8
    return {
        "layers": [
            {"name": "PBKDF2-SHA256", "detail": "200,000 iterations, 16-byte salt"},
            {"name": "AES-128-CBC", "detail": "random 16-byte IV per message"},
            {"name": "HMAC-SHA256", "detail": "integrity + wrong-key detection"},
            {"name": "Adaptive LSB", "detail": "high-variance pixels selected"},
            {"name": "Key-seeded PRNG", "detail": "randomized embedding order"},
        ],
        "password_entropy_bits": round(entropy_bits, 2),
        "password_strength": (
            "very strong" if entropy_bits >= 80 else
            "strong" if entropy_bits >= 60 else
            "moderate" if entropy_bits >= 40 else
            "weak"
        ),
        "capacity_bits": cap,
        "used_bits": used,
        "utilization_percent": round(100.0 * used / cap, 4) if cap else 0,
        "brute_force_pbkdf2_cost_note": (
            "Each guess requires 200,000 SHA-256 iterations + HMAC verification. "
            "An attacker at 10^6 guesses/sec needs ~2^(entropy-20) seconds."
        ),
    }
