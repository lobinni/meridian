"""End-to-end tests on glsim: the full lifecycle, the permissions, the
budgets, and the consensus defences against a leader that lies.

Every test deploys a fresh contract (the `chain` fixture), so nothing leaks
between tests.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from glsim import CURATOR, OPERATOR, KEEPER, KEEPER2, STRANGER, UserError

from conftest import (
    CLAUSES,
    LONG_TEXT,
    open_std,
    filing_for,
)


def refuse(chain, fn, *args, sender=CURATOR, **kw):
    with pytest.raises(UserError):
        chain.tx(fn, *args, sender=sender, **kw)


def standing(chain, gate=0):
    return chain.tx(chain.contract.standing_of, gate)


# ---------------------------------------------------------------------------
# open_gate: freezing the yardstick, or refusing to
# ---------------------------------------------------------------------------


def test_open_freezes_everything(chain):
    open_std(chain)
    st = standing(chain)
    assert st["title"] == "Tranche Two"
    assert st["clauses"] == 4
    assert st["bar"] == 3
    assert st["standing"] == "0|0|0|0"
    assert st["n_standing"] == 0
    assert st["attained"] is False
    assert st["filings"] == 0
    assert st["curator"] == CURATOR
    assert st["operator"] == OPERATOR


def test_bad_gates_are_refused_with_the_reason(chain):
    c = chain.contract
    refuse(chain, c.open_gate, "", CLAUSES, 3, OPERATOR)
    refuse(chain, c.open_gate, "t" * 200, CLAUSES, 3, OPERATOR)
    refuse(chain, c.open_gate, "T", "", 1, OPERATOR)                       # no conditions
    refuse(chain, c.open_gate, "T", "|".join("c%d" % i for i in range(11)), 3, OPERATOR)  # over the cap
    refuse(chain, c.open_gate, "T", "x" * 91, 1, OPERATOR)                 # over-long condition
    refuse(chain, c.open_gate, "T", "same|same", 1, OPERATOR)              # duplicates
    refuse(chain, c.open_gate, "T", CLAUSES, 0, OPERATOR)                  # a bar of zero
    refuse(chain, c.open_gate, "T", CLAUSES, 5, OPERATOR)                  # a bar above the list
    refuse(chain, c.open_gate, "T", CLAUSES, 3, "not-an-address")
    refuse(chain, c.open_gate, "T", CLAUSES, 3, CURATOR)                   # self-attestation
    assert chain.tx(c.gate_count) == 0


# ---------------------------------------------------------------------------
# file: authority and budgets
# ---------------------------------------------------------------------------


def test_a_stranger_cannot_file(chain):
    open_std(chain)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=STRANGER)
    assert chain.tx(chain.contract.filing_count) == 0
    assert chain.tx(chain.contract.may_file, 0, STRANGER) is False


def test_curator_operator_and_keeper_can_file(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=CURATOR)
    chain.tx(chain.contract.file, 0, filing_for("beta"), sender=OPERATOR)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    chain.tx(chain.contract.file, 0, filing_for("gamma"), sender=KEEPER)
    assert chain.tx(chain.contract.filing_count) == 3
    rows = chain.tx(chain.contract.filings_of, 0)["filings"]
    assert [r["by"] for r in rows] == [CURATOR, OPERATOR, KEEPER]


def test_may_file_follows_authority(chain):
    open_std(chain)
    assert chain.tx(chain.contract.may_file, 0, CURATOR) is True
    assert chain.tx(chain.contract.may_file, 0, OPERATOR) is True
    assert chain.tx(chain.contract.may_file, 0, KEEPER) is False
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    assert chain.tx(chain.contract.may_file, 0, KEEPER) is True
    chain.tx(chain.contract.relieve, 0, KEEPER, sender=CURATOR)
    assert chain.tx(chain.contract.may_file, 0, KEEPER) is False
    assert chain.tx(chain.contract.may_file, 0, "garbage") is False


def test_may_file_raises_on_a_bad_id_like_every_read(chain):
    with pytest.raises(UserError):
        chain.tx(chain.contract.may_file, 9, CURATOR)


def test_bad_filings_are_refused_with_the_reason(chain):
    open_std(chain)
    refuse(chain, chain.contract.file, 0, "too short", sender=OPERATOR)
    refuse(chain, chain.contract.file, 0, "x" * 721, sender=OPERATOR)
    with pytest.raises(UserError):
        chain.tx(chain.contract.file, 7, filing_for("alpha"), sender=OPERATOR)
    assert chain.tx(chain.contract.filing_count) == 0


def test_a_gate_takes_at_most_48_filings(chain):
    open_std(chain)
    for _ in range(48):
        chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=CURATOR)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=CURATOR)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)


def test_the_last_twelve_slots_are_not_a_keepers(chain):
    open_std(chain)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    for _ in range(36):
        # The keeper files only FIVE, so its allowance (6) is still open:
        # the refusal that follows can only be the reserve speaking.
        chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=KEEPER if _ < 5 else CURATOR)
    # 36 filed. A keeper is out of the last twelve; the principals are not.
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=KEEPER)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)


def test_a_keeper_has_its_own_allowance_of_six(chain):
    open_std(chain)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    for _ in range(6):
        chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=KEEPER)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=KEEPER)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=CURATOR)  # others unaffected


def test_the_operator_has_its_own_allowance_of_sixteen(chain):
    open_std(chain)
    for _ in range(16):
        chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=CURATOR)


def test_a_relieve_and_reempower_does_not_refill_an_allowance(chain):
    open_std(chain)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    for _ in range(6):
        chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=KEEPER)
    chain.tx(chain.contract.relieve, 0, KEEPER, sender=CURATOR)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=KEEPER)
    row = chain.tx(chain.contract.keepers_of, 0)["keepers"][0]
    assert row["filed"] == 6 and row["active"] is True


def test_the_keeper_chain_is_capped_at_24_rows_relieved_ones_included(chain):
    c = chain.contract
    open_std(chain)
    for i in range(24):
        addr = "0x%040x" % (i + 1)
        chain.tx(c.empower, 0, addr, sender=CURATOR)
        chain.tx(c.relieve, 0, addr, sender=CURATOR)
    refuse(chain, c.empower, 0, KEEPER, sender=CURATOR)


def test_the_active_cap_survives_a_relieve_and_reempower_cycle(chain):
    c = chain.contract
    open_std(chain)
    addrs = ["0x%040x" % (i + 1) for i in range(12)]
    for a in addrs:
        chain.tx(c.empower, 0, a, sender=CURATOR)
    refuse(chain, c.empower, 0, KEEPER, sender=CURATOR)  # 12 active already
    chain.tx(c.relieve, 0, addrs[0], sender=CURATOR)
    chain.tx(c.empower, 0, addrs[0], sender=CURATOR)     # back to 12, fine
    refuse(chain, c.empower, 0, KEEPER, sender=CURATOR)  # still full


def test_keeper_management_refusals_are_clean(chain):
    c = chain.contract
    open_std(chain)
    refuse(chain, c.empower, 0, "nope", sender=CURATOR)
    refuse(chain, c.empower, 0, CURATOR, sender=CURATOR)
    refuse(chain, c.empower, 0, OPERATOR, sender=CURATOR)
    chain.tx(c.empower, 0, KEEPER, sender=CURATOR)
    refuse(chain, c.empower, 0, KEEPER, sender=CURATOR)      # twice
    refuse(chain, c.relieve, 0, STRANGER, sender=CURATOR)    # never a keeper
    chain.tx(c.relieve, 0, KEEPER, sender=CURATOR)
    refuse(chain, c.relieve, 0, KEEPER, sender=CURATOR)      # twice
    refuse(chain, c.relieve, 0, "nope", sender=CURATOR)
    # And only the curator runs any of it.
    refuse(chain, c.empower, 0, KEEPER2, sender=OPERATOR)
    refuse(chain, c.relieve, 0, KEEPER, sender=KEEPER)


def test_keeping_is_scoped_to_one_gate(chain):
    c = chain.contract
    open_std(chain)
    chain.tx(c.open_gate, "Other", CLAUSES, 2, OPERATOR, sender=CURATOR)
    chain.tx(c.empower, 0, KEEPER, sender=CURATOR)
    assert chain.tx(c.may_file, 0, KEEPER) is True
    assert chain.tx(c.may_file, 1, KEEPER) is False


def test_two_gates_never_see_each_others_filings(chain):
    c = chain.contract
    open_std(chain)
    chain.tx(c.open_gate, "Other", "solo condition here", 1, OPERATOR, sender=CURATOR)
    chain.tx(c.file, 1, filing_for("solo"), sender=CURATOR)
    chain.tx(c.judge, 0)
    assert standing(chain, 1)["n_standing"] == 1
    assert standing(chain, 0)["n_standing"] == 0
    assert chain.tx(c.gate_count) == 2


# ---------------------------------------------------------------------------
# judge: the audit itself
# ---------------------------------------------------------------------------


def test_a_filing_lands_before_it_is_judged(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    st = standing(chain)
    assert st["filings"] == 1
    assert st["judged"] == 0
    f = chain.tx(chain.contract.filing, 0)
    assert f["judged"] is False and f["mask"] == "" and f["by"] == OPERATOR


def test_one_audit_demonstrates_what_the_filing_shows(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "gamma"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    f = chain.tx(chain.contract.filing, 0)
    assert f["judged"] is True
    assert f["mask"] == "1|0|1|0"
    assert f["counted"] is True and f["void"] is False
    st = standing(chain)
    assert st["standing"] == "1|0|1|0"
    assert st["n_standing"] == 2
    assert st["attained"] is False  # bar is three


def test_the_standing_is_the_union_across_filings(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    chain.tx(chain.contract.file, 0, filing_for("beta", "gamma"), sender=CURATOR)
    chain.tx(chain.contract.judge, 1)
    st = standing(chain)
    assert st["standing"] == "1|1|1|0"
    assert st["n_standing"] == 3
    assert st["attained"] is True
    # A zero-mask audit cannot pull a bit down.
    chain.tx(chain.contract.file, 0, LONG_TEXT + " Nothing demonstrated here", sender=CURATOR)
    chain.tx(chain.contract.judge, 2)
    assert standing(chain)["standing"] == "1|1|1|0"


def test_a_filing_that_demonstrates_nothing_is_void(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, LONG_TEXT + " Plans and intentions only.", sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    f = chain.tx(chain.contract.filing, 0)
    assert f["void"] is True
    assert f["counted"] is True  # audited before seal, so it entered - as zeros
    assert f["mask"] == "0|0|0|0"
    assert standing(chain)["void"] == 1


def test_an_audit_cannot_be_replayed_into_a_better_one(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    refuse(chain, chain.contract.judge, 0)


def test_struck_filings_are_not_judged(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.strike, 0, sender=CURATOR)
    refuse(chain, chain.contract.judge, 0)


def test_anyone_may_call_judge(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0, sender=STRANGER)
    assert standing(chain)["judged"] == 1


def test_reads_with_bad_ids_are_user_errors(chain):
    c = chain.contract
    open_std(chain)
    for call in (c.standing_of, c.clauses_of, c.filings_of, c.keepers_of, c.attained,
                 c.curator_of, c.operator_of, c.sealed):
        with pytest.raises(UserError):
            chain.tx(call, 9)
        with pytest.raises(UserError):
            chain.tx(call, -1)
    with pytest.raises(UserError):
        chain.tx(c.holding, 0, 4)
    with pytest.raises(UserError):
        chain.tx(c.filing, 9)


# -- the two passes -----------------------------------------------------------


def dual_model(ahead_mask, astern_mask_in_reversed_order):
    """A model that answers the forward pass with one mask and the reversed
    pass with another. The prompts are told apart by which condition heads
    the <conditions> list."""

    def model(prompt):
        first_row_forward = "[0] alpha audit report" in prompt
        mask = ahead_mask if first_row_forward else astern_mask_in_reversed_order
        return {"mask": mask, "because": "scripted"}

    return model


def test_a_row_marked_from_only_one_end_of_the_list_does_not_stand(chain):
    open_std(chain)
    # The position-leaning model: it marks whichever row heads the list it
    # was shown. Forward that is alpha (frozen bit 0); reversed, with the
    # list flipped, the row at [0] is delta (frozen bit 3).
    chain.model = dual_model("1|0|0|0", "1|0|0|0")  # always the first row shown
    chain.tx(chain.contract.file, 0, filing_for(), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    # Each ordering marked a different row; nothing both marked stands.
    assert chain.tx(chain.contract.filing, 0)["mask"] == "0|0|0|0"
    assert standing(chain)["n_standing"] == 0


def test_reversed_answer_is_read_back_into_the_frozen_order(chain):
    open_std(chain)
    # The reversed list is [delta, gamma, beta, alpha]. A reversed mask of
    # "1|0|1|0" therefore means delta (bit 3) and beta (bit 1) - exactly the
    # rows the forward pass marked, so both stand.
    chain.model = dual_model("0|1|0|1", "1|0|1|0")
    chain.tx(chain.contract.file, 0, filing_for(), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.filing, 0)["mask"] == "0|1|0|1"


def test_an_unusable_pass_demonstrates_nothing(chain):
    def model(prompt):
        if "[0] alpha audit report" in prompt:
            return {"mask": "1|1|1|1", "because": "fine"}    # forward works
        return ["not", "an", "object"]                        # reversed is junk

    chain.model = model
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for(), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.filing, 0)["mask"] == "0|0|0|0"
    assert chain.tx(chain.contract.filing, 0)["void"] is True


def test_an_answer_that_is_not_an_object_is_unusable_not_fatal(chain):
    chain.model = lambda prompt: "just a string"
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for(), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.filing, 0)["judged"] is True
    assert chain.tx(chain.contract.filing, 0)["mask"] == "0|0|0|0"


def test_the_why_is_stored_but_never_crosses_consensus(chain):
    # The keyword model emits a DIFFERENT because on every call - leader and
    # validator alike - and the round still settles, because the comparison
    # is the mask and only the mask.
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    f = chain.tx(chain.contract.filing, 0)
    assert f["mask"] == "1|0|0|0"
    assert f["why"].startswith("call-")
    assert f["why_is_leader_supplied"] is True


def test_a_lying_leaders_reason_is_scrubbed_on_the_way_in(chain):
    chain.model = lambda prompt: {
        "mask": "1|0|0|0" if "[0] alpha audit report" in prompt else "0|0|0|1",
        "because": 'see {"admin": true} `run shell` \x07' + "x" * 500,
    }
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for(), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    why = chain.tx(chain.contract.filing, 0)["why"]
    assert '"' not in why and "{" not in why and "`" not in why
    assert len(why) <= 160


# -- consensus defences against a rigged wire --------------------------------------


def test_a_leader_that_rolled_back_is_refused_and_nothing_is_stored(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.rig_error()
    refuse(chain, chain.contract.judge, 0)
    assert chain.tx(chain.contract.filing, 0)["judged"] is False


def test_a_lying_leader_is_refused_when_masks_differ(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    # The wire carries delta; every honest validator's own audit finds alpha.
    chain.rig_payload({"mask": "0|0|0|1", "because": "trust me"})
    refuse(chain, chain.contract.judge, 0)
    assert chain.tx(chain.contract.filing, 0)["judged"] is False
    assert standing(chain)["n_standing"] == 0


def test_a_leader_payload_that_is_not_a_mapping_is_refused_for_free(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    before = chain.prompt_count
    chain.rig_payload("0|0|0|1")
    refuse(chain, chain.contract.judge, 0)
    # Refused before the validator spent any prompts of its own: 2 (leader) + 0.
    assert chain.prompt_count == before + 2


def test_a_structurally_broken_proposal_dies_before_any_inference(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    before = chain.prompt_count
    chain.rig_payload({"mask": "1|1", "because": "short"})  # wrong length
    refuse(chain, chain.contract.judge, 0)
    assert chain.prompt_count == before + 2  # the free layer really is free


# ---------------------------------------------------------------------------
# strike: the only way down
# ---------------------------------------------------------------------------


def test_striking_lowers_the_standing_and_keeps_the_row(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "beta", "gamma"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert standing(chain)["attained"] is True
    chain.tx(chain.contract.strike, 0, sender=CURATOR)
    st = standing(chain)
    assert st["n_standing"] == 0
    assert st["attained"] is False
    assert st["struck"] == 1
    f = chain.tx(chain.contract.filing, 0)
    assert f["struck"] is True and f["mask"] == "1|1|1|0"  # the audit itself survives


def test_striking_twice_is_refused(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.strike, 0, sender=CURATOR)
    refuse(chain, chain.contract.strike, 0, sender=CURATOR)
    assert standing(chain)["struck"] == 1


def test_only_the_curator_strikes(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    refuse(chain, chain.contract.strike, 0, sender=OPERATOR)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    refuse(chain, chain.contract.strike, 0, sender=KEEPER)
    refuse(chain, chain.contract.strike, 0, sender=STRANGER)


def test_a_strike_only_removes_that_filings_contribution(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "beta"), sender=OPERATOR)
    chain.tx(chain.contract.file, 0, filing_for("beta", "gamma"), sender=CURATOR)
    chain.tx(chain.contract.judge, 0)
    chain.tx(chain.contract.judge, 1)
    assert standing(chain)["standing"] == "1|1|1|0"
    chain.tx(chain.contract.strike, 0, sender=CURATOR)
    # beta survives on the second filing; alpha and gamma fall with the first.
    assert standing(chain)["standing"] == "0|1|1|0"


def test_a_keeper_the_curator_no_longer_trusts_is_contained(chain):
    open_std(chain)
    chain.tx(chain.contract.empower, 0, KEEPER, sender=CURATOR)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "beta", "gamma"), sender=KEEPER)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.attained, 0) is True
    chain.tx(chain.contract.relieve, 0, KEEPER, sender=CURATOR)   # stops new filings
    refuse(chain, chain.contract.file, 0, filing_for("delta"), sender=KEEPER)
    chain.tx(chain.contract.strike, 0, sender=CURATOR)            # takes out the old
    assert standing(chain)["n_standing"] == 0
    rows = chain.tx(chain.contract.keepers_of, 0)["keepers"]
    assert rows == [{"who": KEEPER, "active": False, "filed": 1}]


# ---------------------------------------------------------------------------
# seal: freezing the standing upward
# ---------------------------------------------------------------------------


def test_a_sealed_gate_takes_no_more_filings(chain):
    open_std(chain)
    chain.tx(chain.contract.seal, 0, sender=CURATOR)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=CURATOR)
    refuse(chain, chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    assert chain.tx(chain.contract.may_file, 0, OPERATOR) is False


def test_sealing_twice_is_refused(chain):
    open_std(chain)
    chain.tx(chain.contract.seal, 0, sender=CURATOR)
    refuse(chain, chain.contract.seal, 0, sender=CURATOR)
    refuse(chain, chain.contract.seal, 0, sender=OPERATOR)


def test_an_audit_after_sealing_is_recorded_and_never_counted(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.seal, 0, sender=CURATOR)
    chain.tx(chain.contract.judge, 0)
    f = chain.tx(chain.contract.filing, 0)
    assert f["judged"] is True
    assert f["counted"] is False
    assert f["mask"] == "1|0|0|0"          # the record shows what was found
    assert standing(chain)["n_standing"] == 0  # the standing does not


def test_a_strike_after_sealing_recomputes_from_counted_masks_only(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "beta", "gamma"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.attained, 0) is True
    chain.tx(chain.contract.file, 0, filing_for("delta"), sender=CURATOR)
    chain.tx(chain.contract.seal, 0, sender=CURATOR)
    chain.tx(chain.contract.judge, 1)  # recorded, not counted
    assert standing(chain)["standing"] == "1|1|1|0"
    chain.tx(chain.contract.strike, 0, sender=CURATOR)
    # Down it goes, and the post-seal audit does not sneak back in.
    assert standing(chain)["standing"] == "0|0|0|0"
    assert standing(chain)["attained"] is False


def test_the_gate_keeps_working_after_a_strike(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    chain.tx(chain.contract.strike, 0, sender=CURATOR)
    chain.tx(chain.contract.file, 0, filing_for("beta", "gamma", "delta"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 1)
    st = standing(chain)
    assert st["standing"] == "0|1|1|1"
    assert st["attained"] is True
    assert st["sealed"] is False


# ---------------------------------------------------------------------------
# payout gating: what another contract would read
# ---------------------------------------------------------------------------


def test_attained_for_binds_the_outcome_to_the_payee(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "beta", "gamma"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.attained_for, 0, OPERATOR) is True
    assert chain.tx(chain.contract.attained_for, 0, STRANGER) is False
    assert chain.tx(chain.contract.attained_for, 0, "junk") is False
    # EIP-55 noise must not slip past the check.
    assert chain.tx(chain.contract.attained_for, 0, OPERATOR.upper().replace("0X", "0x")) is True


def test_not_attained_until_the_bar_is_crossed(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("alpha", "beta"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.attained, 0) is False
    assert chain.tx(chain.contract.attained_for, 0, OPERATOR) is False
    chain.tx(chain.contract.file, 0, filing_for("delta"), sender=CURATOR)
    chain.tx(chain.contract.judge, 1)
    assert chain.tx(chain.contract.attained, 0) is True


def test_holding_reports_one_condition(chain):
    open_std(chain)
    chain.tx(chain.contract.file, 0, filing_for("gamma"), sender=OPERATOR)
    chain.tx(chain.contract.judge, 0)
    assert chain.tx(chain.contract.holding, 0, 2) is True
    assert chain.tx(chain.contract.holding, 0, 0) is False
