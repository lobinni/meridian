import { useEffect, useMemo, useRef, useState } from "react";
import {
  Play,
  RotateCcw,
  ShieldAlert,
  FileText,
  ArrowDown,
  Equal,
  Combine,
  Lock,
  Unlock,
  XOctagon,
  CheckCircle2,
} from "lucide-react";
import { cn } from "../utils/cn";
import { MaskRow, parseMask } from "./Bitmask";

const CONDITIONS = [
  "alpha audit report published with zero critical findings",
  "beta testnet live with five hundred weekly users",
  "gamma docs covering every public endpoint",
  "delta mainnet deployed and verified on the explorer",
];
const SHORT = ["alpha", "beta", "gamma", "delta"];
const BAR = 3;

type Filing = {
  id: number;
  name: string;
  text: string;
  truth: string; // the mask an honest model returns, frozen order
};

const FILINGS: Filing[] = [
  {
    id: 0,
    name: "Narrative only",
    text: "We are enrolled to begin the alpha audit in October; the beta launch is scheduled for next quarter.",
    truth: "0|0|0|0",
  },
  {
    id: 1,
    name: "Artefact bundle",
    text: "Audit PDF published, zero criticals. Telemetry: 812 weekly users on beta. Docs cover all 41 endpoints.",
    truth: "1|1|1|0",
  },
  {
    id: 2,
    name: "Deployment pack",
    text: "Beta load report attached; delta mainnet contract verified on the explorer. Audit still in review.",
    truth: "0|1|0|1",
  },
];

/** An honest model judges by content: the reversed list just re-numbers rows. */
function honestReversed(truth: string): string {
  return parseMask(truth).reverse().join("|");
}

/** A position-leaning model trusts the TOP HALF of whatever list it sees. */
function leaningPass(listLenSeen: number): number[] {
  return Array.from({ length: listLenSeen }, (_, i) => (i < listLenSeen / 2 ? 1 : 0));
}

type BankedRow = { filing: Filing; mask: string; counted: boolean; struck: boolean; void: boolean };

type Stage =
  | "idle"
  | "forward"
  | "reversed"
  | "unreversed"
  | "merged"
  | "verdict"
  | "banked";

export function AuditLab() {
  const [filing, setFiling] = useState<Filing>(FILINGS[1]);
  const [leaning, setLeaning] = useState(false);
  const [stage, setStage] = useState<Stage>("idle");
  const [shownFwd, setShownFwd] = useState(0);
  const [shownRev, setShownRev] = useState(0);
  const [bank, setBank] = useState<BankedRow[]>([]);
  const [sealed, setSealed] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const n = CONDITIONS.length;

  const { fwdMask, revShownMask, revUnreversed, merged } = useMemo(() => {
    const truthBits = parseMask(filing.truth);
    if (!leaning) {
      const fwd = truthBits;
      const revShown = parseMask(honestReversed(filing.truth));
      const revUn = [...revShown].reverse();
      const m = fwd.map((b, i) => (b === 1 && revUn[i] === 1 ? 1 : 0));
      return { fwdMask: fwd, revShownMask: revShown, revUnreversed: revUn, merged: m };
    }
    const fwd = leaningPass(n);
    const revShown = leaningPass(n);
    const revUn = [...revShown].reverse();
    const m = fwd.map((b, i) => (b === 1 && revUn[i] === 1 ? 1 : 0));
    return { fwdMask: fwd, revShownMask: revShown, revUnreversed: revUn, merged: m };
  }, [filing, leaning, n]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const clearTimers = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };

  const run = () => {
    clearTimers();
    setStage("forward");
    setShownFwd(0);
    setShownRev(0);
    const t = (ms: number, fn: () => void) => timers.current.push(setTimeout(fn, ms));
    for (let i = 1; i <= n; i++) t(200 + i * 170, () => setShownFwd(i));
    t(200 + n * 170 + 500, () => setStage("reversed"));
    for (let i = 1; i <= n; i++) t(200 + n * 170 + 500 + i * 170, () => setShownRev(i));
    const afterRev = 200 + n * 170 + 500 + n * 170 + 600;
    t(afterRev, () => setStage("unreversed"));
    t(afterRev + 750, () => setStage("merged"));
    t(afterRev + 1450, () => setStage("verdict"));
  };

  const bankIt = () => {
    const void_ = merged.every((b) => b === 0);
    setBank((rows) => [
      ...rows,
      { filing, mask: merged.join("|"), counted: !sealed, struck: false, void: void_ },
    ]);
    setStage("banked");
  };

  // one way, one exception: the contract has no unstrike. once struck, a row
  // stays struck — reset the lab to play again, exactly like on chain.
  const strike = (i: number) =>
    setBank((rows) => rows.map((r, k) => (k === i ? { ...r, struck: true } : r)));

  const reset = () => {
    clearTimers();
    setBank([]);
    setStage("idle");
    setSealed(false);
  };

  const standing = useMemo(() => {
    const acc = new Array(n).fill(0);
    for (const r of bank) {
      if (r.counted && !r.struck) {
        parseMask(r.mask).forEach((b, i) => {
          if (b === 1) acc[i] = 1;
        });
      }
    }
    return acc;
  }, [bank, n]);

  const nStanding = standing.reduce((a, b) => a + b, 0);
  const attained = nStanding >= BAR;
  const stageOrder: Stage[] = ["forward", "reversed", "unreversed", "merged", "verdict"];
  const stageIdx = stageOrder.indexOf(stage);
  const past = (s: Stage) =>
    stage === "banked" || (stage !== "idle" && stageIdx >= stageOrder.indexOf(s));

  return (
    <section id="audit" className="relative border-b border-line">
      <div className="mx-auto max-w-[1440px] px-5 py-20 md:px-10 md:py-28">
        <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.28em] text-dim">
          <span className="h-px w-10 bg-volt/70" /> 02 · anatomy of an audit
        </div>
        <h2 className="mt-6 max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
          Two passes. One <span className="text-volt">AND</span>. No confidence score, ever.
        </h2>
        <p className="mt-5 max-w-2xl text-dim">
          This is <span className="font-mono text-xs text-ink">judge()</span> running in
          your browser with the same rules the validators run: both presentation orders,
          a bit only if <span className="text-ink">both</span> passes raised it, and the
          whole mask compared exactly. Flip the model to{" "}
          <span className="text-ember">position-leaning</span> and watch the bias land
          on zeros — not in a tolerance.
        </p>

        {/* control strip */}
        <div className="mt-10 flex flex-wrap items-center gap-3">
          {FILINGS.map((f) => (
            <button
              key={f.id}
              onClick={() => {
                setFiling(f);
                setStage("idle");
                setShownFwd(0);
                setShownRev(0);
              }}
              disabled={stage !== "idle" && stage !== "banked"}
              className={cn(
                "flex items-center gap-2 border px-4 py-2.5 font-mono text-xs uppercase tracking-[0.14em] transition-all disabled:opacity-40",
                filing.id === f.id
                  ? "border-volt/70 bg-volt/10 text-volt"
                  : "border-line bg-panel text-dim hover:border-line2 hover:text-ink"
              )}
            >
              <FileText className="h-3.5 w-3.5" strokeWidth={1.8} />
              {f.name}
              <span className="text-faint">{f.truth}</span>
            </button>
          ))}
          <button
            onClick={() => {
              setLeaning((v) => !v);
              setStage("idle");
            }}
            className={cn(
              "flex items-center gap-2 border px-4 py-2.5 font-mono text-xs uppercase tracking-[0.14em] transition-all",
              leaning
                ? "border-ember/70 bg-ember/10 text-ember"
                : "border-line bg-panel text-dim hover:border-line2 hover:text-ink"
            )}
          >
            <ShieldAlert className="h-3.5 w-3.5" strokeWidth={1.8} />
            {leaning ? "position-leaning model: ON" : "honest model"}
          </button>
          <button
            onClick={stage === "verdict" ? bankIt : run}
            className="ml-auto flex items-center gap-2 border border-volt/70 bg-volt px-6 py-2.5 font-mono text-xs font-semibold uppercase tracking-[0.16em] text-void transition-colors hover:bg-transparent hover:text-volt"
          >
            {stage === "verdict" ? (
              <>
                <Combine className="h-4 w-4" strokeWidth={2} /> Bank into standing
              </>
            ) : (
              <>
                <Play className="h-4 w-4" strokeWidth={2} /> Run audit
              </>
            )}
          </button>
        </div>

        {/* the filing under audit */}
        <div className="mt-4 border border-line bg-panel p-4">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-faint">
            &lt;filing&gt; — everything inside is data, never a request
          </div>
          <p className="mt-2 font-mono text-sm leading-relaxed text-dim">“{filing.text}”</p>
        </div>

        {/* the two passes */}
        <div className="mt-6 grid gap-px border border-line bg-line lg:grid-cols-2">
          {/* forward */}
          <div className="bg-void p-5 md:p-7">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
                pass one · frozen order
              </span>
              <span
                className={cn(
                  "font-mono text-[10px] uppercase tracking-widest",
                  past("forward") ? "text-volt" : "text-faint"
                )}
              >
                {past("forward") ? "ran on leader + every validator" : "waiting"}
              </span>
            </div>
            <ol className="mt-4 space-y-1.5">
              {CONDITIONS.map((c, i) => (
                <li key={i} className="flex items-center gap-3 font-mono text-xs">
                  <span className="w-7 text-faint">[{i}]</span>
                  <span className="text-dim">{c}</span>
                  <span
                    className={cn(
                      "ml-auto grid h-6 w-6 place-items-center border tabular transition-all",
                      shownFwd > i
                        ? fwdMask[i] === 1
                          ? "border-volt/70 bg-volt/15 text-volt"
                          : "border-line text-faint"
                        : "border-line/50 text-transparent"
                    )}
                  >
                    {shownFwd > i ? fwdMask[i] : "·"}
                  </span>
                </li>
              ))}
            </ol>
          </div>

          {/* reversed */}
          <div className="bg-void p-5 md:p-7">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
                pass two · reversed & renumbered
              </span>
              <span
                className={cn(
                  "font-mono text-[10px] uppercase tracking-widest",
                  past("reversed") ? "text-volt" : "text-faint"
                )}
              >
                {past("reversed") ? "same filing, flipped list" : "waiting"}
              </span>
            </div>
            <ol className="mt-4 space-y-1.5">
              {[...CONDITIONS].reverse().map((c, i) => (
                <li key={i} className="flex items-center gap-3 font-mono text-xs">
                  <span className="w-7 text-faint">[{i}]</span>
                  <span className="text-dim">{c}</span>
                  <span
                    className={cn(
                      "ml-auto grid h-6 w-6 place-items-center border tabular transition-all",
                      shownRev > i
                        ? revShownMask[i] === 1
                          ? "border-volt/70 bg-volt/15 text-volt"
                          : "border-line text-faint"
                        : "border-line/50 text-transparent"
                    )}
                  >
                    {shownRev > i ? revShownMask[i] : "·"}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </div>

        {/* the fold */}
        <div className="mt-px grid gap-px border border-t-0 border-line bg-line md:grid-cols-3">
          <div
            className={cn(
              "bg-void p-5 transition-opacity md:p-7",
              past("unreversed") ? "opacity-100" : "opacity-35"
            )}
          >
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
              <ArrowDown className="h-3.5 w-3.5" strokeWidth={1.8} /> unreverse pass two
            </div>
            <MaskRow bits={revUnreversed} className="mt-4" labels={SHORT} dimZeros={!past("unreversed")} />
            <p className="mt-3 text-xs leading-relaxed text-faint">
              Read back into the frozen order — bit i now means condition i again,
              whichever order the model saw.
            </p>
          </div>
          <div
            className={cn(
              "bg-void p-5 transition-opacity md:p-7",
              past("merged") ? "opacity-100" : "opacity-35"
            )}
          >
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
              <Equal className="h-3.5 w-3.5" strokeWidth={1.8} /> merge: both or nothing
            </div>
            <MaskRow bits={merged} className="mt-4" labels={SHORT} dimZeros={!past("merged")} />
            <p className="mt-3 text-xs leading-relaxed text-faint">
              <span className="font-mono text-dim">1 ∧ 1 → 1</span>, everything else → 0.
              A row only one ordering marked was a guess; a guess is stored as no
              demonstration.
            </p>
          </div>
          <div
            className={cn(
              "relative bg-void p-5 transition-opacity md:p-7",
              past("verdict") ? "opacity-100" : "opacity-35"
            )}
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
              what crosses consensus
            </div>
            <div className="mt-4 font-mono text-2xl tabular tracking-[0.3em]">
              {merged.map((b, i) => (
                <span key={i}>
                  <span className={b ? "text-volt glow-volt rounded-sm px-1" : "text-faint"}>{b}</span>
                  {i < n - 1 && <span className="text-line2">|</span>}
                </span>
              ))}
            </div>
            <p className="mt-3 text-xs leading-relaxed text-faint">
              Validators re-run both passes and must match this exactly. The{" "}
              <span className="font-mono text-dim">because</span> string is stored,
              scrubbed — and never compared.
            </p>
            {stage === "verdict" && (
              <div className="absolute right-4 top-4 flex items-center gap-1.5 border border-volt/50 bg-volt/10 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-volt">
                <CheckCircle2 className="h-3 w-3" strokeWidth={2} /> settled
              </div>
            )}
          </div>
        </div>

        {leaning && stage === "verdict" && (
          <div className="mt-4 border border-ember/40 bg-ember/5 p-4 font-mono text-xs leading-relaxed text-ember">
            The leaning model marked the top half of each list — different rows in each
            pass. Both passes disagreed, the mask is all zeros, and{" "}
            <span className="text-ink">nothing records how unsure it was</span>. The
            value carries the uncertainty; the comparison stays exact.
          </div>
        )}

        {/* the standing machine */}
        <div className="mt-14 grid gap-6 lg:grid-cols-5">
          <div className="border border-line bg-panel lg:col-span-3">
            <div className="flex items-center justify-between border-b border-line px-5 py-3">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
                the record — every filing, struck ones too
              </span>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setSealed((v) => !v)}
                  className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-dim transition-colors hover:text-ink"
                >
                  {sealed ? (
                    <Lock className="h-3.5 w-3.5 text-ember" strokeWidth={1.8} />
                  ) : (
                    <Unlock className="h-3.5 w-3.5" strokeWidth={1.8} />
                  )}
                  {sealed ? "sealed" : "unsealed"}
                </button>
                <button
                  onClick={reset}
                  className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-dim transition-colors hover:text-ink"
                >
                  <RotateCcw className="h-3.5 w-3.5" strokeWidth={1.8} /> reset
                </button>
              </div>
            </div>
            {bank.length === 0 ? (
              <p className="p-8 text-center font-mono text-xs text-faint">
                no filings yet — run an audit, bank it, watch the union grow
              </p>
            ) : (
              <ul>
                {bank.map((r, i) => (
                  <li
                    key={i}
                    className={cn(
                      "flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-line px-5 py-3 last:border-b-0",
                      r.struck && "opacity-45"
                    )}
                  >
                    <span className="font-mono text-[10px] text-faint">#{i}</span>
                    <span className="font-mono text-xs text-ink">{r.filing.name}</span>
                    <span className="font-mono text-xs tabular">
                      {r.mask.split("").map((ch, k) =>
                        ch === "1" ? (
                          <span key={k} className="text-volt">1</span>
                        ) : ch === "0" ? (
                          <span key={k} className="text-faint">0</span>
                        ) : (
                          <span key={k} className="text-line2">|</span>
                        )
                      )}
                    </span>
                    {r.void && (
                      <span className="border border-line px-1.5 py-0.5 font-mono text-[9px] uppercase text-faint">void</span>
                    )}
                    {!r.counted && (
                      <span className="border border-ember/50 px-1.5 py-0.5 font-mono text-[9px] uppercase text-ember">
                        recorded · not counted (sealed)
                      </span>
                    )}
                    {r.struck && (
                      <span className="border border-ember/70 bg-ember/10 px-1.5 py-0.5 font-mono text-[9px] uppercase text-ember">
                        struck — row kept
                      </span>
                    )}
                    {r.struck ? (
                      <span className="ml-auto border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-faint">
                        no unstrike
                      </span>
                    ) : (
                      <button
                        onClick={() => strike(i)}
                        className="ml-auto flex items-center gap-1 border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-dim transition-colors hover:border-ember/60 hover:text-ember"
                      >
                        <XOctagon className="h-3 w-3" strokeWidth={1.8} />
                        strike
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex flex-col border border-line bg-panel lg:col-span-2">
            <div className="border-b border-line px-5 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
              standing — union of counted, unstruck masks
            </div>
            <div className="flex flex-1 flex-col justify-between gap-6 p-5">
              <MaskRow bits={standing} size="lg" labels={SHORT} />
              <div>
                <div className="flex justify-between font-mono text-[10px] uppercase tracking-widest text-faint">
                  <span>bar: {BAR} conditions</span>
                  <span className="tabular">{nStanding} / {CONDITIONS.length}</span>
                </div>
                <div className="mt-2 flex gap-1">
                  {Array.from({ length: CONDITIONS.length }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-1.5 flex-1 transition-colors duration-500",
                        i < nStanding ? (i < BAR ? "bg-volt" : "bg-volt/50") : "bg-line"
                      )}
                    />
                  ))}
                </div>
              </div>
              <div
                className={cn(
                  "border px-4 py-3 text-center font-mono text-sm font-semibold uppercase tracking-[0.3em] transition-all",
                  attained
                    ? "border-volt/70 bg-volt/10 text-volt glow-volt"
                    : "border-line text-faint"
                )}
              >
                {attained ? "attained" : sealed ? "sealed · building" : "building"}
              </div>
              <p className="text-xs leading-relaxed text-faint">
                Union grows on audits; it falls only when you strike — and then it is
                recomputed from exactly the rows that are counted and unstruck. Try it:
                attain, then strike the filing that carried you over the bar.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
