import { useEffect, useRef } from "react";
import { ArrowDownRight, Terminal, FileCode2 } from "lucide-react";

/**
 * Canvas of falling bit-mask columns. Each column is a vertical stream of
 * pipe-joined bits, drifting down at its own speed; `1`s glow volt, `0`s
 * stay faint — the record the contract keeps, as weather.
 */
function MaskRain() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0;
    let h = 0;
    let raf = 0;
    const DPR = Math.min(window.devicePixelRatio || 1, 2);

    type Col = { x: number; y: number; speed: number; bits: string[] };
    let cols: Col[] = [];

    const randBit = () => (Math.random() < 0.32 ? "1" : "0");

    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * DPR;
      canvas.height = h * DPR;
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      const n = Math.max(14, Math.floor(w / 34));
      cols = Array.from({ length: n }, (_, i) => ({
        x: (i + 0.5) * (w / n),
        y: Math.random() * h,
        speed: 0.35 + Math.random() * 1.15,
        bits: Array.from({ length: 64 }, randBit),
      }));
    };

    const tick = () => {
      ctx.clearRect(0, 0, w, h);
      ctx.font = "11px 'JetBrains Mono', monospace";
      ctx.textAlign = "center";
      const rowH = 17;
      for (const c of cols) {
        const headRow = Math.floor(c.y / rowH);
        for (let r = 0; r < 42; r++) {
          const row = headRow - r;
          if (row < 0) continue;
          const y = row * rowH;
          if (y > h + rowH) continue;
          const bit = c.bits[row % c.bits.length];
          const fade = Math.max(0, 1 - r / 30);
          if (bit === "1") {
            ctx.fillStyle = `rgba(198, 241, 53, ${(0.75 * fade).toFixed(3)})`;
          } else {
            ctx.fillStyle = `rgba(120, 128, 122, ${(0.4 * fade).toFixed(3)})`;
          }
          ctx.fillText(bit, c.x, y);
          if (r % 3 === 0) {
            ctx.fillStyle = `rgba(50, 56, 52, ${(0.5 * fade).toFixed(3)})`;
            ctx.fillText("|", c.x + 8, y);
          }
        }
        c.y += c.speed;
        if (c.y - 42 * rowH > h) {
          c.y = -20;
          c.speed = 0.35 + Math.random() * 1.15;
          c.bits = c.bits.map(() => randBit());
        }
        if (Math.random() < 0.06) {
          c.bits[Math.floor(Math.random() * c.bits.length)] = randBit();
        }
      }
      raf = requestAnimationFrame(tick);
    };

    resize();
    tick();
    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={ref} className="absolute inset-0 h-full w-full opacity-60" />;
}

const STATS = [
  ["10", "clauses max", "the prompt stays small enough to trust"],
  ["2", "passes", "frozen order · reversed & renumbered"],
  ["0", "tolerance", "nodes agree on the whole mask, exactly"],
  ["1", "way down", "the curator's public strike — row kept"],
];

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden border-b border-line">
      <div className="meridian-grid absolute inset-0" />
      <MaskRain />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_55%_at_50%_38%,transparent_10%,#060708_78%)]" />

      <div className="relative mx-auto max-w-[1440px] px-5 pb-16 pt-36 md:px-10 md:pb-24 md:pt-44">
        <div className="animate-rise flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.28em] text-dim">
          <span className="h-px w-10 bg-volt/70" />
          GenLayer Intelligent Contract · Optimistic Democracy
        </div>

        <h1 className="mt-8 max-w-[16ch] text-[13.5vw] font-semibold leading-[0.92] tracking-[-0.03em] md:text-[8.2rem]">
          <span className="animate-rise block" style={{ animationDelay: "0.08s" }}>
            Filings in.
          </span>
          <span className="animate-rise block" style={{ animationDelay: "0.2s" }}>
            <span className="text-volt">Bits</span> across.
          </span>
          <span className="animate-rise block text-dim" style={{ animationDelay: "0.32s" }}>
            The contract counts.
          </span>
        </h1>

        <div className="mt-12 grid gap-10 md:grid-cols-12">
          <p className="animate-rise max-w-xl text-base leading-relaxed text-dim md:col-span-6 md:text-lg" style={{ animationDelay: "0.42s" }}>
            Meridian is milestone attestation for grants: a reusable primitive that
            audits filings against conditions{" "}
            <span className="text-ink">frozen before any filing existed</span> — one
            digit per condition, asked twice, in both orders — and what crosses
            consensus is{" "}
            <span className="font-mono text-volt">1|0|1|1</span>, never a verdict.
            The standing is a union that can only move{" "}
            <span className="text-ink">up</span>. Nobody declares the milestone met.
          </p>
          <div className="animate-rise flex flex-col items-start gap-3 md:col-span-6 md:items-end" style={{ animationDelay: "0.5s" }}>
            <a
              href="#audit"
              className="group flex items-center gap-3 border border-volt/70 bg-volt px-6 py-3.5 font-mono text-xs font-semibold uppercase tracking-[0.18em] text-void transition-all hover:bg-transparent hover:text-volt"
            >
              Run an audit round
              <ArrowDownRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:translate-y-0.5" strokeWidth={2} />
            </a>
            <div className="flex gap-3">
              <a
                href="#repo"
                className="flex items-center gap-2 border border-line bg-panel px-5 py-3.5 font-mono text-xs uppercase tracking-[0.18em] text-dim transition-colors hover:border-volt/50 hover:text-ink"
              >
                <FileCode2 className="h-4 w-4" strokeWidth={1.8} /> The contract
              </a>
              <a
                href="#quickstart"
                className="flex items-center gap-2 border border-line bg-panel px-5 py-3.5 font-mono text-xs uppercase tracking-[0.18em] text-dim transition-colors hover:border-volt/50 hover:text-ink"
              >
                <Terminal className="h-4 w-4" strokeWidth={1.8} /> pytest
              </a>
            </div>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-2 border border-line md:grid-cols-4" style={{ animationDelay: "0.6s" }}>
          {STATS.map(([v, k, d], i) => (
            <div
              key={k}
              className="animate-rise border-line p-5 odd:border-r max-md:[&:nth-child(-n+2)]:border-b md:[&:not(:last-child)]:border-r md:p-6"
              style={{ animationDelay: `${0.55 + i * 0.08}s` }}
            >
              <div className="font-mono text-3xl font-semibold text-volt md:text-4xl">{v}</div>
              <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.2em] text-ink">{k}</div>
              <div className="mt-2 text-xs leading-relaxed text-faint">{d}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
