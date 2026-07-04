import { Activity, ImageIcon, Layers } from "lucide-react";

type Interp = "excellent" | "good" | "moderate" | "poor";
const tone = (t: Interp) => t === "excellent" || t === "good"
  ? "chip-good" : t === "moderate" ? "chip-warn" : "chip-bad";

export function MetricsPanel({ metrics, modification }: {
  metrics: { mse: number; psnr: number; ssim: number; interpretation: Record<string, Interp> };
  modification: { modified_pixels: number; total_pixels: number; modified_percent: number; channel_bit_flips: number };
}) {
  const cards = [
    { key: "psnr", label: "PSNR", value: `${metrics.psnr.toFixed(2)} dB`,
      hint: "Peak Signal-to-Noise Ratio. >40 dB = imperceptible distortion." , icon: <Activity size={18} /> },
    { key: "mse", label: "MSE", value: metrics.mse.toFixed(4),
      hint: "Mean Squared Error. Lower = fewer pixel changes.", icon: <ImageIcon size={18} /> },
    { key: "ssim", label: "SSIM", value: metrics.ssim.toFixed(6),
      hint: "Structural Similarity. 1.0 = identical structure.", icon: <Layers size={18} /> },
  ];
  return (
    <section className="panel p-5 fade-in">
      <header className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">Imperceptibility Analysis</h2>
          <p className="text-xs text-slate-400 mt-0.5">Real PSNR / MSE / SSIM computed via scikit-image.</p>
        </div>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {cards.map((c) => (
          <div key={c.key} className="bg-bg/40 border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider mono">
                {c.icon} {c.label}
              </div>
              <span className={tone(metrics.interpretation[c.key] as Interp)}>
                {metrics.interpretation[c.key]}
              </span>
            </div>
            <div className="mt-3 text-2xl font-semibold mono text-accent">{c.value}</div>
            <p className="mt-2 text-xs text-slate-500 leading-relaxed">{c.hint}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <Stat label="Modified pixels" value={modification.modified_pixels.toLocaleString()} />
        <Stat label="Total pixels" value={modification.total_pixels.toLocaleString()} />
        <Stat label="Modification %" value={`${modification.modified_percent.toFixed(3)}%`} />
        <Stat label="Bit flips" value={modification.channel_bit_flips.toLocaleString()} />
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-bg/30 border border-border rounded-md px-3 py-2">
      <div className="text-slate-500 mono uppercase text-[10px] tracking-wider">{label}</div>
      <div className="mono text-slate-200 mt-0.5">{value}</div>
    </div>
  );
}
