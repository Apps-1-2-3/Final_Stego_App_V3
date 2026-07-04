import { useState } from "react";

export function EmbeddingVisualizer({ originalUrl, stegoUrl, diffUrl }:
  { originalUrl: string; stegoUrl: string; diffUrl: string }) {
  const [view, setView] = useState<"original" | "stego" | "diff">("diff");
  const src = view === "original" ? originalUrl : view === "stego" ? stegoUrl : diffUrl;
  return (
    <section className="panel p-5 fade-in">
      <header className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h2 className="text-lg font-semibold">Embedding Visualization</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Difference map highlights every pixel modified during adaptive LSB embedding.
          </p>
        </div>
        <div className="flex gap-1">
          {(["original", "stego", "diff"] as const).map((v) => (
            <button key={v} onClick={() => setView(v)}
              className={`px-3 py-1.5 rounded-md text-xs mono uppercase border transition
                ${view === v ? "border-accent text-accent bg-accent/10" : "border-border text-slate-400 hover:border-accent/40"}`}>
              {v === "diff" ? "Difference" : v}
            </button>
          ))}
        </div>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <ImageBox label="Original" url={originalUrl} highlighted={view === "original"} />
        <ImageBox label="Stego" url={stegoUrl} highlighted={view === "stego"} />
        <ImageBox label="Difference" url={diffUrl} highlighted={view === "diff"} />
      </div>
      <div className="mt-4 bg-bg/30 border border-border rounded-md p-3 text-center">
        <img src={src} alt={view} className="mx-auto max-h-96 rounded-lg border border-border" />
        <div className="text-xs mono uppercase text-slate-400 mt-2">{view} (large view)</div>
      </div>
    </section>
  );
}

function ImageBox({ label, url, highlighted }: { label: string; url: string; highlighted: boolean }) {
  return (
    <div className={`border rounded-lg overflow-hidden transition ${highlighted ? "border-accent" : "border-border"}`}>
      <div className="bg-bg/40 px-3 py-2 text-xs mono uppercase tracking-wider text-slate-400 border-b border-border">
        {label}
      </div>
      <img src={url} alt={label} className="w-full aspect-square object-contain bg-bg/60" />
    </div>
  );
}
