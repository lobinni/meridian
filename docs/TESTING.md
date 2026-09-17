# Testing

```
pip install -r requirements.txt      # pytest, nothing else
pytest tests/ -q                     # offline, no Studio, no network
```

## How the offline suites work

`tests/glsim.py` is a small GenVM stand-in, about 250 lines, with four jobs:

1. **A fake `genlayer` module.** `gl.Contract`, `@gl.public.write/view`,
   `gl.vm.UserError/Return/run_nondet_unsafe`, `gl.nondet.exec_prompt`,
   `gl.message.sender_address`, `Address`, `u256`, `DynArray`, `TreeMap` -
   enough for `load_module()` to `exec` the untouched contract source and
   instantiate it. Storage arrays auto-initialise from annotations, the way
   the real runtime does it.
2. **A chain.** `Chain.tx(fn, *args, sender=...)` sets the caller and ticks
   the clock (`gl.message_raw["datetime"]`), then invokes the method.
   `UserError` propagates like a revert, so tests assert refusals directly.
3. **A scripted model.** Every `exec_prompt` is routed to a function you
   install. `glsim.keyword_model` reads `proven(<first word of a
   condition>)` markers out of the filing text, so a bit is tied to the
   *content* of a condition, not its position - which is exactly what makes
   the reversed pass meaningful in a test. Suites that need a lying or
   position-leaning model install their own callable; `test_e2e.py` shows
   `dual_model`, which answers the forward pass and the reversed pass
   differently and tells them apart by which condition heads the list.
4. **A riggable wire.** `chain.rig_payload({...})` hands validators a value
   `leader_fn` never produced; `chain.rig_error()` simulates a leader that
   rolled back. Without these, the defences that inspect the leader's
   payload are unreachable - and a defence you cannot exercise looks
   identical to one that is not there. No mock patching: the rig goes
   through the same `run_nondet_unsafe` entry the real network uses.

## The suites

| File | Covers |
| ---- | ------ |
| `test_schema.py` | the Studio-schema preflight: runner header, one contract class, fully-annotated ABI-legal public methods, legal storage, `@allow_storage` everywhere it belongs, no `__init__` sender trap - the offline answer to "Could not load contract schema" |
| `test_logic.py` | every pure helper: masks, the AND fold, the two validator layers, tidying, guarding, the prompt's shape, address shape |
| `test_e2e.py` | the whole contract: open/file/judge/strike/empower/relieve/seal, permissions, every budget number, gate isolation, position bias, an unusable pass, a lying leader, a rolled-back leader, a structurally broken proposal refused for free, strike math, seal semantics, `attained_for` payout binding |
| `test_runbook.py` | replays [QUICKSTART.md](QUICKSTART.md) line by line and asserts every number the doc prints - the docs are tested like the code |

For a Studio deploy, run the preflight first:

```bash
pytest tests/test_schema.py -q
```

then paste the file knowing the schema family has no members left in it
(see [STUDIO.md](STUDIO.md)).

A few tests worth reading first, because they are the design defending
itself:

* `test_a_row_marked_from_only_one_end_of_the_list_does_not_stand`
* `test_a_lying_leader_is_refused_when_masks_differ`
* `test_a_structurally_broken_proposal_dies_before_any_inference`
* `test_a_strike_after_sealing_recomputes_from_counted_masks_only`
* `test_a_relieve_and_reempower_does_not_refill_an_allowance`

## The opt-in integration suite

`tests/test_integration.py` skips unless both are true: `genlayer-test` is
installed **and** `GENLAYER_STUDIO=1` is set. That is deliberate - a reviewer
with the plugin installed should still see a clean offline run, not a wall
of connection errors. It runs in two modes.

### Mode 1 - smoke the published deployment (read-only)

```bash
pip install genlayer-test
GENLAYER_STUDIO=1 \
MERIDIAN_ADDRESS=0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0 \
gltest --network studionet tests/test_integration.py
```

With `MERIDIAN_ADDRESS` set, the suite binds the published deployment
(see `deployments/studionet.json`) instead of deploying, and only read-only
checks run: every documented view responds with its documented shape,
`attained` is always arithmetic over `n_standing` and `bar`,
`attained_for` never inherits a standing to the wrong address, and
`may_file` mirrors the write rule for strangers. Write tests are skipped
automatically - nothing is written to the shared deployment.

### Mode 2 - fresh deploy, full lifecycle

```bash
pip install genlayer-test
GENLAYER_STUDIO=1 gltest --network studionet tests/test_integration.py
```

Without `MERIDIAN_ADDRESS`, the suite deploys `contracts/meridian.py`,
opens a gate, files real prose, and calls `judge()` with real prompts
through real validators - slow by design.

Pair with `python scripts/verify_deployment.py` to prove the bytes you are
testing are the bytes you reviewed.

## The executable sample

```bash
python samples/demo.py
```

Same simulator, same contract, narrated: a full lifecycle with every mask
and counter printed, pulled from `samples/*.json`. If `demo.py` and the test
suites disagree, one of them is lying, and it is a bug either way.

## Adding a test

The fixture is one fresh deployment per test:

```python
def test_something(chain):
    from conftest import open_std, filing_for
    open_std(chain)                                   # gate 0: 4 conditions, bar 3
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=glsim.OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.holding, 0, 0) is True
```

Named senders: `glsim.CURATOR`, `glsim.OPERATOR`, `glsim.KEEPER`,
`glsim.KEEPER2`, `glsim.STRANGER` - all valid 20-byte hex addresses.
