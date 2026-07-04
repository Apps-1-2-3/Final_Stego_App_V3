import { useState, useCallback } from "react";
import { UploadCloud } from "lucide-react";

export function Dropzone({ onFile, file, accept = "image/png,image/bmp" }:
  { onFile: (f: File) => void; file: File | null; accept?: string }) {
  const [over, setOver] = useState(false);
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  }, [onFile]);
  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={`block cursor-pointer border-2 border-dashed rounded-xl p-6 text-center transition-all
        ${over ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"}`}
    >
      <input type="file" accept={accept} className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }} />
      <UploadCloud className="mx-auto mb-2 text-accent" size={28} />
      {file ? (
        <div>
          <div className="mono text-sm truncate">{file.name}</div>
          <div className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(1)} KB</div>
        </div>
      ) : (
        <div>
          <div className="text-sm">Drop image here or click to browse</div>
          <div className="text-xs text-slate-500 mt-1">PNG / BMP recommended</div>
        </div>
      )}
    </label>
  );
}
