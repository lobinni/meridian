import { useState, type ReactNode } from "react";
import {
  UserRound,
  KeyRound,
  Gauge,
  ShieldCheck,
  Copy,
  Check,
  FolderTree,
  FileCode2,
  TerminalSquare,
  Terminal,
  ArrowUpRight,
  Boxes,
} from "lucide-react";
import {
  PERMISSIONS,
  BUDGETS,
  THREATS,
  API_WRITES,
  API_READS,
  REPO,
  QUICKSTART,
  DEPLOYMENT,
} from "../data/content";
import { cn } from "../utils/cn";

function SectionHead({
  id,
  index,
  title,
  hint,
}: {
  id: string;
  index: string;
  title: ReactNode;
  hint?: string;
}) {
  return (
    <div id={id} className="scroll-mt-20">
      <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.28em] text-dim">
        <span className="h-px w-10 bg-volt/70" /> {index}
      </div>
      <h2 className="mt-6 text-4xl font-semibold tracking-tight md:text-5xl">{title}</h2>
      {hint && <p className="mt-4 max-w-2xl text-sm leading-relaxed text-faint">{hint}</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Permissions + budgets + threats                                    */
/* ------------------------------------------------------------------ */

export function Permissions() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1440px] px-5 py-20 md:px-10 md:py-28">
        <SectionHead
          id="permissions"
          index="03 · who may write, and how much"
          title={
            <>
              Every write is <span className="text-volt">address-bound</span>.<br />
              Every budget is capped.
            </>
          }
          hint="A standing is worth exactly as much as the record it was computed from. The principals are addresses, every role spends only its own allowance, and re-empowering a keeper never refills one."
        />

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <div className="border border-line">
            <div className="flex items-center gap-2 border-b border-line bg-panel px-5 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
              <KeyRound className="h-3.5 w-3.5 text-volt" strokeWidth={1.8} /> authority
            </div>
            <table className="w-full text-left">
              <tbody>
                {PERMISSIONS.map((p) => (
                  <tr key={p.call} className="border-b border-line last:border-b-0">
                    <td className="px-5 py-3.5 align-top font-mono text-xs text-volt">{p.call}</td>
                    <td className="px-2 py-3.5 align-top text-sm text-ink">{p.who}</td>
                    <td className="hidden px-5 py-3.5 align-top text-xs leading-relaxed text-faint md:table-cell">
                      {p.note}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border border-line">
            <div className="flex items-center gap-2 border-b border-line bg-panel px-5 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
              <Gauge className="h-3.5 w-3.5 text-volt" strokeWidth={1.8} /> budgets — no party
              can lock another out
            </div>
            <table className="w-full text-left">
              <tbody>
                {BUDGETS.map((b) => (
                  <tr key={b.item} className="border-b border-line last:border-b-0">
                    <td className="px-5 py-3 align-top text-xs leading-relaxed text-dim">{b.item}</td>
                    <td className="whitespace-nowrap px-2 py-3 align-top font-mono text-xs text-volt">
                      {b.value}
                    </td>
                    <td className="hidden px-5 py-3 align-top text-xs leading-relaxed text-faint md:table-cell">
                      {b.protects}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6 border border-line">
          <div className="flex items-center gap-2 border-b border-line bg-panel px-5 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
            <ShieldCheck className="h-3.5 w-3.5 text-volt" strokeWidth={1.8} /> threat → answer
          </div>
          <div className="grid md:grid-cols-2">
            {THREATS.map(([t, a], i) => (
              <div
                key={t}
                className={cn(
                  "flex items-baseline gap-3 border-line px-5 py-3",
                  i % 2 === 0 && "md:border-r",
                  "border-b last:border-b-0 md:[&:nth-last-child(2)]:border-b-0"
                )}
              >
                <UserRound className="h-3 w-3 shrink-0 translate-y-0.5 text-ember" strokeWidth={2} />
                <div className="text-xs leading-relaxed">
                  <span className="text-ink">{t}</span>
                  <span className="text-faint"> → </span>
                  <span className="text-dim">{a}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  API                                                                */
/* ------------------------------------------------------------------ */

export function Api() {
  return (
    <section className="border-b border-line bg-panel/40">
      <div className="mx-auto max-w-[1440px] px-5 py-20 md:px-10 md:py-28">
        <SectionHead
          id="api"
          index="04 · the interface"
          title={
            <>
              Seven writes. Twelve reads. <span className="text-stroke">Zero hidden state.</span>
            </>
          }
          hint="attained() and holding() return false rather than raising for a gate that has earned nothing yet — so a calling contract has one branch to handle, not two."
        />
        <div className="mt-12 grid gap-6 lg:grid-cols-5">
          <ApiTable title="writes" rows={API_WRITES} accent className="lg:col-span-2" />
          <ApiTable title="reads" rows={API_READS} className="lg:col-span-3" />
        </div>
        <div className="code-frame mt-6 overflow-x-auto p-6">
          <pre className="font-mono text-xs leading-relaxed text-dim">
            <span className="text-faint">{"// gating a payout contract on the outcome\n"}</span>
            <span className="text-volt">if</span> meridian.<span className="text-frost">attained_for</span>(gate_id, str(payee)):{"\n"}
            {"    "}self._release(payee){"\n\n"}
            <span className="text-faint">{"# or on one specific condition — the audit clause, specifically\n"}</span>
            <span className="text-volt">if</span> meridian.<span className="text-frost">holding</span>(gate_id, <span className="text-volt">0</span>):{"\n"}
            {"    "}self._mark_audited()
          </pre>
        </div>
      </div>
    </section>
  );
}

function ApiTable({
  title,
  rows,
  accent,
  className,
}: {
  title: string;
  rows: { sig: string; effect: string }[];
  accent?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("border border-line bg-void", className)}>
      <div
        className={cn(
          "border-b border-line px-5 py-3 font-mono text-[10px] uppercase tracking-[0.2em]",
          accent ? "text-volt" : "text-dim"
        )}
      >
        {title}
      </div>
      <ul>
        {rows.map((r) => (
          <li key={r.sig} className="border-b border-line px-5 py-3 last:border-b-0">
            <div className={cn("font-mono text-xs", accent ? "text-volt" : "text-frost")}>{r.sig}</div>
            <div className="mt-1 text-xs leading-relaxed text-faint">{r.effect}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Repository                                                         */
/* ------------------------------------------------------------------ */

const KIND_STYLE: Record<string, string> = {
  submission: "border-volt/70 bg-volt/10 text-volt",
  suite: "border-frost/50 text-frost",
  infra: "border-line2 text-dim",
  "opt-in": "border-line2 text-dim",
  sample: "border-line2 text-dim",
  doc: "border-line2 text-dim",
  deployment: "border-volt/50 text-volt",
  tool: "border-frost/40 text-frost",
};

export function Repo() {
  const [copied, setCopied] = useState<string | null>(null);
  const copy = (p: string) => {
    navigator.clipboard?.writeText(p).catch(() => {});
    setCopied(p);
    setTimeout(() => setCopied((c) => (c === p ? null : c)), 1200);
  };

  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1440px] px-5 py-20 md:px-10 md:py-28">
        <SectionHead
          id="repo"
          index="05 · the repository"
          title={
            <>
              One file is the submission.
              <br />
              <span className="text-stroke">The rest exists so you can trust it.</span>
            </>
          }
        />
        <div className="mt-10 border border-volt/40 bg-volt/5 p-5 md:p-6">
          <div className="flex flex-wrap items-center gap-3">
            <FileCode2 className="h-4 w-4 text-volt" strokeWidth={1.8} />
            <span className="font-mono text-sm text-ink">contracts/meridian.py</span>
            <span className="border border-volt/60 px-2 py-0.5 font-mono text-[9px] uppercase tracking-widest text-volt">
              deployable artifact
            </span>
            <button
              onClick={() => copy("contracts/meridian.py")}
              className="ml-auto flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-dim transition-colors hover:text-volt"
            >
              {copied === "contracts/meridian.py" ? (
                <Check className="h-3.5 w-3.5 text-volt" strokeWidth={2} />
              ) : (
                <Copy className="h-3.5 w-3.5" strokeWidth={1.8} />
              )}
              {copied === "contracts/meridian.py" ? "copied" : "copy path"}
            </button>
          </div>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-dim">
            The entire Intelligent Contract — the freezing, the two-pass audit, the
            validator, the union, the budgets — in one readable file. Deploy it, verify
            the on-chain source against it byte-for-byte, submit it.
          </p>
        </div>

        {/* live deployment banner */}
        <a
          href={DEPLOYMENT.explorer}
          target="_blank"
          rel="noreferrer"
          className="group mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border border-line bg-panel p-5 transition-colors hover:border-volt/60"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute h-full w-full animate-ping rounded-full bg-volt/60" />
            <span className="h-full w-full rounded-full bg-volt" />
          </span>
          <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.24em] text-volt">
            live · {DEPLOYMENT.network}
          </span>
          <span className="font-mono text-xs text-ink md:text-sm">{DEPLOYMENT.address}</span>
          <span className="ml-auto flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-faint transition-colors group-hover:text-volt">
            explorer <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={1.8} />
          </span>
        </a>

        <div className="mt-6 border border-line">
          <div className="flex items-center gap-2 border-b border-line bg-panel px-5 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-dim">
            <FolderTree className="h-3.5 w-3.5" strokeWidth={1.8} /> tree
          </div>
          <ul>
            {REPO.map((f) => (
              <li
                key={f.path}
                className="group flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-line px-5 py-3 transition-colors last:border-b-0 hover:bg-panel/60"
              >
                <span className="font-mono text-xs text-ink">{f.path}</span>
                <span
                  className={cn(
                    "border px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-widest",
                    KIND_STYLE[f.kind]
                  )}
                >
                  {f.kind}
                </span>
                <span className="text-xs leading-relaxed text-faint">{f.desc}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Quickstart                                                         */
/* ------------------------------------------------------------------ */

export function Quickstart() {
  const [copied, setCopied] = useState<number | null>(null);
  return (
    <section className="relative overflow-hidden border-b border-line bg-panel/40">
      <div className="pointer-events-none absolute -right-24 top-10 select-none font-mono text-[18rem] font-bold leading-none text-line/40">
        &gt;_
      </div>
      <div className="relative mx-auto max-w-[1440px] px-5 py-20 md:px-10 md:py-28">
        <SectionHead
          id="quickstart"
          index="06 · run it"
          title={
            <>
              Offline in seconds. <span className="text-volt">Live when you mean it.</span>
            </>
          }
          hint="The suites run on a bundled GenVM stand-in — no Studio, no network, no model key. The integration suite is opt-in by environment variable, by design."
        />
        <div className="code-frame mt-10 max-w-3xl p-2">
          <div className="flex items-center gap-1.5 border-b border-line px-4 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-line2" />
            <span className="h-2.5 w-2.5 rounded-full bg-line2" />
            <span className="h-2.5 w-2.5 rounded-full bg-volt/60" />
            <span className="ml-3 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-faint">
              <TerminalSquare className="h-3 w-3" strokeWidth={1.8} /> shell
            </span>
          </div>
          <div className="space-y-4 p-4 md:p-5">
            {QUICKSTART.map((q, i) => (
              <div key={i}>
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 font-mono text-xs text-volt">$</span>
                  <code className="break-all font-mono text-xs leading-relaxed text-ink">{q.cmd}</code>
                  <button
                    onClick={() => {
                      navigator.clipboard?.writeText(q.cmd).catch(() => {});
                      setCopied(i);
                      setTimeout(() => setCopied((c) => (c === i ? null : c)), 1200);
                    }}
                    className="ml-auto shrink-0 text-faint transition-colors hover:text-volt"
                  >
                    {copied === i ? (
                      <Check className="h-3.5 w-3.5 text-volt" strokeWidth={2} />
                    ) : (
                      <Copy className="h-3.5 w-3.5" strokeWidth={1.8} />
                    )}
                  </button>
                </div>
                <div className="mt-1 pl-4 font-mono text-[11px] leading-relaxed text-faint">{q.out}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Footer                                                             */
/* ------------------------------------------------------------------ */

export function Footer() {
  return (
    <footer className="relative overflow-hidden">
      <div className="mx-auto max-w-[1440px] px-5 py-16 md:px-10">
        <div className="flex flex-wrap items-end justify-between gap-10">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="grid h-8 w-8 place-items-center border border-volt/60 bg-volt/10">
                <Boxes className="h-4 w-4 text-volt" strokeWidth={1.8} />
              </span>
              <span className="font-mono text-sm font-semibold tracking-[0.22em]">MERIDIAN</span>
            </div>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-faint">
              Milestone attestation rails for grants. Nobody declares the milestone
              met — the contract counts. Copy the agreement rule; that is what it is
              for. MIT.
            </p>
          </div>
          <div className="flex gap-8 font-mono text-[11px] uppercase tracking-[0.16em]">
            <div className="flex flex-col gap-2">
              <span className="text-faint">contract</span>
              <a href="#audit" className="flex items-center gap-1 text-dim transition-colors hover:text-volt">
                judge() <ArrowUpRight className="h-3 w-3" strokeWidth={1.8} />
              </a>
              <a href="#api" className="flex items-center gap-1 text-dim transition-colors hover:text-volt">
                API <ArrowUpRight className="h-3 w-3" strokeWidth={1.8} />
              </a>
            </div>
            <div className="flex flex-col gap-2">
              <span className="text-faint">project</span>
              <a href="#repo" className="flex items-center gap-1 text-dim transition-colors hover:text-volt">
                repository <ArrowUpRight className="h-3 w-3" strokeWidth={1.8} />
              </a>
              <a href="#quickstart" className="flex items-center gap-1 text-dim transition-colors hover:text-volt">
                quickstart <Terminal className="h-3 w-3" strokeWidth={1.8} />
              </a>
            </div>
          </div>
        </div>
        <div className="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6 font-mono text-[10px] uppercase tracking-[0.2em] text-faint">
          <span>GenLayer · Optimistic Democracy</span>
          <span className="tabular">frozen yardstick · exact bits · union only up</span>
        </div>
      </div>
    </footer>
  );
}
