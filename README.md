# Meridian

**Milestone attestation rails for grants.** A GenLayer Intelligent Contract
that decides whether a grant milestone has been met - by turning filings
into a bitmask against conditions frozen before any filing existed, and by
never letting the standing move anywhere but **up**, except through the one
public act that moves it down.

Nobody declares the milestone met. The contract counts.

```
The block sees ONE filing and the NUMBERED conditions, twice - forward and
reversed - and the only thing that crosses consensus is a string of ones
and zeros. Everything else is arithmetic the contract does alone.
```

## Live on studionet

| | |
|---|---|
| Address | [`0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0`](https://explorer-studio.genlayer.com/address/0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0) |
| Network | GenLayer **studionet** |
| Source | `contracts/meridian.py` (`py-genlayer:test`, zero-arg constructor) |
| Verify | `python scripts/verify_deployment.py` — byte-for-byte on-chain source check |
| Live smoke test | `GENLAYER_STUDIO=1 MERIDIAN_ADDRESS=0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0 gltest --network studionet tests/test_integration.py` (read-only) |

Deployments are recorded in [`deployments/`](deployments/studionet.json).

## Submitting

**The deployable artifact is one file: [`contracts/meridian.py`](contracts/meridian.py).**
Everything else exists so a reviewer can run the contract, probe its
defences, and trust what they deployed — and the documentation site under
`src/` is presentation only, excluded from the bundle. See
[SUBMISSION.md](SUBMISSION.md), or rebuild the bundle:

```bash
bash scripts/pack_submission.sh   # writes ./submission with exactly the contract project
```

## Repository layout

```
contracts/meridian.py     the Intelligent Contract - the entire submission
tests/
  glsim.py                a small GenVM stand-in: fake genlayer module, chain,
                          scripted model, riggable consensus wire
  test_schema.py          Studio-schema preflight: kills "Could not load
                          contract schema" offline, before you ever paste
  test_logic.py           the pure helpers the consensus rule is built from
  test_e2e.py             lifecycle, permissions, budgets, and a lying leader
  test_runbook.py         replays docs/QUICKSTART.md and asserts every number
  test_integration.py     opt-in, runs against a live network (GENLAYER_STUDIO=1)
samples/
  gate_tranche_two.json   a gate definition you can open as-is
  filings.json            four filings with the mask each one should earn
  demo.py                 an executable tour: python samples/demo.py
docs/
  SPEC.md                 the full specification
  CONSENSUS.md            why the agreement rule is the way it is
  QUICKSTART.md           from zero to a judged filing in five minutes
  TESTING.md              how the suites work and how to run them
  STUDIO.md               run-debug deploys without "Could not load schema"
  DEPLOY.md               Studio, CLI, and what to check before submitting
deployments/
  studionet.json          the live deployment record: address, network, verify steps
scripts/
  verify_deployment.py    byte-for-byte on-chain source check + static preflight
  pack_submission.sh      builds ./submission with exactly the contract bundle
SUBMISSION.md             the submission contract - what to submit, how to verify
src/ + web tooling        the documentation/showcase site - presentation only,
                          never part of a submission bundle
```

**Submitting:** the only file a deployment needs is
[`contracts/meridian.py`](contracts/meridian.py). Everything else exists so a
reviewer can run the contract, probe its defences, and trust what they
deployed.

## Quickstart

```bash
pip install -r requirements.txt   # just pytest
pytest tests/ -q                  # 80+ tests, offline, seconds

python samples/demo.py            # watch a full lifecycle end to end
```

## The five rules

1. **Frozen yardstick.** Conditions, the bar and the operator's address are
   set at `open_gate()` and can never be edited.
2. **Bits, never verdicts.** The model answers one digit per condition,
   twice, in both presentation orders. A bit stands only if **both** passes
   raised it - position bias lands on the conservative value, and nothing
   records how unsure the model was.
3. **Exact agreement.** Nodes must produce the identical whole mask. There
   is no tolerance on any bit.
4. **One way, with one exception.** Standing is the union of every counted
   mask. It cannot fall on its own; only the curator striking a filing
   (row kept, marked, recomputed) lowers it.
5. **No lock-outs.** Every write is bound to an address, every chain is
   capped, each role spends only its own allowance, and the principals keep
   a reserve no keeper can touch.

## License

MIT. Copy the agreement rule; that is what it is for.
