"""An executable tour of the contract, offline, in about a second.

    python samples/demo.py

It deploys contracts/meridian.py on the same GenVM stand-in the test suites
use (tests/glsim.py), replays a full milestone lifecycle - open, filings,
audits, the only way down, a keeper contained - and reads every value back
the way a caller on chain would: through the public views.

Nothing here touches a network or a real model. The keyword model stands in
for the LLM, reading proven(<word>) markers in the sample filings; on a live
network the model judges the prose itself, twice, and the masks cross
consensus exactly as they do here.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import glsim  # noqa: E402
from glsim import CURATOR, OPERATOR, KEEPER  # noqa: E402


def show(mask, bar):
    bits = [int(b) for b in mask.split("|")]
    cells = " ".join(str(b) for b in bits)
    flag = "ATTAINED" if sum(bits) >= bar else "building"
    return f"[{cells}]  {flag}"


def main():
    gate = json.loads((ROOT / "samples" / "gate_tranche_two.json").read_text())
    filings = json.loads((ROOT / "samples" / "filings.json").read_text())

    module = glsim.load_module(ROOT / "contracts" / "meridian.py")
    chain = glsim.Chain(module, "Meridian")
    chain.model = glsim.keyword_model
    c = chain.contract

    title = gate["title"]
    clauses = "|".join(gate["clauses"])
    bar = gate["bar"]

    print("=" * 74)
    print("MERIDIAN - milestone attestation, offline tour")
    print("=" * 74)

    print(f'\n1. CURATOR opens "{title}"  (bar {bar} of {len(gate["clauses"])})')
    for i, cl in enumerate(gate["clauses"]):
        print(f"     [{i}] {cl}")
    chain.tx(c.open_gate, title, clauses, bar, gate["operator"], sender=CURATOR)
    st = chain.tx(c.standing_of, 0)
    print("   frozen:", st["standing"])

    print("\n2. OPERATOR files the quarterly narrative - names, not proof")
    chain.tx(c.file, 0, filings[0]["path"], sender=OPERATOR)
    chain.tx(c.judge, 0)
    f = chain.tx(c.filing, 0)
    st = chain.tx(c.standing_of, 0)
    print(f"   audit: {f['mask']}  -> void: {f['void']}")
    print(f"   standing: {show(st['standing'], bar)}")

    print("\n3. OPERATOR files the real artefacts (alpha, beta, gamma)")
    chain.tx(c.file, 0, filings[1]["path"], sender=OPERATOR)
    chain.tx(c.judge, 1)
    st = chain.tx(c.standing_of, 0)
    print(f"   audit: {chain.tx(c.filing, 1)['mask']}")
    print(f"   standing: {show(st['standing'], bar)}")
    print(f"   payout gate attained_for(operator): {chain.tx(c.attained_for, 0, OPERATOR)}")

    print("\n4. THE ONLY WAY DOWN - CURATOR strikes filing 1 (row kept, marked)")
    chain.tx(c.strike, 1, sender=CURATOR)
    st = chain.tx(c.standing_of, 0)
    print(f"   standing: {show(st['standing'], bar)}")
    kept = chain.tx(c.filing, 1)
    print(f"   row 1: struck={kept['struck']}  audit preserved: {kept['mask']}")

    print("\n5. A KEEPER is empowered and files the deployment evidence")
    chain.tx(c.empower, 0, KEEPER, sender=CURATOR)
    chain.tx(c.file, 0, filings[2]["path"], sender=KEEPER)
    chain.tx(c.file, 0, filings[3]["path"], sender=KEEPER)
    chain.tx(c.judge, 2)
    chain.tx(c.judge, 3)
    st = chain.tx(c.standing_of, 0)
    print(f"   audits: {chain.tx(c.filing, 2)['mask']} + {chain.tx(c.filing, 3)['mask']}")
    print(f"   standing: {show(st['standing'], bar)}")
    print("   attained again - on a different three conditions than before")

    print("\n6. The keeper is relieved; the row and its count are kept")
    chain.tx(c.relieve, 0, KEEPER, sender=CURATOR)
    print(f"   keepers: {chain.tx(c.keepers_of, 0)['keepers']}")
    print(f"   may_file(keeper) now: {chain.tx(c.may_file, 0, KEEPER)}")

    print("\nFinal record, as any caller on chain would read it:")
    print(json.dumps(chain.tx(c.standing_of, 0), indent=2))


if __name__ == "__main__":
    main()
