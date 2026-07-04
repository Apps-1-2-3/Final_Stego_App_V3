import { useEffect, useRef, useState } from "react";
import { Dropzone } from "./Dropzone";
import { PasswordInput } from "./PasswordInput";
import { MetricsPanel } from "./MetricsPanel";
import { HistogramPanel } from "./HistogramPanel";
import { SecurityPanel } from "./SecurityPanel";
import { EmbeddingVisualizer } from "./EmbeddingVisualizer";
import { postForm, b64ToBlob } from "../lib/api";
import { Loader2, Lock, Download } from "lucide-react";

export function EncodePanel() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);
  const [stegoUrl, setStegoUrl] = useState<string>("");
  const [originalUrl, setOriginalUrl] = useState<string>("");
  const [diffUrl, setDiffUrl] = useState<string>("");
  const [histData, setHistData] = useState<any>(null);
  const tick = useRef<number | null>(null);

  useEffect(() => {
    if (file) { const u = URL.createObjectURL(file); setOriginalUrl(u); return () => URL.revokeObjectURL(u); }
  }, [file]);

  function startProgress() {
    setProgress(8);
    tick.current = window.setInterval(() => setProgress((p) => Math.min(p + 6, 88)), 150);
  }
  function endProgress() {
    if (tick.current) window.clearInterval(tick.current);
    setProgress(100);
    setTimeout(() => setProgress(0), 500);
  }

  async function onEncode() {
    if (!file || !message || !password) { setError("Image, message, and key are required."); return; }
    setError(""); setBusy(true); setResult(null); setHistData(null); setDiffUrl(""); setStegoUrl("");
    startProgress();
    try {
      const fd = new FormData();
      fd.append("image", file); fd.append("message", message); fd.append("password", password);
      const r = await postForm("/api/encode", fd);
      setResult(r);

      const stegoBlob = b64ToBlob(r.stego_image_b64);
      const stegoFile = new File([stegoBlob], "stego.png", { type: "image/png" });
      setStegoUrl(URL.createObjectURL(stegoBlob));

      // follow-up calls in parallel
      const fd2 = new FormData(); fd2.append("original", file); fd2.append("stego", stegoFile);
      const fd3 = new FormData(); fd3.append("original", file); fd3.append("stego", stegoFile);
      const [hist, diff] = await Promise.all([
        postForm("/api/histogram", fd2),
        postForm("/api/difference-map", fd3),
      ]);
      setHistData(hist);
      setDiffUrl(URL.createObjectURL(b64ToBlob(diff.diff_map_b64)));
    } catch (e: any) {
      setError(e.message || "encode failed");
    } finally { setBusy(false); endProgress(); }
  }

  function download() {
    const a = document.createElement("a");
    a.href = stegoUrl; a.download = "stego.png"; a.click();
  }

  return (
    <div className="space-y-5">
      <section className="panel p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Lock size={18} className="text-accent" /> Encode Message</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div>
            <div className="label">Cover image</div>
            <Dropzone file={file} onFile={setFile} />
          </div>
          <div className="space-y-3">
            <div>
              <div className="label">Secret message</div>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)}
                rows={4} placeholder="Type the message you want to hide..." className="input resize-none" />
              <div className="text-[11px] text-slate-500 mt-1 mono">{new Blob([message]).size} bytes</div>
            </div>
            <div>
              <div className="label">Encryption key</div>
              <PasswordInput value={password} onChange={setPassword} />
            </div>
            <button onClick={onEncode} disabled={busy} className="btn-primary w-full justify-center">
              {busy ? <Loader2 className="animate-spin" size={16} /> : <Lock size={16} />}
              {busy ? "Encrypting & embedding..." : "Encrypt & Embed"}
            </button>
            {progress > 0 && (
              <div className="h-1.5 w-full bg-border rounded overflow-hidden">
                <div className="h-full bg-accent transition-all" style={{ width: `${progress}%` }} />
              </div>
            )}
            {error && <div className="chip-bad">{error}</div>}
          </div>
        </div>
      </section>

      {result && (
        <>
          <section className="panel p-5 fade-in flex items-center justify-between flex-wrap gap-3">
            <div>
              <div className="text-sm text-slate-300">Stego image ready</div>
              <div className="text-xs text-slate-500 mono mt-1">
                Encoded in {result.stats.encoding_ms.toFixed(1)} ms · ciphertext {result.stats.ciphertext_bytes} B ·
                capacity {(result.stats.capacity_bits / 8 / 1024).toFixed(1)} KiB
              </div>
            </div>
            <button onClick={download} className="btn-primary"><Download size={16} /> Download stego.png</button>
          </section>

          <MetricsPanel metrics={result.metrics} modification={result.stats} />
          {histData && <HistogramPanel data={histData} />}
          <SecurityPanel sec={result.security} keyValid={null} />
          {diffUrl && originalUrl && stegoUrl &&
            <EmbeddingVisualizer originalUrl={originalUrl} stegoUrl={stegoUrl} diffUrl={diffUrl} />}
        </>
      )}
    </div>
  );
}
