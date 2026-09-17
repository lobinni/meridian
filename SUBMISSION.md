# Submission

**Meridian — milestone attestation rails for grants.** A pure GenLayer
Intelligent Contracts project. This file is the submission contract: what
you need, where it lives, and how to verify it without trusting us.

## The artifact

| | |
|---|---|
| Deployable artifact | **`contracts/meridian.py`** — the entire contract, one file |
| Live deployment | [`0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0`](https://explorer-studio.genlayer.com/address/0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0) on **studionet** |
| Runner pin | `py-genlayer:test` (line 1 of the contract file) |
| Constructor | none — zero arguments, storage zero-initializes |

Everything else in this repository exists so a reviewer can run, probe and
trust that one file. **Only `contracts/meridian.py` is submitted.**

## What is in the submission bundle (and what is not)

```
SUBMIT = contracts/ tests/ docs/ samples/ deployments/ scripts/verify_deployment.py
         README.md  SUBMISSION.md  requirements.txt  pytest.ini

NOT   = src/ index.html package.json vite/tsconfig files node_modules/
        (a documentation/showcase site for the contract - presentation only,
        excluded by scripts/pack_submission.sh)
```

Rebuild the bundle yourself:

```bash
bash scripts/pack_submission.sh   # writes ./submission/, prints the tree
```

## Verify the deployment - 90 seconds, no trust required

```bash
# 1. offline: the contract file is schema-clean and behaves as specified
pip install -r requirements.txt
pytest tests/ -q

# 2. on-chain: the deployed source is byte-for-byte the local file
python scripts/verify_deployment.py

# 3. live: read-only smoke test against the deployed address
pip install genlayer-test
GENLAYER_STUDIO=1 \
MERIDIAN_ADDRESS=0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0 \
gltest --network studionet tests/test_integration.py
```

Step 2 is the one that matters for judging: it proves the review you are
about to do applies to the bytes that are actually live. If the RPC refuses
to serve the source (Studio's method set changes between releases), the
script tells you how to paste the explorer's source view instead — the
comparison still runs, and it still fails loudly on any difference.

## Read it in five minutes

1. `contracts/meridian.py` docstring — what it is, why consensus is a
   bitmask, why the standing can only move up.
2. `docs/CONSENSUS.md` — the agreement rule, argued.
3. `docs/QUICKSTART.md` — the lifecycle `tests/test_runbook.py` replays
   and asserts.
4. `samples/demo.py` — run it (`python samples/demo.py`) and watch the
   whole thing happen offline, narrated.
