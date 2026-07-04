import { useState } from "react";
import { Dropzone } from "./Dropzone";
import { PasswordInput } from "./PasswordInput";
import { postForm } from "../lib/api";
import { Unlock, Loader2, ShieldAlert, ShieldCheck } from "lucide-react";

export function DecodePanel() {
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [out, setOut] = useState<{ message: string; decoding_ms: number } | null>(null);
  const [keyValid, setKeyValid] = useState<boolean | null>(null);

  async function onDecode() {
    if (!file || !password) { setError("Stego image and key required."); return; }
    setError(""); setBusy(true); setOut(null); setKeyValid(null);
    try {
      const fd = new FormData();
      fd.append("image", file); fd.append("password", password);
      const r = await postForm("/api/decode", fd);
      setOut({ message: r.message, decoding_ms: r.decoding_ms });
      setKeyValid(true);
    } catch (e: any) {
      setKeyValid(false);
      setError("Authentication failed. Wrong key or tampered image. No plaintext was revealed.");
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-5">
      <section className="panel p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Unlock size={18} className="text-accent" /> Decode Message</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div>
            <div className="label">Stego image</div>
            <Dropzone file={file} onFile={setFile} />
          </div>
          <div className="space-y-3">
            <div>
              <div className="label">Decryption key</div>
              <PasswordInput value={password} onChange={setPassword} />
            </div>
            <button onClick={onDecode} disabled={busy} className="btn-primary w-full justify-center">
              {busy ? <Loader2 className="animate-spin" size={16} /> : <Unlock size={16} />}
              {busy ? "Extracting & verifying..." : "Extract & Decrypt"}
            </button>
            {keyValid === false && (
              <div className="bg-bad/10 border border-bad/30 text-bad rounded-lg p-3 text-sm flex gap-2 fade-in">
                <ShieldAlert size={18} className="shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium">HMAC verification failed</div>
                  <div className="text-xs mt-1 opacity-80">{error}</div>
                </div>
              </div>
            )}
            {out && (
              <div className="bg-good/10 border border-good/30 rounded-lg p-3 fade-in">
                <div className="flex items-center gap-2 text-good text-sm font-medium">
                  <ShieldCheck size={18} /> Key validated · decoded in {out.decoding_ms.toFixed(1)} ms
                </div>
                <pre className="mono text-sm text-slate-100 mt-3 whitespace-pre-wrap break-words bg-bg/40 border border-border rounded-md p-3">
{out.message}
                </pre>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
