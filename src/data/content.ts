// All content for the site. The numbers here mirror contracts/meridian.py.

export const DEPLOYMENT = {
  network: "studionet",
  address: "0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0",
  short: "0x947D…8Fd0",
  explorer:
    "https://explorer-studio.genlayer.com/address/0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0",
  verifyCmd: "python scripts/verify_deployment.py",
};

export const BUDGETS = [
  { item: "conditions per gate", value: "10", protects: "the prompt the whole network pays to run" },
  { item: "chars per condition / title", value: "90 / 96", protects: "prompt size" },
  { item: "chars per filing", value: "24 – 720", protects: "prompt size, spam" },
  { item: "filing rows per gate, struck included", value: "48", protects: "strike(), reroll, listings" },
  { item: "final slots of a gate", value: "12, principals only", protects: "the principals can never be filled out" },
  { item: "filings per keeper per gate", value: "6", protects: "one keeper cannot spend the pool" },
  { item: "filings per operator per gate", value: "16", protects: "the operator cannot stall its own gate" },
  { item: "active keepers per gate", value: "12", protects: "authority surface" },
  { item: "keeper rows per gate, relieved included", value: "24", protects: "every keeper walk" },
];

export const PERMISSIONS = [
  { call: "open_gate()", who: "anyone — caller becomes the curator", note: "freezes conditions, bar, operator" },
  { call: "file()", who: "curator · operator · active keeper", note: "each inside its own budget" },
  { call: "judge()", who: "anyone, deliberately", note: "an audit can only reach the mask the filing implies" },
  { call: "strike()", who: "curator alone", note: "the only way down — row kept, marked, recomputed" },
  { call: "empower() / relieve()", who: "curator alone", note: "keep the row and its spent allowance" },
  { call: "seal()", who: "curator alone", note: "freezes standing upward; a strike still lowers it" },
];

export const RULES = [
  {
    n: "01",
    title: "Frozen yardstick",
    body: "Conditions, the bar and the operator's address are set at open_gate() and can never be edited. A gate that could be edited later would let whoever wants the answer add the condition a filing happens to meet.",
  },
  {
    n: "02",
    title: "Bits, never verdicts",
    body: "The model answers one digit per condition — twice, in both presentation orders. A bit stands only if both passes raised it. Position bias lands on the conservative value, and nothing stores how unsure the model was.",
  },
  {
    n: "03",
    title: "Exact agreement",
    body: "Nodes must produce the identical whole mask. Two nodes agreeing that “something was demonstrated” while naming different rows have agreed about nothing worth recording. No tolerance, on any bit.",
  },
  {
    n: "04",
    title: "One way, one exception",
    body: "Standing is the union of every counted mask — it cannot fall on its own. Only the curator striking a filing lowers it: publicly, the row kept and marked, the union recomputed from what remains.",
  },
  {
    n: "05",
    title: "No lock-outs",
    body: "Every write is bound to an address. Every chain is capped, every role spends only its own allowance, and the last twelve slots of a gate are reserved for its principals.",
  },
];

export const API_WRITES = [
  { sig: "open_gate(title, clauses, bar, operator)", effect: "Freezes the yardstick. Caller is curator; operator ≠ curator." },
  { sig: "file(gate_id, text)", effect: "Appends a linked filing row. 24–720 chars after cleaning." },
  { sig: "judge(filing_id)", effect: "The audit. Two prompts, both orders; consensus on the whole mask." },
  { sig: "strike(filing_id)", effect: "Curator only. Mark the row; recompute the union. The only way down." },
  { sig: "empower(gate_id, who)", effect: "Curator only. Create or reactivate a keeper row (allowance kept)." },
  { sig: "relieve(gate_id, who)", effect: "Curator only. Deactivate; filings stay, naming their author." },
  { sig: "seal(gate_id)", effect: "Curator only, permanent. Audits still record; nothing new counts." },
];

export const API_READS = [
  { sig: "gate_count() / filing_count()", effect: "Totals." },
  { sig: "attained(gate_id)", effect: "n_standing ≥ bar. One line, for another contract." },
  { sig: "attained_for(gate_id, who)", effect: "Attained AND who is the operator — the payout gate." },
  { sig: "sealed(gate_id)", effect: "Is the standing frozen upward?" },
  { sig: "holding(gate_id, clause)", effect: "One condition's current standing." },
  { sig: "curator_of / operator_of", effect: "The two principals, as addresses." },
  { sig: "may_file(gate_id, who)", effect: "Asks the same helper file() asks, in the same order." },
  { sig: "keepers_of(gate_id)", effect: "Every keeper row, relieved ones too, with spent allowances." },
  { sig: "clauses_of(gate_id)", effect: "The frozen catalogue, each condition with its standing." },
  { sig: "standing_of(gate_id)", effect: "The mask, the counters, the bar — everything that produced it." },
  { sig: "filing(filing_id)", effect: "One row; why flagged leader-supplied, never consensus." },
  { sig: "filings_of(gate_id)", effect: "Every linked row; rebuild the union from counted && !struck." },
];

export const REPO = [
  { path: "contracts/meridian.py", kind: "submission", desc: "The Intelligent Contract. The only file a deployment needs." },
  { path: "tests/glsim.py", kind: "infra", desc: "GenVM stand-in: fake genlayer module, chain, scripted model, riggable wire." },
  { path: "tests/test_schema.py", kind: "suite", desc: "Studio-schema preflight: kills \u201cCould not load contract schema\u201d offline." },
  { path: "tests/test_logic.py", kind: "suite", desc: "Pure helpers: masks, the AND fold, validator layers, guards, prompt shape." },
  { path: "tests/test_e2e.py", kind: "suite", desc: "Full lifecycle, permissions, budgets, position bias, a lying leader." },
  { path: "tests/test_runbook.py", kind: "suite", desc: "Replays docs/QUICKSTART.md and asserts every number it prints." },
  { path: "tests/test_integration.py", kind: "opt-in", desc: "Live network via genlayer-test, only with GENLAYER_STUDIO=1." },
  { path: "samples/gate_tranche_two.json", kind: "sample", desc: "A gate definition you can open as-is." },
  { path: "samples/filings.json", kind: "sample", desc: "Four filings with the mask each should earn." },
  { path: "samples/demo.py", kind: "sample", desc: "Executable tour of a full lifecycle, offline, in a second." },
  { path: "docs/SPEC.md", kind: "doc", desc: "The full specification: state model, consensus, API, threat model." },
  { path: "docs/CONSENSUS.md", kind: "doc", desc: "The agreement rule, argued: two passes, exact equality, no flags." },
  { path: "docs/QUICKSTART.md", kind: "doc", desc: "Zero to a judged filing in five minutes." },
  { path: "docs/TESTING.md", kind: "doc", desc: "How the offline suites work, and the opt-in live one." },
  { path: "docs/STUDIO.md", kind: "doc", desc: "run-debug deploys: the schema-error cause table and 60-second preflight." },
  { path: "docs/DEPLOY.md", kind: "doc", desc: "Studio, CLI, and the checks to run before calling it done." },
  { path: "deployments/studionet.json", kind: "deployment", desc: "The live deployment record: address, network, explorer, verify steps." },
  { path: "scripts/verify_deployment.py", kind: "tool", desc: "On-chain source byte-for-byte against the local file, plus preflight." },
  { path: "scripts/pack_submission.sh", kind: "tool", desc: "Builds ./submission with exactly the contract bundle — no frontend." },
  { path: "SUBMISSION.md", kind: "doc", desc: "The submission contract: what to submit, how to verify it." },
];

export const QUICKSTART = [
  { cmd: "pip install -r requirements.txt", out: "# just pytest — the offline suites need nothing else" },
  { cmd: "pytest tests/test_schema.py -q", out: "# schema preflight — Studio's “Could not load contract schema” has no causes left" },
  { cmd: "pytest tests/ -q", out: ".................. 90+ passed in a second — no Studio, no network" },
  { cmd: "python samples/demo.py", out: "# a full lifecycle, narrated: open → filings → audits → strike → rebuild" },
  { cmd: "python scripts/verify_deployment.py", out: "# on-chain source == contracts/meridian.py, byte-for-byte — or it fails loudly" },
  { cmd: "GENLAYER_STUDIO=1 MERIDIAN_ADDRESS=0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0 gltest --network studionet tests/test_integration.py", out: "# read-only smoke against the live studionet deployment" },
];

export const THREATS = [
  ["yardstick rewritten after evidence", "frozen at open_gate(); no edit path exists"],
  ["model drift between runs", "one filing, one digit per condition, twice; exact consensus"],
  ["position bias", "both orders asked; a bit stands only if both raise it"],
  ["stored confidence", "uncertainty enters the value and only the value"],
  ["a quiet downgrade", "audits only add bits; the only way down is public"],
  ["prompt injection", "brackets neutralised at the boundary; blocks framed as data"],
  ["echoed example answer", "placeholders d0|d1 parse to unusable, never to bits"],
  ["keeper lock-out", "12-slot principal reserve + per-role allowances"],
  ["payout to the wrong team", "attained_for() binds the outcome to the operator"],
  ["unbounded walks", "every chain capped; no global scans"],
];
