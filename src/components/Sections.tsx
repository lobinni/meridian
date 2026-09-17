import { useEffect, useRef, useState } from "react";
import { Lock, GitPullRequestArrow, Scale, ArrowUpFromLine, Landmark } from "lucide-react";
import { RULES } from "../data/content";
import { cn } from "../utils/cn";

function useInView(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => e.isIntersecting && setSeen(true),
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, seen };
}

/* ------------------------------------------------------------------ */
/*  The problem                                                        */
/* ------------------------------------------------------------------ */

export function Problem() {
  const { ref, seen } = useInView();
  return (
    <section className="border-b border-line" id="protocol">
      <div
        ref={ref}
        className={cn(
          "mx-auto max-w-[1440px] px-5 py-20 transition-all duration-1000 md:px-10 md:py-28",
          seen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
        )}
      >
        <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.28em] text-dim">
          <span className="h-px w-10 bg-volt/70" /> 01 · the problem
        </div>
        <div className="mt-8 grid gap-12 lg:grid-cols-12">
          <h2 className="text-4xl font-semibold leading-[1.02] tracking-tight md:text-6xl lg:col-span-7">
            “Has the team hit the milestone?” is{" "}
            <span className="text-dim">not a question</span> a model should answer
            about a pile of reports.
          </h2>
          <div className="space-y-6 text-base leading-relaxed text-dim lg:col-span-5">
            <p>
              Ask it directly and you get a confident yes, a different confidence each
              run, and no record of{" "}
              <span className="text-ink">which condition each report satisfied</span>.
              Worse, term sheets tend to be rewritten after the reports arrive — by
              whoever wants the answer to come out a particular way.
            </p>
            <p>
              The failure that costs money is quieter than a wrong answer: a report
              that <span className="text-ink">mentions</span> a condition gets read as{" "}
              <span className="text-ink">meeting</span> it. Enrollment is not a
              published audit. A schedule is not a live testnet.
            </p>
            <div className="border-l-2 border-volt/70 bg-panel p-4 font-mono text-xs leading-relaxed text-ink">
              So the yardstick is frozen before any filing exists, each filing is
              audited against it separately, and “attained” is arithmetic the contract
              does alone.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Five rules                                                         */
/* ------------------------------------------------------------------ */

const RULE_ICONS = [Lock, GitPullRequestArrow, Scale, ArrowUpFromLine, Landmark];

export function Rules() {
  return (
    <section className="border-b border-line meridian-latitudes">
      <div className="mx-auto max-w-[1440px] px-5 py-20 md:px-10 md:py-28">
        <div className="mb-14 flex flex-wrap items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.28em] text-dim">
              <span className="h-px w-10 bg-volt/70" /> the protocol
            </div>
            <h2 className="mt-6 text-4xl font-semibold tracking-tight md:text-6xl">
              Five rules, <span className="text-stroke">no discretion</span>
            </h2>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-faint">
            Everything the contract enforces is on this page. There is no admin
            override, no governance toggle, no off-chain component to trust.
          </p>
        </div>

        <div className="grid gap-px border border-line bg-line md:grid-cols-2 xl:grid-cols-5">
          {RULES.map((r, i) => {
            const Icon = RULE_ICONS[i];
            return (
              <RuleCard key={r.n} rule={r} Icon={Icon} index={i} />
            );
          })}
        </div>
      </div>
    </section>
  );
}

function RuleCard({
  rule,
  Icon,
  index,
}: {
  rule: (typeof RULES)[number];
  Icon: typeof Lock;
  index: number;
}) {
  const { ref, seen } = useInView(0.15);
  return (
    <div
      ref={ref}
      className={cn(
        "group relative flex min-h-[340px] flex-col bg-void p-6 transition-all duration-700",
        seen ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
      )}
      style={{ transitionDelay: `${index * 90}ms` }}
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] text-faint">{rule.n}</span>
        <Icon
          className="h-5 w-5 text-faint transition-colors duration-300 group-hover:text-volt"
          strokeWidth={1.5}
        />
      </div>
      <h3 className="mt-8 text-xl font-semibold tracking-tight text-ink">{rule.title}</h3>
      <p className="mt-3 text-sm leading-relaxed text-dim">{rule.body}</p>
      <div className="mt-auto pt-6">
        <div className="h-px w-full bg-line transition-colors duration-300 group-hover:bg-volt/50" />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Consensus band — the argument in one screen                        */
/* ------------------------------------------------------------------ */

export function ConsensusBand() {
  const { ref, seen } = useInView();
  const lines = [
    { k: "merge_passes([1,1,0], [1,0,1])", v: "== [1,0,0]", note: "both, or nothing" },
    { k: "merge_passes([1,1,1], None)", v: "== None", note: "an unusable pass demonstrates nothing" },
    { k: "masks_agree(mine, theirs, n)", v: "mine == theirs", note: "exact, symmetric, no tolerance" },
  ];
  return (
    <section className="relative overflow-hidden border-b border-line bg-panel">
      <div className="meridian-grid absolute inset-0 opacity-40" />
      <div
        ref={ref}
        className={cn(
          "relative mx-auto max-w-[1440px] px-5 py-20 transition-all duration-1000 md:px-10 md:py-28",
          seen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
        )}
      >
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <div className="flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.28em] text-dim">
              <span className="h-px w-10 bg-volt/70" /> the agreement rule
            </div>
            <h2 className="mt-6 text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
              Uncertainty enters the value.
              <br />
              <span className="text-volt">Never the comparison.</span>
            </h2>
            <p className="mt-6 max-w-lg leading-relaxed text-dim">
              A disagreement flag would be true exactly when two honest nodes are least
              likely to agree — and it would split them over a difference no rule acts
              on. So the mask carries everything, and nodes compare the mask byte for
              byte. Swap in a worse model and the mechanism still works: it
              demonstrates fewer conditions, which is the correct response to a worse
              model.
            </p>
          </div>
          <div className="code-frame p-6 font-mono text-[13px] leading-loose md:p-8">
            <div className="text-faint"># layer 1 — free, before any prompt</div>
            <div>
              <span className="text-frost">well_formed</span>
              <span className="text-dim">(mask, n)</span>
            </div>
            <div className="mt-4 text-faint"># layer 2 — the validator re-runs both passes</div>
            <div>
              <span className="text-frost">run_nondet_unsafe</span>
              <span className="text-dim">(leader_fn, validator_fn)</span>
            </div>
            <div className="mt-6 space-y-2 border-t border-line pt-5">
              {lines.map((l) => (
                <div key={l.k} className="flex flex-wrap items-baseline gap-x-3">
                  <span className="text-ink">{l.k}</span>
                  <span className="text-volt">{l.v}</span>
                  <span className="text-faint">— {l.note}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
