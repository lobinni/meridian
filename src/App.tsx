import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { Problem, Rules, ConsensusBand } from "./components/Sections";
import { AuditLab } from "./components/AuditLab";
import { Permissions, Api, Repo, Quickstart, Footer } from "./components/Reference";

const MARQUEE_ITEMS = [
  "frozen yardstick",
  "one digit per condition",
  "asked twice, both orders",
  "exact on the whole mask",
  "union only moves up",
  "the strike is the only way down",
  "every write bound to an address",
  "budgets capped, principals reserved",
  "uncertainty lives in the value",
];

function Marquee() {
  const row = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS];
  return (
    <div className="overflow-hidden border-b border-line bg-volt py-2.5">
      <div className="flex w-max animate-marquee gap-0">
        {row.map((item, i) => (
          <span
            key={i}
            className="flex items-center gap-6 whitespace-nowrap px-6 font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-void"
          >
            {item}
            <span className="text-void/50">//</span>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-void text-ink">
      <Nav />
      <main>
        <Hero />
        <Marquee />
        <Problem />
        <Rules />
        <AuditLab />
        <ConsensusBand />
        <Permissions />
        <Api />
        <Repo />
        <Quickstart />
      </main>
      <Footer />
    </div>
  );
}
