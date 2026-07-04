import { useMemo, useState } from "react";
import { Dropzone } from "./Dropzone";
import { PasswordInput } from "./PasswordInput";
import { postForm, b64ToBlob } from "../lib/api";
import { Loader2, GitCompare, ShieldAlert, ShieldCheck, Trophy, Check, X, Download } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";

type Side = {
  stego_image_b64: string; diff_map_b64: string;
  heatmap: { rows: number; cols: number; grid: number[][] };
  metrics: { psnr: number; mse: number; ssim: number };
  modification: { modified_percent: number; modified_pixels: number; total_pixels: number; channel_bit_flips: number };
  histogram_deviation: number; encoding_ms: number;
  extracted_message: string; ciphertext_preview: string;
  encrypted: boolean; randomized: boolean;
  wrong_key_protected: boolean; wrong_key_error?: string;
  resistance_score: number;
};
type Cmp = {
  input: { message_bytes: number; ciphertext_bytes: number };
  histograms: { bins: number[]; original: any; traditional: any; proposed: any };
  traditional: Side; proposed: Side;
  comparison: { psnr_delta: number; ssim_delta: number; mod_pct_delta: number; histogram_deviation_delta: number; winner: string };
};

export function ComparePanel() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<Cmp | null>(null);
  const [trUrl, setTrUrl] = useState(""); const [trDiff, setTrDiff] = useState("");
  const [prUrl, setPrUrl] = useState(""); const [prDiff, setPrDiff] = useState("");

  async function run() {
    if (!file || !message || !password) { setError("Image, message, and key are required."); return; }
    setError(""); setBusy(true); setData(null);
    try {
      const fd = new FormData();
      fd.append("image", file); fd.append("message", message); fd.append("password", password);
      const r: Cmp = await postForm("/api/compare", fd);
      setData(r);
      setTrUrl(URL.createObjectURL(b64ToBlob(r.traditional.stego_image_b64)));
      setTrDiff(URL.createObjectURL(b64ToBlob(r.traditional.diff_map_b64)));
      setPrUrl(URL.createObjectURL(b64ToBlob(r.proposed.stego_image_b64)));
      setPrDiff(URL.createObjectURL(b64ToBlob(r.proposed.diff_map_b64)));
    } catch (e: any) { setError(e.message || "compare failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-5">
      <section className="panel p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <GitCompare size={18} className="text-accent" /> Dual-Mode Comparative Analysis
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Runs <span className="text-rose-400 mono">Traditional sequential LSB</span> and the
          {" "}<span className="text-accent mono">Proposed AES + randomized adaptive LSB</span> against
          the same image, message and key — then compares them side by side.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div>
            <div className="label">Cover image</div>
            <Dropzone file={file} onFile={setFile} />
          </div>
          <div className="space-y-3">
            <div>
              <div className="label">Secret message</div>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)}
                rows={4} placeholder="Message to hide in both systems..." className="input resize-none" />
            </div>
            <div>
              <div className="label">Encryption key</div>
              <PasswordInput value={password} onChange={setPassword} />
            </div>
            <button onClick={run} disabled={busy} className="btn-primary w-full justify-center">
              {busy ? <Loader2 className="animate-spin" size={16} /> : <GitCompare size={16} />}
              {busy ? "Running both pipelines..." : "Run Comparative Analysis"}
            </button>
            {error && <div className="text-rose-400 text-sm mono">{error}</div>}
          </div>
        </div>
      </section>

      {data && (
        <>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <SideCard
              title="Traditional LSB" subtitle="Sequential · Plaintext · No key"
              tone="rose" side={data.traditional} stegoUrl={trUrl} diffUrl={trDiff}
            />
            <SideCard
              title="Proposed Secure" subtitle="AES-128 · Randomized · Adaptive sparse"
              tone="accent" side={data.proposed} stegoUrl={prUrl} diffUrl={prDiff}
            />
          </div>

          <MetricsCompare trad={data.traditional} prop={data.proposed} />
          <HistogramCompare h={data.histograms} />
          <HeatmapsCompare trad={data.traditional} prop={data.proposed} />
        </>
      )}
    </div>
  );
}


function SideCard({ title, subtitle, tone, side, stegoUrl, diffUrl }:
  { title: string; subtitle: string; tone: "rose" | "accent"; side: Side; stegoUrl: string; diffUrl: string }) {
  const [view, setView] = useState<"stego" | "diff">("stego");
  const border = tone === "accent" ? "border-accent/40" : "border-rose-500/40";
  const text = tone === "accent" ? "text-accent" : "text-rose-400";
  return (
    <section className={`panel p-5 border ${border} fade-in`}>
      <header className="flex items-start justify-between mb-3">
        <div>
          <h3 className={`text-base font-semibold ${text}`}>{title}</h3>
          <div className="text-[11px] text-slate-400 mono">{subtitle}</div>
        </div>
        <div className="flex gap-1">
          <ViewBtn active={view === "stego"} onClick={() => setView("stego")}>Stego</ViewBtn>
          <ViewBtn active={view === "diff"} onClick={() => setView("diff")}>Diff Map</ViewBtn>
        </div>
      </header>
      <div className="rounded-lg overflow-hidden bg-bg border border-border aspect-square flex items-center justify-center">
        <img src={view === "stego" ? stegoUrl : diffUrl} alt={view} className="max-w-full max-h-full object-contain" />
      </div>
      <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
        <Stat label="PSNR" v={`${side.metrics.psnr} dB`} />
        <Stat label="SSIM" v={side.metrics.ssim.toFixed(5)} />
        <Stat label="Mod %" v={`${side.modification.modified_percent}%`} />
      </div>
      <a download={`${title.toLowerCase().replace(/\s+/g, "-")}.png`} href={stegoUrl}
        className="mt-3 inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-accent">
        <Download size={12} /> Download stego image
      </a>
    </section>
  );
}
function ViewBtn({ active, onClick, children }: any) {
  return (
    <button onClick={onClick} className={`px-2.5 py-1 rounded text-[11px] mono uppercase border transition
      ${active ? "border-accent text-accent bg-accent/10" : "border-border text-slate-400 hover:border-accent/40"}`}>
      {children}
    </button>
  );
}
function Stat({ label, v }: { label: string; v: string }) {
  return (
    <div className="bg-bg border border-border rounded p-2">
      <div className="text-[10px] text-slate-500 uppercase mono">{label}</div>
      <div className="text-sm mono">{v}</div>
    </div>
  );
}

function MetricsCompare({ trad, prop }: { trad: Side; prop: Side }) {
  const rows = [
    ["PSNR (dB)", trad.metrics.psnr, prop.metrics.psnr, "higher"],
    ["MSE", trad.metrics.mse, prop.metrics.mse, "lower"],
    ["SSIM", trad.metrics.ssim, prop.metrics.ssim, "higher"],
    ["Modified Pixels %", trad.modification.modified_percent, prop.modification.modified_percent, "lower"],
    ["Histogram Deviation", trad.histogram_deviation, prop.histogram_deviation, "lower"],
    ["Channel Bit Flips", trad.modification.channel_bit_flips, prop.modification.channel_bit_flips, "lower"],
    ["Encoding (ms)", trad.encoding_ms, prop.encoding_ms, "info"],
  ] as const;
  return (
    <section className="panel p-5 fade-in">
      <h3 className="text-base font-semibold mb-3">Imperceptibility Metrics</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 uppercase mono border-b border-border">
              <th className="py-3">Metric</th>
              <th>Traditional</th>
              <th>Proposed</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([m, a, b, dir]) => {
              const aN = Number(a), bN = Number(b);
              return (
                <tr key={m} className="border-b border-border/40">
                  <td className="py-2 text-slate-300">{m}</td>
                  <td className="mono text-slate-300">{a}</td>
                  <td className="mono text-slate-300">{b}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function HistogramCompare({ h }: { h: Cmp["histograms"] }) {
  const [ch, setCh] = useState<"r" | "g" | "b">("r");
  const rows = useMemo(() => h.bins.map((b, i) => ({
    bin: b, original: h.original[ch][i], traditional: h.traditional[ch][i], proposed: h.proposed[ch][i],
  })), [h, ch]);
  return (
    <section className="panel p-5 fade-in">
      <header className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex gap-1">
          {(["r", "g", "b"] as const).map((c) => (
            <button key={c} onClick={() => setCh(c)}
              className={`px-3 py-1.5 rounded-md text-xs mono uppercase border transition
                ${ch === c ? "border-accent text-accent bg-accent/10" : "border-border text-slate-400 hover:border-accent/40"}`}>{c}</button>
          ))}
        </div>
      </header>
      <div className="h-72 w-full">
        <ResponsiveContainer>
          <LineChart data={rows} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2336" />
            <XAxis dataKey="bin" tick={{ fill: "#64748b", fontSize: 10 }} interval={31} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#0d1320", border: "1px solid #1a2336", borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="original" stroke="#94a3b8" strokeWidth={2} dot={false} name="Original" />
            <Line type="monotone" dataKey="traditional" stroke="#f87171" strokeWidth={1.5} strokeDasharray="4 3" dot={false} name="Traditional" />
            <Line type="monotone" dataKey="proposed" stroke="#22d3ee" strokeWidth={1.5} strokeDasharray="2 2" dot={false} name="Proposed" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function HeatmapsCompare({ trad, prop }: { trad: Side; prop: Side }) {
  return (
    <section className="panel p-5 fade-in">
      <h3 className="text-base font-semibold mb-3">Embedding Density Heatmaps</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Heatmap title="Traditional" tone="rose" data={trad.heatmap} />
        <Heatmap title="Proposed" tone="accent" data={prop.heatmap} />
      </div>
    </section>
  );
}
function Heatmap({ title, tone, data }: { title: string; tone: "rose" | "accent"; data: Side["heatmap"] }) {
  const max = Math.max(0.001, ...data.grid.flat());
  const color = tone === "accent" ? "34,211,238" : "248,113,113";
  return (
    <div>
      <div className={`text-xs mono uppercase mb-2 ${tone === "accent" ? "text-accent" : "text-rose-400"}`}>{title}</div>
      <div className="bg-bg border border-border rounded-lg p-2 aspect-square">
        <div className="grid w-full h-full" style={{ gridTemplateColumns: `repeat(${data.cols}, 1fr)` }}>
          {data.grid.flatMap((row, ri) => row.map((v, ci) => (
            <div key={`${ri}-${ci}`} style={{ background: `rgba(${color}, ${(v / max).toFixed(3)})` }} />
          )))}
        </div>
      </div>
    </div>
  );
}


function Cell({ v, bad }: { v: boolean | string; bad?: boolean }) {
  if (typeof v === "boolean") {
    return v
      ? <span className="inline-flex items-center gap-1 text-accent mono text-xs"><Check size={12} /> Yes</span>
      : <span className="inline-flex items-center gap-1 text-rose-400 mono text-xs"><X size={12} /> No</span>;
  }
  return <span className={`mono text-xs ${bad ? "text-rose-400" : "text-accent"}`}>{v}</span>;
}
