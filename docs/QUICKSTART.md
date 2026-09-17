# Quickstart

From zero to a judged filing in five minutes. Everything below runs
**offline** on the simulator in `tests/glsim.py`; the exact same calls work
against a deployment, with the same arguments, in the same order
(see [DEPLOY.md](DEPLOY.md)).

```bash
pip install -r requirements.txt
python samples/demo.py        # this walkthrough, executable
pytest tests/test_runbook.py  # the same walkthrough, as an assertion
```

## 1. Open the gate

The curator deploys the contract and opens a gate: four conditions, a bar of
three, the operator bound to an address. The order of the conditions is the
order every mask reads in, forever.

```python
open_gate(
    "Tranche Two",
    "alpha audit report published with zero critical findings"
    "|beta testnet live with five hundred weekly users"
    "|gamma documentation covering every public endpoint"
    "|delta mainnet deployed and verified on the explorer",
    3,
    "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
)
```

`standing_of(0)` now reads:

```json
{"clauses": 4, "bar": 3, "standing": "0|0|0|0", "n_standing": 0, "attained": false}
```

## 2. File a narrative. Watch it earn nothing.

The operator files a report that *names* the work without showing it:
enrolled to begin the alpha audit, beta launch scheduled next quarter.

```python
file(0, "Quarterly report. ... enrolled to begin the alpha audit in October ...")
judge(0)      # anyone may call this
```

```
0|0|0|0  ->  void
```

Enrollment is not a published audit; a schedule is not a live testnet. A
document that mentions a condition is not evidence of it - that refusal is
the reason the contract exists.

## 3. File the artefacts. The gate attains.

```python
file(0, "... the audit report is published (link), zero critical findings;
          the testnet shows 812 weekly users; every public endpoint is
          documented ...")
judge(1)
```

```
1|1|1|0  ->  standing 1|1|1|0, attained = true
attained_for(0, operator) = true        <- what a payout contract gates on
```

## 4. The only way down

The audit's link turns out to be a staging environment. The curator strikes
the filing:

```python
strike(1)
```

```
standing 1|1|1|0 -> 0|0|0|0, attained = false
filing(1): {"struck": true, "mask": "1|1|1|0"}   <- the row stays, marked
```

The record of what was claimed, judged and struck never disappears.

## 5. A keeper rebuilds it - differently

```python
empower(0, "0xcccccccccccccccccccccccccccccccccccccccc")
file(0, "... beta telemetry, delta mainnet verified ...")     # by the keeper
file(0, "... gamma documentation complete ...")               # by the keeper
judge(2); judge(3)
```

```
0|1|0|1 + 0|0|1|0  ->  standing 0|1|1|1, attained = true
```

Attained again - on a **different three conditions** than before the strike.
The union only ever reflects what is currently unstruck and counted.

## 6. Contain the keeper

```python
relieve(0, "0xcccc...cccc")
```

```
keepers_of(0) -> {"who": "0xcccc...", "active": false, "filed": 2}
may_file(0, keeper) -> false
```

The row and its spending are kept, so relieving and re-empowering never
refills an allowance. Filings the keeper already made stay on the record,
naming its address; the recourse for one the curator disowns is `strike()`.

## Final state (exactly what `test_runbook.py` asserts)

```json
{
  "title": "Tranche Two", "sealed": false,
  "clauses": 4, "bar": 3,
  "standing": "0|1|1|1", "n_standing": 3, "attained": true,
  "filings": 4, "judged": 4, "void": 1, "struck": 1
}
```

Seventeen write transactions, every read above available as a view call.
