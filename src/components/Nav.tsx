import { useEffect, useState } from "react";
import { GitBranch, Boxes } from "lucide-react";
import { DEPLOYMENT } from "../data/content";
import { cn } from "../utils/cn";

const LINKS = [
  ["Protocol", "#protocol"],
  ["Audit", "#audit"],
  ["Standing", "#standing"],
  ["Permissions", "#permissions"],
  ["API", "#api"],
  ["Repository", "#repo"],
  ["Quickstart", "#quickstart"],
] as const;

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 border-b transition-all duration-500",
        scrolled ? "border-line bg-void/85 backdrop-blur-md" : "border-transparent"
      )}
    >
      <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between px-5 md:px-10">
        <a href="#top" className="group flex items-center gap-2.5">
          <span className="grid h-7 w-7 place-items-center border border-volt/60 bg-volt/10">
            <Boxes className="h-3.5 w-3.5 text-volt" strokeWidth={1.8} />
          </span>
          <span className="font-mono text-sm font-semibold tracking-[0.22em] text-ink">
            MERIDIAN
          </span>
          <span className="hidden font-mono text-[10px] tracking-widest text-faint sm:inline">
            v1.0 · studionet-ready
          </span>
        </a>
        <nav className="hidden items-center gap-6 lg:flex">
          {LINKS.map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="font-mono text-[11px] uppercase tracking-[0.18em] text-dim transition-colors hover:text-volt"
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <a
            href={DEPLOYMENT.explorer}
            target="_blank"
            rel="noreferrer"
            className="hidden items-center gap-2 border border-volt/40 bg-volt/5 px-3 py-1.5 transition-colors hover:border-volt/70 sm:flex"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-volt" />
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
              live · <span className="text-volt">{DEPLOYMENT.short}</span>
            </span>
          </a>
          <div className="flex items-center gap-2 border border-line bg-panel px-3 py-1.5">
            <GitBranch className="h-3.5 w-3.5 text-volt" strokeWidth={1.8} />
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">
              submit = <span className="text-volt">contracts/meridian.py</span>
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
