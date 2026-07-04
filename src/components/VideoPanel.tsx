import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";
import { Download, Film, Loader2, Lock, Unlock } from "lucide-react";

export function VideoPanel() {

  const [video, setVideo] = useState<File | null>(null);

  const [message, setMessage] = useState("");

  const [password, setPassword] = useState("");

  const [downloadUrl, setDownloadUrl] = useState("");

  const [decodedMessage, setDecodedMessage] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    return () => {
      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    };
  }, [downloadUrl]);

  async function encode() {

    if (!video) {
      setError("Please select a video.");
      return;
    }

    if (!message) {
      setError("Please enter a secret message.");
      return;
    }

    if (!password) {
      setError("Please enter a password.");
      return;
    }

    setLoading(true);
    setError("");

    try {

      const form = new FormData();

      form.append("video", video);

      form.append("message", message);

      form.append("password", password);

      const res = await fetch(
        `${API_BASE}/api/video/encode`,
        {
          method: "POST",
          body: form,
        }
      );

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Video encoding failed.");
        return;
      }

      const blob = await res.blob();

      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);

      setDecodedMessage("");

    }
      catch (err: any) {

        console.error(err);

        setError("Encoding failed: " + String(err?.message || err));

      }

     finally {

      setLoading(false);
    }
  }

  async function decode() {

    if (!video) {
      setError("Please select encoded video.");
      return;
    }

    if (!password) {
      setError("Please enter password.");
      return;
    }

    setLoading(true);
    setError("");

    try {

      const form = new FormData();

      form.append("video", video);

      form.append("password", password);

      const res = await fetch(
        `${API_BASE}/api/video/decode`,
        {
          method: "POST",
          body: form,
        }
      );


      const data = await res.json();

      console.log(data);

      if (!res.ok) {
        setError(data.error || "Backend error while decoding.");
        return;
      }

      setDecodedMessage(data.message);

    } catch (err) {

      console.error(err);

      setError("Decoding failed.");

    } finally {

      setLoading(false);
    }
  }

  return (

    <div className="space-y-8">

      {/* Header */}
      <div>

        <h1 className="text-3xl font-semibold tracking-tight">
          <Film className="inline-block mr-2 text-accent" size={28} />
          Video Steganography
        </h1>

        <p className="text-slate-400 mt-2">
          Embed encrypted secret messages inside video frames using
          AES encryption and adaptive frame-based steganography.
        </p>

      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-2 gap-6">

        {/* Upload Section */}
        <div className="border border-border rounded-2xl p-6 bg-panel">

          <div className="mono text-xs uppercase text-slate-500 mb-3">
            Video File
          </div>

          <div className="border border-dashed border-slate-700 rounded-xl p-10 text-center">

            <div className="text-xl mb-3">
              Upload Video
            </div>

            <div className="text-sm text-slate-500 mb-5">
              MP4, AVI, MOV, MKV, WMV supported
            </div>

            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.wmv,.webm"
              onChange={(e) =>
                setVideo(
                  e.target.files?.[0] || null
                )
              }
            />

            {video && (

              <div className="mt-5 text-cyan-400 text-sm">
                Selected: {video.name}
              </div>

            )}

          </div>

        </div>

        {/* Controls */}
        <div className="border border-border rounded-2xl p-6 bg-panel space-y-5">

          {/* Message */}
          <div>

            <div className="mono text-xs uppercase text-slate-500 mb-2">
              Secret Message
            </div>

            <textarea
              className="w-full p-4 bg-black border border-slate-700 rounded-xl min-h-[140px]"
              placeholder="Enter secret message..."
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
            />

          </div>

          {/* Password */}
          <div>

            <div className="mono text-xs uppercase text-slate-500 mb-2">
              Encryption Password
            </div>

            <input
              type="password"
              className="w-full p-4 bg-black border border-slate-700 rounded-xl"
              placeholder="Enter password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
            />

          </div>

          {/* Buttons */}
          <div className="flex gap-4">

            <button
              onClick={encode}
              disabled={loading}
              className="flex-1 py-4 bg-accent text-bg rounded-xl font-semibold hover:opacity-90 transition inline-flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={16} /> : <Lock size={16} />}
              {loading ? "Processing..." : "Encode Video"}
            </button>

            <button
              onClick={decode}
              disabled={loading}
              className="flex-1 py-4 border border-accent text-accent rounded-xl font-semibold hover:bg-accent/10 transition inline-flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Unlock size={16} />
              Decode Video
            </button>

          </div>

        </div>

      </div>

      {error && (

        <div className="chip-bad">
          {error}
        </div>

      )}

      {/* Download */}
      {downloadUrl && (

        <div className="border border-cyan-500/20 rounded-2xl p-6 bg-panel">

          <div className="text-cyan-400 font-semibold text-lg mb-4">
            Video Successfully Encoded
          </div>

          <a
            href={downloadUrl}
            download="stego_video.avi"
            className="inline-flex items-center gap-2 px-5 py-3 bg-accent text-bg rounded-xl font-semibold"
          >
            <Download size={16} />
            Download Encoded Video
          </a>

        </div>

      )}

      {/* Decoded Output */}
      {decodedMessage && (

        <div className="border border-cyan-500/20 rounded-2xl p-6 bg-panel">

          <div className="text-cyan-400 font-semibold text-lg mb-3">
            Decoded Secret Message
          </div>

          <div className="bg-black border border-slate-700 rounded-xl p-4 text-slate-200">
            {decodedMessage}
          </div>

        </div>

      )}

    </div>
  );
}
