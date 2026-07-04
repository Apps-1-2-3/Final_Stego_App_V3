import { Shield, Lock, Key, Shuffle, CheckCircle2 } from "lucide-react";

type Layer = { name: string; detail: string };
type Sec = {
  layers: Layer[];
  password_entropy_bits: number;
  password_strength: string;
  capacity_bits: number;
  used_bits: number;
  utilization_percent: number;
  brute_force_pbkdf2_cost_note: string;
};

const icons: Record<string, JSX.Element> = {
  "PBKDF2-SHA256": <Key size={16} />,
  "AES-128-CBC": <Lock size={16} />,
  "HMAC-SHA256": <Shield size={16} />,
  "Adaptive LSB": <CheckCircle2 size={16} />,
  "Key-seeded PRNG": <Shuffle size={16} />,
};

const strengthTone = (s: string) =>
  s === "very strong" || s === "strong" ? "chip-good" :
  s === "moderate" ? "chip-warn" : "chip-bad";

export function SecurityPanel({ sec, keyValid }: { sec: Sec; keyValid?: boolean | null }) {
  return (
    <section className="panel p-5 fade-in">
      <header className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2"><Shield size={18} className="text-accent" /> Security Analysis</h2>
          <p className="text-xs text-slate-400 mt-0.5">Multi-layer defence stack and key strength assessment.</p>
        </div>
        {keyValid !== null && keyValid !== undefined && (
          <span className={keyValid ? "chip-good" : "chip-bad"}>
            {keyValid ? "Key validated" : "Key rejected"}
          </span>
        )}
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-3 mb-4">
        {sec.layers.map((l, i) => (
          <div key={l.name} className="bg-bg/40 border border-border rounded-lg p-3 relative">
            <div className="flex items-center gap-2 text-accent">
              {icons[l.name] || <Shield size={16} />}
              <span className="text-xs mono uppercase tracking-wider">L{i + 1}</span>
            </div>
            <div className="mt-2 font-medium text-sm">{l.name}</div>
            <div className="text-[11px] text-slate-500 mt-1 leading-snug">{l.detail}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Password entropy" value={`${sec.password_entropy_bits.toFixed(1)} bits`}>
          <span className={strengthTone(sec.password_strength)}>{sec.password_strength}</span>
        </Stat>
        <Stat label="Capacity" value={`${(sec.capacity_bits / 8 / 1024).toFixed(1)} KiB`} />
        <Stat label="Used" value={`${(sec.used_bits / 8).toLocaleString()} B`} />
        <Stat label="Utilization" value={`${sec.utilization_percent.toFixed(2)}%`} />
      </div>

      <p className="mt-4 text-[11px] text-slate-500 leading-relaxed border-t border-border pt-3">
        <span className="text-slate-300 mono">Brute-force note:</span> {sec.brute_force_pbkdf2_cost_note}
      </p>
    </section>
  );
}

function Stat({ label, value, children }: { label: string; value: string; children?: React.ReactNode }) {
  return (
    <div className="bg-bg/30 border border-border rounded-md px-3 py-2.5">
      <div className="flex items-center justify-between">
        <div className="text-slate-500 mono uppercase text-[10px] tracking-wider">{label}</div>
        {children}
      </div>
      <div className="mono text-slate-200 mt-1 text-sm">{value}</div>
    </div>
  );
}
