# Meridian - Specification

The contract in one sentence: **filings are audited one at a time against
conditions frozen before any filing existed; the standing is the union of
what they demonstrated; nobody declares the milestone met - the contract
counts.**

---

## 1. Purpose

A grant curator and a grant operator disagree about exactly one thing at
payout time: has the milestone been met? Meridian removes that disagreement
from the negotiation by freezing the yardstick up front and auditing each
piece of evidence against it, separately, with a record that cannot be
rewritten quietly.

It is a **primitive**, not a workflow. It does not move money, it does not
know what a grant is, and it never asks a model "has the team done well".

## 2. Vocabulary

| Term        | Meaning                                                        |
| ----------- | -------------------------------------------------------------- |
| gate        | one milestone: frozen conditions + a bar + two principals      |
| clause      | one frozen condition inside a gate (max 10)                    |
| bar         | how many conditions must stand for the gate to be attained     |
| curator     | the address that opened the gate; owns it; the only way down   |
| operator    | the team being paid; bound to an address at open, forever      |
| keeper      | an address the curator empowered to file; may not govern       |
| filing      | one piece of evidence, one row, audited once                   |
| standing    | union of every counted, unstruck mask                          |
| mask        | one digit per condition, pipe joined: `0|1|1|0`                |
| void        | a filing that was audited and demonstrated nothing             |
| seal        | curator's permanent freeze of the standing **upward**          |
| strike      | curator's removal of one filing from the union; the only way down |

## 3. State model

GenVM forbids a collection inside a storage dataclass, so every child row
lives in one flat array carrying its parent id, and rows of one parent are
**linked**: each row stores the index of the next row with the same parent,
and the parent stores its first and last. Walking one gate costs that gate's
rows and nothing else on the contract. Clauses are appended in one call at
`open_gate()`, so they are contiguous - a range read suffices.

```
gates:        DynArray[Gate]     gate i owns its first_filing -> ... -> last_filing
clauses:      DynArray[Clause]   gate i owns clauses[first_clause .. first_clause+n_clauses)
filings:      DynArray[Filing]
keeper_rows:  DynArray[Keeper]
```

`Gate` holds: curator, operator, title, bar, sealed, the clause range, the
standing mask and its weight, the filing chain head/tail/count, the
judged/void/struck counters, the operator's spent allowance, and the keeper
chain head/tail/count.

`Filing` holds: gate, author address, text, timestamp, judged, mask, void,
counted, struck, the leader-supplied `why` (never consensus), and the chain
link.

## 4. The audit (consensus) in detail

`judge(filing_id)` is the only non-deterministic write. See
[CONSENSUS.md](CONSENSUS.md) for *why*; mechanically:

1. **Leader** builds two prompts - conditions in frozen order, and reversed
   and renumbered - from **locals** (storage is unread before the block,
   never inside it). Each prompt demands a JSON object whose `mask` is one
   digit per numbered condition. A non-object answer is `unusable`, not a
   crash. The reversed mask is unreversed, and the two masks are folded
   conservatively: a bit stands only if **both** passes raised it. An
   unusable pass is all zeros. The block returns a flat dict of plain
   strings: `{mask, because}`.
2. **Validator, layer 1 (free):** the leader's payload must be a Return, a
   dict, and its mask must be structurally sound - right length, nothing but
   bits. Checked against storage the validator already holds, before any
   prompt is spent.
3. **Validator, layer 2 (exact):** the validator runs both passes itself.
   The masks must be **identical**. `run_nondet_unsafe` carries this.
4. **Deterministic half:** the contract parses the agreed mask itself (a
   defence in depth), marks the row judged, records `void` when no bits
   stand, and - only while the gate is unsealed - unions the mask into the
   standing and marks the row `counted`.

Nothing stores how unsure the model was: the `because` string is
leader-supplied, scrubbed, and never compared.

## 5. Writes

| Method | Caller | Effect |
| ------ | ------ | ------ |
| `open_gate(title, clauses, bar, operator)` | anyone | freezes everything; caller is curator |
| `file(gate_id, text)` | curator, operator, or an active keeper (each within its budget) | appends a linked row |
| `judge(filing_id)` | **anyone, deliberately** | the audit; consensus |
| `strike(filing_id)` | curator only | mark + recompute; the only way down |
| `empower(gate_id, who)` | curator only | create/reactivate a keeper row |
| `relieve(gate_id, who)` | curator only | deactivate a keeper row; filings stay |
| `seal(gate_id)` | curator only | permanent; audits still record, nothing new counts |

`judge()` is open on purpose: auditing adds no text, can reach only the mask
the filing already implies, and an operator *wants* their filing audited.

### Refusals are designed

Every misuse above raises a `UserError` naming the rule: `no such gate`,
`the bar must be between 1 and the number of conditions`,
`a filing needs substance: at least 24 characters`, `already judged`,
`struck filings are not judged`, `only the curator may strike a filing`, ...
A refusal is never a crash and never a silent write.

## 6. Budgets - so no party can lock another out

| Budget | Value | Protects |
| ------ | ----- | -------- |
| conditions per gate | 10 | the prompt the whole network pays to run |
| characters per condition / title | 90 / 96 | prompt size |
| characters per filing | 24 - 720 | prompt size |
| filing rows per gate, struck included | 48 | `strike()`, `_reroll()`, `filings_of()` |
| the last slots of a gate | 12, principals only | the principals can never be filled out by keepers |
| filings per keeper per gate | 6 | one keeper cannot spend the pool |
| filings per operator per gate | 16 | the operator cannot stall its own gate |
| active keepers per gate | 12 | authority surface |
| keeper rows per gate, relieved included | 24 | every keeper walk |

A relieve-and-re-empower keeps the row and its spent allowance, so neither
refills anything. Recomputed union (`_reroll`) walks at most 48 rows; every
keeper walk at most 24.

## 7. Reads

| View | Returns |
| ---- | ------- |
| `gate_count()` / `filing_count()` | totals |
| `attained(gate_id)` | `n_standing >= bar` |
| `attained_for(gate_id, who)` | attained **and** `who` is the operator (case-insensitive) - the payout gate |
| `sealed(gate_id)` | bool |
| `holding(gate_id, clause)` | one condition's standing |
| `curator_of` / `operator_of` | the principals |
| `may_file(gate_id, who)` | asks the same helper `file()` asks |
| `keepers_of(gate_id)` | every keeper row, relieved ones too |
| `clauses_of(gate_id)` | the frozen catalogue, each with its standing |
| `standing_of(gate_id)` | the standing with every counter that produced it |
| `filing(filing_id)` | one row; `why` flagged as leader-supplied |
| `filings_of(gate_id)` | every linked row; a reader can rebuild the union from `counted && !struck` alone |

`attained()` and `holding()` return `False` rather than raising for a gate
that has earned nothing yet, so a calling contract has one branch to handle,
not two. Every other read raises `UserError` on a bad id, including negative
ids.

## 8. Using it from another contract

```python
@gl.contract_interface
class Meridian:
    class View:
        def attained(self, gate_id: u256) -> bool: ...
        def attained_for(self, gate_id: u256, who: str) -> bool: ...
        def holding(self, gate_id: u256, clause: u256) -> bool: ...
        def operator_of(self, gate_id: u256) -> str: ...

m = Meridian(MERIDIAN_ADDR).view()

# Gate the tranche, bound to the payee - never to a label anybody could type.
if m.attained_for(gate_id, str(payee)):
    self._release(payee)

# Or gate on one specific condition ("zero critical findings", specifically).
if m.holding(gate_id, 0):
    self._mark_audited()
```

On chain, every address a view returns is an EIP-55 checksummed string;
compare case-insensitively.

## 9. Threat model, and what answers it

| Threat | Answer |
| ------ | ------ |
| yardstick rewritten after evidence arrives | frozen at `open_gate()`; there is no edit path |
| model drifts between runs | one filing, one digit per condition, twice; exact-bit consensus |
| position bias | both orders asked; a bit stands only if both raise it; disagreement lands on 0 |
| "it was 70% sure" stored as fact | uncertainty enters the value and only the value; nothing else to compare |
| a judge quietly lowers a standing | impossible: auditing only adds bits; the only way down is the curator's public `strike` |
| a reputation-replaying attack on `judge` | `already judged` |
| prompt injection via filing text | `guard()` neutralises `<`, `>`, `[`, `]` at the prompt boundary; blocks framed as DATA; storage keeps the raw text |
| model echoes the example answer | the example uses `d0|d1|...` placeholders, which parse to unusable |
| keeper fills the gate and locks the principals out | the 12-slot principal reserve |
| one keeper eats the pool | the 6-per-keeper allowance, kept across relieve/empower |
| operator floods its own gate | the 16-per-operator allowance |
| a stranger files for the operator | every write is address-bound; only curator/operator/keepers file |
| a standing paid twice to different addresses | `attained_for()` binds the outcome to the operator's address |
| an unbounded walk DoS | every chain is capped; no global scans |

## 10. What the contract deliberately does not do

* No web access. Every input is text a caller supplies, removing an entire
  class of deployment failure.
* No scoring. A mask is set membership, not quality.
* No appeal protocol. A strike is the curator's act; a gate that needs
  adjudication needs a court, and this is a yardstick.
* No edits, no deletes. Rows are marked, never erased.
