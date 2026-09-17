# Deploying Meridian

The deployment artifact is one file: **`contracts/meridian.py`**. That file
is the submission. This page gets you from the file to a live address, and
ends with the checks to run before you call it done.

> **A reference deployment already exists on studionet:**
> [`0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0`](https://explorer-studio.genlayer.com/address/0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0)
> (recorded in `deployments/studionet.json`, deployed via the Studio
> run-debug flow below). Deploy your own only if you want to be the curator
> of new gates; otherwise read and test against the published one.
> To add your own deployment to the record, drop a JSON file next to
> `deployments/studionet.json` with the same shape.

## 0. Before anything external

```bash
pip install -r requirements.txt
pytest tests/ -q            # the whole offline suite must pass
python samples/demo.py      # the lifecycle, end to end, on your machine
```

## 1. GenLayer Studio (the visual path)

> **Hitting "Could not load contract schema"?** Read [STUDIO.md](STUDIO.md)
> first — it is the dedicated guide for the Studio run-debug panel: the
> cause table, and the offline preflight (`pytest tests/test_schema.py -q`)
> that proves the file clean before you paste it.

1. Open https://studio.genlayer.com/run-debug (Studio's local simulator)
   or connect to **studionet**.
2. Create a new contract file and paste the contents of
   `contracts/meridian.py` — starting with the first-line
   `# { "Depends": "py-genlayer:test" }` header as the very first byte; the
   runtime selects its executor from it. (`test` pins to whatever runner the
   network you deploy to ships today; an unknown hash pin is ignored with a
   warning, not an error.)
3. **Deploy.** The constructor exists and takes no arguments — GenVM's
   schema step refuses classes with no `__init__` at all, so the panel
   should show an empty constructor form and a full methods list.
4. **Check the methods panel.** Seven writes and twelve reads should be
   listed. An empty or missing panel means the schema family — the table in
   [STUDIO.md](STUDIO.md) names every cause; never fix by editing blind.
5. In the *Write methods* panel, as your deployer account:

   ```
   open_gate(
     "Tranche Two",
     "alpha audit report published with zero critical findings|beta testnet live with five hundred weekly users|gamma documentation covering every public endpoint|delta mainnet deployed and verified on the explorer",
     3,
     "<operator 0x address - not yours>"
   )
   ```

   The caller becomes the curator. The operator must be a different address:
   nobody attests their own milestone.

6. Read back with `standing_of(0)` - you want
   `standing: "0|0|0|0"`, `bar: 3`, `clauses: 4`.

## 2. CLI (genlayer-py)

```bash
pip install genlayer-py
genlayer deploy --contract contracts/meridian.py --network studionet
```

Then write-call with the same arguments as above. The pipe-joined string is
one argument; quote it once.

## 3. The lifecycle to exercise once deployed

Follow [QUICKSTART.md](QUICKSTART.md) - it is written for exactly this
deployment, and `tests/test_runbook.py` asserts the same numbers offline:

```python
file(0, "...")                       # as the operator
judge(0)                             # as anyone - watch the audit land
attained_for(0, "<operator>")        # what a payout contract would gate on
```

Expect your first `judge()` to take a while: two prompts on the leader, two
on every validator, then consensus.

## 4. What to check before you call it done

| # | Check | How |
| - | ----- | --- |
| 1 | `standing_of(0)["standing"] == "0|0|0|0"` | view call |
| 2 | `curator_of(0)` is your address, `operator_of(0)` is theirs | view call |
| 3 | `may_file(0, "<a stranger>") == false` | view call |
| 4 | The deployed source matches `contracts/meridian.py` byte-for-byte | diff the Studio source view against the file |
| 5 | `GENLAYER_STUDIO=1 gltest --network studionet tests/test_integration.py` passes | optional but recommended |

Check 4 is the one people skip and regret: paste-from-clipboard deployment
makes "what I reviewed" and "what is live" two different files. Verify.

## 5. Operating notes

* **There is no admin key beyond the curator address of each gate.** Lose
  the curator key and the gate can never be struck, sealed, or re-staffed;
  the standing can then only go up. Treat that as a property, not a bug.
* `judge()` is open by design. If you want audits to happen on your
  schedule, schedule calls to it - but anyone else may too, and that hurts
  no one: an audit can reach only the mask the filing already implies.
* Sealing is forever. Seal when the funding decision is made, not before:
  after sealing, audits are still recorded on their rows but no longer move
  the standing upward. Strikes still move it down.
