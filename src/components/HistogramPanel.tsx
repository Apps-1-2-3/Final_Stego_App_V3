import { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";

type Hist = { r: number[]; g: number[]; b: number[] };
type Data = { original: Hist; stego: Hist; bins: number[] };

export function HistogramPanel({ data }: { data: Data }) {
  const [channel, setChannel] = useState<"r" | "g" | "b">("r");
  const color = channel === "r" ? "#f87171" : channel === "g" ? "#34d399" : "#60a5fa";

  const rows = useMemo(() => data.bins.map((b, i) => ({
    bin: b,
    original: data.original[channel][i],
    stego: data.stego[channel][i],
  })), [data, channel]);

  const totalDiff = useMemo(() =>
    rows.reduce((acc, r) => acc + Math.abs(r.original - r.stego), 0), [rows]);

  return (
    <section className="panel p-5 fade-in">
      <header className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h2 className="text-lg font-semibold">Histogram Analysis</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Per-channel 256-bin histogram. Total absolute diff: <span className="mono text-accent">{totalDiff.toLocaleString()}</span>
          </p>
        </div>
        <div className="flex gap-1">
          {(["r", "g", "b"] as const).map((c) => (
            <button key={c} onClick={() => setChannel(c)}
              className={`px-3 py-1.5 rounded-md text-xs mono uppercase border transition
                ${channel === c ? "border-accent text-accent bg-accent/10" : "border-border text-slate-400 hover:border-accent/40"}`}>
              {c}
            </button>
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
            <Line type="monotone" dataKey="original" stroke={color} strokeWidth={2} dot={false} name="Original" />
            <Line type="monotone" dataKey="stego" stroke="#a78bfa" strokeWidth={1.5} strokeDasharray="4 3" dot={false} name="Stego" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
