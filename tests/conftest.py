import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import glsim  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent
CONTRACT_PATH = ROOT / "contracts" / "meridian.py"


@pytest.fixture(scope="session")
def meridian_mod():
    """The contract source, executed against the fake genlayer module."""
    return glsim.load_module(CONTRACT_PATH)


@pytest.fixture()
def chain(meridian_mod):
    """A fresh deployment per test, with the keyword model wired in."""
    c = glsim.Chain(meridian_mod, "Meridian")
    c.model = glsim.keyword_model
    return c


# A standard gate used across suites: four conditions, bar three.
CLAUSES = (
    "alpha audit report published with zero critical findings|"
    "beta testnet live with five hundred weekly users|"
    "gamma documentation covering every public endpoint|"
    "delta mainnet deployed and verified on the explorer"
)

COND_ALPHA = "alpha audit report published with zero critical findings"
COND_BETA = "beta testnet live with five hundred weekly users"
COND_GAMMA = "gamma documentation covering every public endpoint"
COND_DELTA = "delta mainnet deployed and verified on the explorer"

LONG_TEXT = (
    "Quarterly report. The committee reviewed the repository, the deployment "
    "records and the monitoring dashboards referenced below in full. "
)


def open_std(chain, sender=glsim.CURATOR, operator=glsim.OPERATOR, bar=3, clauses=CLAUSES):
    chain.tx(chain.contract.open_gate, "Tranche Two", clauses, bar, str(operator), sender=sender)
    return 0


def filing_for(*words):
    """A filing body that the keyword model reads as demonstrating exactly
    the given condition first-words (alpha|beta|gamma|delta)."""
    body = LONG_TEXT
    for w in words:
        body += " Milestone evidence: proven(%s)." % w
    return body
