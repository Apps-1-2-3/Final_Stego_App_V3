# StegoVault v3

Secure image and video steganography with a comparative analysis dashboard.

StegoVault combines AES-128-CBC encryption, HMAC-SHA256 authentication, PBKDF2
key derivation, adaptive LSB embedding, and key-seeded randomized placement. The
React dashboard can encode/decode images, compare traditional sequential LSB
against the proposed secure method, inspect PSNR/MSE/SSIM metrics, compare RGB
histograms, visualize changed pixels, and run lossless video steganography.

## Stack

- Frontend: React 18, TypeScript, Vite, Tailwind CSS, Recharts, lucide-react
- Backend: Python 3, Flask, Pillow, NumPy, scikit-image, PyCryptodome, OpenCV
- Video: FFmpeg is required on the system path

## Project Structure

```text
stego-app/
  backend/
    app.py                 Flask API
    encryption.py          AES/HMAC/PBKDF2 encryption layer
    embedding.py           Adaptive randomized image embedding
    extraction.py          Image payload extraction
    traditional.py         Sequential LSB baseline
    video/                 Modular video steganography engine
    requirements.txt
  src/
    App.tsx
    components/            Dashboard panels
    lib/api.ts
  package.json
  vite.config.ts
```

## Run Locally

### Backend

```bash
cd stego-app
python -m venv backend/.venv
backend/.venv/Scripts/activate
pip install -r backend/requirements.txt
python -m backend.app
```

On macOS/Linux, activate with `source backend/.venv/bin/activate`.

The API runs on `http://localhost:5000`.

### Frontend

```bash
cd stego-app
npm install or npm i
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api/*` to the Flask backend.

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Backend status and FFmpeg availability |
| POST | `/api/capacity` | Image payload capacity |
| POST | `/api/encode` | Encrypt and embed a message in an image |
| POST | `/api/decode` | Extract and decrypt a message from an image |
| POST | `/api/metrics` | PSNR, MSE, SSIM, and modification stats |
| POST | `/api/histogram` | RGB histogram comparison |
| POST | `/api/difference-map` | Pixel-level difference map |
| POST | `/api/security-analysis` | Security-layer report |
| POST | `/api/compare` | Traditional vs proposed side-by-side analysis |
| POST | `/api/video/encode` | Encode a message into a lossless AVI video |
| POST | `/api/video/decode` | Decode a message from a StegoVault video |

## Notes

- Use PNG or BMP for image steganography. JPEG recompression destroys LSB data.
- Encoded video is returned as lossless FFV1 AVI to preserve embedded frame bits.
- Wrong-key image extraction fails during HMAC verification before plaintext is
  exposed.
- Install FFmpeg and make sure `ffmpeg -version` works before using video mode.
"# Final_Stego_App_V3" 
