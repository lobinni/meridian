"""Opt-in integration suite against a live GenLayer network.

Deliberately opt-in: it skips when `genlayer-test` is absent, and it also
skips when the plugin is present without GENLAYER_STUDIO set - otherwise
anybody who reviews GenLayer contracts, and therefore has the plugin
installed, would see a wall of connection errors on a repository that
promises an offline run.

Two modes:

  1. AGAINST THE PUBLISHED DEPLOYMENT (read-only smoke):

         GENLAYER_STUDIO=1 \
         MERIDIAN_ADDRESS=0x947D2D00Dbc6738581C16309bc77F81AB0288Fd0 \
         gltest --network studionet tests/test_integration.py

     Only view calls run. Nothing is written to the shared deployment.

  2. AGAINST A FRESH DEPLOY (full lifecycle, writes + a real audit):

         GENLAYER_STUDIO=1 gltest --network studionet tests/test_integration.py

`judge()` runs real prompts through real validators there, so mode 2 is
slow by design.
"""

import os
import pathlib

import pytest

pytest.importorskip("gltest", reason="genlayer-test is not installed")

if not os.environ.get("GENLAYER_STUDIO"):
    pytest.skip(
        "integration tests are opt-in: set GENLAYER_STUDIO=1", allow_module_level=True
    )

from gltest import get_contract_factory, create_account  # noqa: E402
from gltest.assertions import tx_execution_succeeded  # noqa: E402

CONTRACT_PATH = pathlib.Path(__file__).parent.parent / "contracts" / "meridian.py"
ONCHAIN = os.environ.get("MERIDIAN_ADDRESS")  # e.g. deployments/studionet.json

CLAUSES = (
    "alpha audit report published with zero critical findings|"
    "beta testnet live with five hundred weekly users|"
    "gamma documentation covering every public endpoint"
)


@pytest.fixture(scope="module")
def contract():
    factory = get_contract_factory(contract_file_path=str(CONTRACT_PATH))
    if ONCHAIN:
        # Read-only mode: bind the published deployment instead of deploying.
        return factory.build_contract(contract_address=ONCHAIN)
    return factory.deploy()


# ---------------------------------------------------------------------------
# Mode 1 + 2: view calls are safe against any deployment, shared or fresh
# ---------------------------------------------------------------------------


def test_views_respond_with_the_documented_shapes(contract):
    n = contract.gate_count(args=[]).call()
    assert isinstance(n, int) and n >= 0
    assert isinstance(contract.filing_count(args=[]).call(), int)
    if n > 0:
        st = contract.standing_of(args=[0]).call()
        for key in (
            "title", "curator", "operator", "sealed", "clauses", "bar",
            "standing", "n_standing", "attained", "filings", "judged",
            "void", "struck",
        ):
            assert key in st, f"standing_of is missing {key}"
        assert isinstance(st["standing"], str)
        assert st["attained"] == (st["n_standing"] >= st["bar"])
        assert contract.curator_of(args=[0]).call() == st["curator"]
        assert contract.operator_of(args=[0]).call() == st["operator"]


def test_attained_for_is_address_bound(contract):
    if contract.gate_count(args=[]).call() == 0:
        pytest.skip("deployment has no gates yet")
    operator = contract.operator_of(args=[0]).call()
    st = contract.standing_of(args=[0]).call()
    assert contract.attained_for(args=[0, operator]).call() == st["attained"]
    # A different address never inherits the standing.
    other = "0x" + "42" * 20
    if other.lower() != str(operator).lower():
        assert contract.attained_for(args=[0, other]).call() is False


def test_may_file_mirrors_the_write_rule(contract):
    if contract.gate_count(args=[]).call() == 0:
        pytest.skip("deployment has no gates yet")
    stranger = "0x" + "77" * 20
    assert contract.may_file(args=[0, stranger]).call() is False
    assert contract.may_file(args=[0, "not-an-address"]).call() is False


# ---------------------------------------------------------------------------
# Mode 2 only: writes. Skipped against a shared deployment.
# ---------------------------------------------------------------------------

needs_fresh = pytest.mark.skipif(
    bool(ONCHAIN), reason="read-only mode against a shared deployment"
)


@needs_fresh
def test_open_and_read_back(contract):
    operator = create_account()
    tx = contract.open_gate(
        args=["Integration Gate", CLAUSES, 2, str(operator.address)]
    ).transact()
    assert tx_execution_succeeded(tx)

    st = contract.standing_of(args=[0]).call()
    assert st["clauses"] == 3
    assert st["bar"] == 2
    assert st["standing"] == "0|0|0"
    assert st["attained"] is False


@needs_fresh
def test_file_audit_and_payout_gate(contract):
    body = (
        "Deployment report 2026-05. The beta testnet has been live for six "
        "continuous weeks and the telemetry dashboard shows an average of "
        "812 weekly active users over the last four weeks. The alpha audit "
        "and the gamma documentation are still in progress."
    )
    tx = contract.file(args=[0, body]).transact()
    assert tx_execution_succeeded(tx)

    tx = contract.judge(args=[0]).transact(wait_interval=2000, wait_retries=60)
    assert tx_execution_succeeded(tx)

    st = contract.standing_of(args=[0]).call()
    # One clean condition, honestly reported: beta stands, one short of the bar.
    assert st["judged"] == 1
    assert st["n_standing"] >= 1
    assert st["attained"] == (st["n_standing"] >= st["bar"])
