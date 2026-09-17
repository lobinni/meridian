# Deploying on GenLayer Studio (run-debug) without schema errors

Studio: https://studio.genlayer.com/run-debug

"**Could not load contract schema**" is not one error — it is a family of
them, and Studio reports the whole family the same way: deployment never
materializes and the methods panel stays empty. This page lists every cause
we know, how `contracts/meridian.py` pre-empts it, and the 60-second
preflight that proves it before you ever open the browser.

## The 60-second preflight (do this first)

```bash
pip install -r requirements.txt
pytest tests/test_schema.py -q    # the schema preflight suite
pytest tests/ -q                  # the full offline suite
```

`tests/test_schema.py` asserts, from the AST of the file you are about to
paste: the runner header on line 1, exactly one `gl.Contract` subclass, an
explicit constructor with ABI-legal parameters, fully-annotated public
methods, legal fully-specialized storage fields, `@allow_storage` on every
storage dataclass, no collections inside storage dataclasses, no
`sender_address` in `__init__`, and no imports GenVM doesn't ship. If this
suite passes and Studio still refuses the file, the problem is the network,
not the contract.

> Field note, from a real deploy: the constructor check exists because this
> exact contract once failed schema extraction on studio.genlayer.com with
> `TypeError: ('__init__ is absent', …)` — the one schema-killer that never
> shows up in documentation. It is the loudest assertion in the preflight
> now.

## What actually causes the error, and what Meridian does about it

| # | Cause seen in the wild | What this contract does |
|---|------------------------|-------------------------|
| 1 | **Storage dataclass without `@allow_storage`** — the runtime refuses the type and Studio's schema step dies with an empty methods panel | All four rows (`Clause`, `Gate`, `Filing`, `Keeper`) carry `@allow_storage` + `@dataclass`, and `test_every_storage_dataclass_carries_allow_storage` refuses to let one slip |
| 2 | **Missing or malformed runner header** — Studio needs line 1 to select the executor. A hash pin the running GenVM doesn't know is *ignored with a warning* (`runner comment does not start with version, using default`) | Line 1 is `# { "Depends": "py-genlayer:test" }`, which selects the runner the Studio you are deploying to actually ships; asserted byte-for-byte by the preflight |
| 3 | **`int` (or `float`, `list`, `dict`) as a storage field** — TypeError at schema time | Storage is `str`, `bool`, `u256`, `Address` and fully-specialized `DynArray[...]` of storage dataclasses only |
| 4 | **Bare `TreeMap` / `DynArray` without specialization** | Every collection annotation carries `[K, V]`/`[T]`; the preflight parses the AST to prove it |
| 5 | **A collection inside a storage dataclass** — forbidden by GenVM (it would need `gl.storage.inmem_allocate` gymnastics) | Flat arrays linked by parent id + `next` index; `test_no_collection_inside_a_storage_dataclass` keeps it that way |
| 6a | **No `__init__` at all** — a *confirmed* deploy-killer: GenVM's schema step raises `TypeError: ('__init__ is absent', …)` (observed on studio.genlayer.com) | The contract declares an explicit no-argument `__init__`; storage zero-initializes, so the body is `pass`, and `test_schema_generator_needs_a_ctor` guards the regression forever |
| 6b | **`gl.message.sender_address` inside `__init__`** — deployment-time failure | The constructor takes no arguments and reads no caller; curator is bound at the first write (`open_gate`), operator is passed as a parameter |
| 7 | **Un-annotated public methods or exotic parameter types** — the ABI can't be built | Every public method is fully annotated with ABI-legal types (`str`, `bool`, `u256`, `Address`→`str` params, `dict` views, `None` writes); asserted per method |
| 8 | **`typing.Any` anywhere visible** | Removed entirely; the preflight grep-refuses its return |
| 9 | **More than one `gl.Contract` subclass in the file** | Exactly one, asserted |
| 10 | **Imports GenVM doesn't ship** | `genlayer` and `dataclasses` only |
| 11 | Returning storage proxies instead of plain values from views | Views build fresh dicts of `str()`/`int()`/`bool()` leaves — nothing crosses the ABI that isn't plain |
| 12 | Instance-only state (`self.x = …` undeclared) — silently discarded, looks like "state doesn't persist" | All state is class-body annotated; `test_no_instance_only_state` refuses assignments to undeclared fields |

## Paste-deploy, step by step

1. Open https://studio.genlayer.com/run-debug (Studio's local simulator —
   no faucet needed).
2. **New file** → paste the *entire* contents of `contracts/meridian.py`,
   starting with the `# { "Depends": … }` line. The header must remain the
   first byte of the file.
3. **Deploy.** The constructor takes no arguments, so there is nothing to
   fill in — if Studio asks for constructor arguments, you are not looking
   at this file.
4. **Verify the methods panel.** You should see seven writes
   (`open_gate`, `file`, `judge`, `strike`, `empower`, `relieve`, `seal`)
   and twelve reads. A missing or empty panel *is* the schema family — fix
   the cause in the table, never by editing live code blindly.
5. Smoke-test in order (each write waits for finalization):

   ```
   open_gate("Tranche Two",
             "alpha audit published zero criticals|beta testnet 500 weekly users|gamma docs cover every endpoint",
             2, "<another address, not yours>")
   standing_of(0)            → standing "0|0|0", bar 2, clauses 3
   may_file(0, "<random>")   → false
   file(0, "Deployment report: the beta testnet shows 812 weekly users over four weeks, dashboard link attached (beta).")
   judge(0)                  → waits on real model consensus (30–90 s)
   standing_of(0)            → condition 1 stands
   ```

6. Before calling it done, diff the source Studio shows for the deployed
   address against `contracts/meridian.py` — byte-for-byte. "What I
   reviewed" and "what is live" must be the same file.

## If the error still appears after a green preflight

* **Hard-refresh the Studio tab** and re-create the file — Studio caches
  schema state per file id, and a previously-failed paste can poison the
  cache for the same file name.
* **Check you are pasting the first byte.** A leading blank line or BOM
  before `# { "Depends": … }` makes the header invisible to the runner
  selector.
* **Do not strip comments** when "minimizing" before a paste — the header
  is a comment, and stripping it is cause #2.
* If Studio is mid-upgrade (the UI says so), schema extraction for freshly
  pasted files can fail globally; deploy something trivial (`class T(gl.Contract): …`)
  to isolate: if the trivial file also fails, wait and retry — it is not
  your contract.
* Errors that appear *after* deployment, at call time, are runtime errors,
  not schema errors: they show as reverted/failed transactions. Those are
  the domain of the `UserError` refusals this contract raises by design,
  and of [DEPLOY.md](DEPLOY.md)'s operating notes.
