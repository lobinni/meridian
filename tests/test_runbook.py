"""Replays docs/QUICKSTART.md step by step and asserts every value the
walkthrough tells the reader to expect - the runbook is tested like the code.

If a number in this file and the number in QUICKSTART.md ever disagree, one
of them is lying, and it is not the test.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import glsim
from glsim import CURATOR, OPERATOR, KEEPER

from conftest import open_std, filing_for, LONG_TEXT


def test_the_quickstart_runbook(chain):
    c = chain.contract

    # Step 1 - the curator opens the gate: four conditions, a bar of three,
    # the operator bound to its address. Everything below is on gate 0.
    open_std(chain)
    st = chain.tx(c.standing_of, 0)
    assert (st["clauses"], st["bar"], st["n_standing"]) == (4, 3, 0)
    assert st["standing"] == "0|0|0|0"
    assert st["attained"] is False

    # Step 2 - a filing that NAMES the work without showing it. The audit
    # returns nothing: 0|0|0|0, recorded as void.
    mentions = (
        LONG_TEXT
        + " We are enrolled to begin the alpha audit in October and the beta "
        "testnet launch is scheduled for next quarter."
    )
    chain.tx(c.file, 0, mentions, sender=OPERATOR)
    chain.tx(c.judge, 0)
    f0 = chain.tx(c.filing, 0)
    assert f0["mask"] == "0|0|0|0"
    assert f0["void"] is True
    assert chain.tx(c.standing_of, 0)["n_standing"] == 0

    # Step 3 - the operator files the real artefacts: alpha, beta, gamma.
    # The gate attains the bar.
    chain.tx(c.file, 0, filing_for("alpha", "beta", "gamma"), sender=OPERATOR)
    chain.tx(c.judge, 1)
    st = chain.tx(c.standing_of, 0)
    assert st["standing"] == "1|1|1|0"
    assert st["attained"] is True
    assert chain.tx(c.attained_for, 0, OPERATOR) is True

    # Step 4 - the only way down. The curator strikes filing 1: the row is
    # kept, marked, and the union recomputed from what remains.
    chain.tx(c.strike, 1, sender=CURATOR)
    st = chain.tx(c.standing_of, 0)
    assert st["standing"] == "0|0|0|0"
    assert st["attained"] is False
    assert st["struck"] == 1
    assert chain.tx(c.filing, 1)["struck"] is True
    assert chain.tx(c.filing, 1)["mask"] == "1|1|1|0"  # the audit survives

    # Step 5 - an empowered keeper files the deployment evidence, and the
    # gate attains again on a DIFFERENT three conditions.
    chain.tx(c.empower, 0, KEEPER, sender=CURATOR)
    chain.tx(c.file, 0, filing_for("beta", "delta"), sender=KEEPER)
    chain.tx(c.file, 0, filing_for("gamma"), sender=KEEPER)
    chain.tx(c.judge, 2)
    chain.tx(c.judge, 3)
    st = chain.tx(c.standing_of, 0)
    assert st["standing"] == "0|1|1|1"
    assert st["attained"] is True

    # Step 6 - the keeper is relieved. The row and its count are kept.
    chain.tx(c.relieve, 0, KEEPER, sender=CURATOR)
    keepers = chain.tx(c.keepers_of, 0)["keepers"]
    assert keepers == [{"who": KEEPER, "active": False, "filed": 2}]
    assert chain.tx(c.may_file, 0, KEEPER) is False

    # The final record, exactly as QUICKSTART prints it.
    final = chain.tx(c.standing_of, 0)
    assert final == {
        "title": "Tranche Two",
        "curator": CURATOR,
        "operator": OPERATOR,
        "sealed": False,
        "clauses": 4,
        "bar": 3,
        "standing": "0|1|1|1",
        "n_standing": 3,
        "attained": True,
        "filings": 4,
        "judged": 4,
        "void": 1,
        "struck": 1,
    }
