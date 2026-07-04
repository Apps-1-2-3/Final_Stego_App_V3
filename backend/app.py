"""Flask API server for StegoVault."""
import io
import os
import base64
import time
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image

from .encryption import encrypt, decrypt
from .embedding import embed, capacity_bits
from .extraction import extract
from .traditional import embed_sequential, extract_sequential
from .metrics import compute_all
from .histogram import (
    compare_histograms, difference_map, modification_stats,
    histogram_deviation, density_heatmap, rgb_histograms,
)
from .analysis import security_report

from .video_stego import (
    embed_message_in_video,
    extract_message_from_video
)
from .video.ffmpeg_utils import check_ffmpeg

app = Flask(__name__)
CORS(app)


def _read_image_field(field="image") -> Image.Image:
    f = request.files.get(field)
    if not f:
        raise ValueError(f"missing file field '{field}'")
    return Image.open(f.stream).convert("RGB")


def _img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _suffix_for_upload(file, default=".mp4") -> str:
    suffix = Path(file.filename or "").suffix.lower()
    return suffix if suffix else default


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "StegoVault",
        "version": "3.0",
        "video": {"ffmpeg_available": check_ffmpeg()},
    }


@app.post("/api/capacity")
def api_capacity():
    img = _read_image_field()
    return {"capacity_bits": capacity_bits(img), "capacity_bytes": capacity_bits(img) // 8}


@app.post("/api/encode")
def api_encode():
    img = _read_image_field()
    message = request.form.get("message", "")
    password = request.form.get("password", "")
    if not message or not password:
        return {"error": "message and password required"}, 400

    t0 = time.perf_counter()
    blob = encrypt(message, password)
    stego = embed(img, blob, password)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    metrics = compute_all(img, stego)
    mod_stats = modification_stats(img, stego)

    return jsonify({
        "stego_image_b64": _img_to_b64(stego),
        "stats": {
            "message_bytes": len(message.encode("utf-8")),
            "ciphertext_bytes": len(blob),
            "capacity_bits": capacity_bits(img),
            "encoding_ms": round(elapsed_ms, 2),
            **mod_stats,
        },
        "metrics": metrics,
        "security": security_report(password, img, len(blob)),
    })


@app.post("/api/decode")
def api_decode():
    img = _read_image_field()
    password = request.form.get("password", "")
    if not password:
        return {"error": "password required"}, 400
    try:
        t0 = time.perf_counter()
        blob = extract(img, password)
        message = decrypt(blob, password)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {"message": message, "decoding_ms": round(elapsed_ms, 2), "key_valid": True}
    except Exception as e:
        return {"error": str(e), "key_valid": False}, 401

@app.post("/api/video/encode")
def api_video_encode():
    file = request.files.get("video")
    if not file:
        return {"error": "video required"}, 400

    message = request.form.get("message", "")
    password = request.form.get("password", "")
    if not message or not password:
        return {"error": "message and password required"}, 400

    if not check_ffmpeg():
        return {"error": "FFmpeg is required for video steganography."}, 503

    temp_input = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=_suffix_for_upload(file)
    )
    temp_output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".avi"
    )
    temp_output.close()
    try:
        file.save(temp_input.name)
        embed_message_in_video(
            temp_input.name,
            message,
            password,
            output_path=temp_output.name,
        )
        response = send_file(
            temp_output.name,
            mimetype="video/x-msvideo",
            as_attachment=True,
            download_name="stego_video.avi",
        )

        @response.call_on_close
        def cleanup_files():
            for path in (temp_input.name, temp_output.name):
                try:
                    os.remove(path)
                except Exception:
                    pass

        return response
    except Exception as e:
        try:
            os.remove(temp_output.name)
        except Exception:
            pass
        return {"error": str(e)}, 400
    finally:
        if os.path.exists(temp_input.name):
            try:
                os.remove(temp_input.name)
            except Exception:
                pass


@app.post("/api/video/decode")
def api_video_decode():
    file = request.files.get("video")
    password = request.form.get("password", "")
    if not file or not password:
        return {"error": "video and password required"}, 400

    if not check_ffmpeg():
        return {"error": "FFmpeg is required for video steganography."}, 503

    temp_input = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=_suffix_for_upload(file, ".avi")
    )
    try:
        file.save(temp_input.name)
        message = extract_message_from_video(temp_input.name, password)
        return jsonify({"message": message})
    except Exception as e:
        return {"error": str(e)}, 400
    finally:
        try:
            os.remove(temp_input.name)
        except Exception:
            pass


@app.post("/api/metrics")
def api_metrics():
    orig = _read_image_field("original")
    stego = _read_image_field("stego")
    return jsonify({
        "metrics": compute_all(orig, stego),
        "modification": modification_stats(orig, stego),
    })


@app.post("/api/histogram")
def api_histogram():
    orig = _read_image_field("original")
    stego = _read_image_field("stego")
    return jsonify(compare_histograms(orig, stego))


@app.post("/api/difference-map")
def api_diff_map():
    orig = _read_image_field("original")
    stego = _read_image_field("stego")
    return jsonify({
        "diff_map_b64": difference_map(orig, stego),
        "modification": modification_stats(orig, stego),
    })


@app.post("/api/security-analysis")
def api_security():
    img = _read_image_field()
    password = request.form.get("password", "")
    payload_bytes = int(request.form.get("payload_bytes", 0))
    return jsonify(security_report(password, img, payload_bytes))


@app.post("/api/compare")
def api_compare():
    """Run BOTH traditional sequential LSB and proposed AES+adaptive
    randomized LSB on the same image/message/key, return side-by-side
    stego images, difference maps, histograms, metrics, security and
    extraction results so the frontend can render a comparative dashboard.
    """
    img = _read_image_field()
    message = request.form.get("message", "")
    password = request.form.get("password", "")
    wrong_key = request.form.get("wrong_key", "") or (password + "_wrong")
    if not message or not password:
        return {"error": "message and password required"}, 400

    # ---- Pipeline A: traditional sequential plaintext LSB ----
    t0 = time.perf_counter()
    trad_stego = embed_sequential(img, message)
    trad_ms = (time.perf_counter() - t0) * 1000
    trad_metrics = compute_all(img, trad_stego)
    trad_mod = modification_stats(img, trad_stego)
    trad_dev = histogram_deviation(img, trad_stego)
    trad_diff = difference_map(
            img,
            trad_stego,
            mode="traditional"
        )
    trad_heat = density_heatmap(img, trad_stego)
    trad_extracted = extract_sequential(trad_stego)

    # ---- Pipeline B: proposed AES + key-seeded adaptive randomized LSB ----
    t1 = time.perf_counter()
    blob = encrypt(message, password)
    prop_stego = embed(img, blob, password)
    prop_ms = (time.perf_counter() - t1) * 1000
    prop_metrics = compute_all(img, prop_stego)
    prop_mod = modification_stats(img, prop_stego)
    prop_dev = histogram_deviation(img, prop_stego)
    prop_diff = difference_map(
            img,
            prop_stego,
            mode="proposed"
        )
    prop_heat = density_heatmap(img, prop_stego)

    # extractions: right key recovers plaintext; wrong key MUST fail
    try:
        prop_blob = extract(prop_stego, password)
        prop_plain = decrypt(prop_blob, password)
        prop_cipher_preview = prop_blob[:32].hex()
        prop_decrypt_ok = True
    except Exception as e:
        prop_plain = f"<error: {e}>"
        prop_cipher_preview = ""
        prop_decrypt_ok = False

    try:
        wrong_blob = extract(prop_stego, wrong_key)
        decrypt(wrong_blob, wrong_key)
        prop_wrong_key_failed = False
        prop_wrong_key_error = "extraction unexpectedly succeeded"
    except Exception as e:
        prop_wrong_key_failed = True
        prop_wrong_key_error = str(e)


    return jsonify({
        "input": {
            "message_bytes": len(message.encode("utf-8")),
            "ciphertext_bytes": len(blob),
        },
        "histograms": {
            "bins": list(range(256)),
            "original": rgb_histograms(img),
            "traditional": rgb_histograms(trad_stego),
            "proposed": rgb_histograms(prop_stego),
        },
        "traditional": {
            "stego_image_b64": _img_to_b64(trad_stego),
            "diff_map_b64": trad_diff,
            "heatmap": trad_heat,
            "metrics": trad_metrics,
            "modification": trad_mod,
            "histogram_deviation": trad_dev,
            "encoding_ms": round(trad_ms, 2),
            "extracted_message": trad_extracted,
            "ciphertext_preview": "",
            "encrypted": False,
            "randomized": False,
            "wrong_key_protected": False,
        },
        "proposed": {
            "stego_image_b64": _img_to_b64(prop_stego),
            "diff_map_b64": prop_diff,
            "heatmap": prop_heat,
            "metrics": prop_metrics,
            "modification": prop_mod,
            "histogram_deviation": prop_dev,
            "encoding_ms": round(prop_ms, 2),
            "extracted_message": prop_plain if prop_decrypt_ok else "",
            "ciphertext_preview": prop_cipher_preview,
            "encrypted": True,
            "randomized": True,
            "wrong_key_protected": prop_wrong_key_failed,
            "wrong_key_error": prop_wrong_key_error,
            "security": security_report(password, img, len(blob)),
        },
        "comparison": {
            "psnr_delta": round(prop_metrics["psnr"] - trad_metrics["psnr"], 4),
            "ssim_delta": round(prop_metrics["ssim"] - trad_metrics["ssim"], 6),
            "mod_pct_delta": round(trad_mod["modified_percent"] - prop_mod["modified_percent"], 4),
            "histogram_deviation_delta": round(trad_dev - prop_dev, 6),
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
