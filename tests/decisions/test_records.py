"""Story D3 criteria 1, 2, 4 and 6: a record for every opportunity and for the day's "no trade"; a replay through D2
reproduces every record (decision, alternatives, risk and validity reasons); records are never rewritten and a
correction is a new linked run; the schema and its three-book fields are validated."""

import json

import pytest

from fno.constants import Decision
from fno.playbook.decision_record import RecordError, decision_facts, validate_record
from fno.playbook.decision_run import replay
from fno.playbook.decision_store import DecisionStore, DuplicateRun
from tests.playbook.evaluation_builders import DAY, Counts, book_with_open, evaluator, price

from .builders import SAME_CODE, doc, run_day, snapshot


def records(run):
    return {p.stem: json.loads(p.read_text()) for p in run.glob("*.json") if p.name != "inputs.json"}


def test_every_opportunity_and_the_day_have_a_record(tmp_path):
    run = run_day(tmp_path, snapshot(doc("sc-a"), doc("sc-b", expected=-5.0)))
    stored = records(run)
    assert set(stored) == {"sc-a-v1_2026-11-27", "sc-b-v1_2026-11-27", "no_trade"}
    assert stored["sc-b-v1_2026-11-27"]["decision"]["action"] == "no trade"  # criterion 1: no-trade outcomes too
    assert stored["no_trade"]["decision"]["reason"] == "chosen: ['sc-a-v1:2026-11-27']"
    assert {a["opportunity_id"] for a in stored["sc-a-v1_2026-11-27"]["alternatives"]} == {"sc-b-v1:2026-11-27"}


def test_nothing_approved_still_records_the_days_no_trade(tmp_path):
    stored = records(run_day(tmp_path, snapshot(doc("sc-x", status="research"))))
    assert set(stored) == {"no_trade"} and stored["no_trade"]["decision"]["action"] == "no trade"


@pytest.mark.parametrize(
    ("case", "seen"),
    [
        ("chosen and not chosen: slot", "slot:"), ("rule did not fire", "rule did not fire"),
        ("bad prices on every width", "bad prices"), ("unproven", "unproven:"), ("shadow", "shadow: would trade"),
    ],
)  # fmt: skip
def test_a_replay_through_d2_reproduces_every_record(tmp_path, case, seen):
    docs, kwargs = [doc("sc-a"), doc("sc-b", expected=300.0)], {"the_book": book_with_open(2)}
    if case == "rule did not fire":
        kwargs = {"values": {"F1_live_atm_iv_minus_rv20": -1.0}}
    elif case == "bad prices on every width":
        kwargs = {
            "prices": {
                (k, t): (500.0 if k in (25_500, 24_500) else price(k, t))
                for k in range(24_000, 26_050, 50)
                for t in ("CE", "PE")
            }
        }
    elif case == "unproven":
        kwargs = {"counts": Counts(completed=3, open_=1)}
    elif case == "shadow":
        docs = [doc("sc-a"), doc("sc-new", status="research")]
    playbook = snapshot(*docs, registered_research=("sc-new",))
    run = run_day(tmp_path, playbook, **kwargs)
    said = " ".join(f"{r['decision']['outcome']} {r['decision']['reason']}" for r in records(run).values())
    assert seen in said  # the case really produced that D2 outcome and reason
    assert replay(run, evaluator(), SAME_CODE) == []


def test_a_replay_finds_an_edited_reason_and_edited_inputs(tmp_path):
    run = run_day(tmp_path, snapshot(doc("sc-a"), doc("sc-b", expected=300.0)), the_book=book_with_open(2))
    loser = run / "sc-a-v1_2026-11-27.json"
    record = json.loads(loser.read_text())
    assert record["decision"]["outcome"] == Decision.NOT_CHOSEN and record["risk"]["verdicts"]
    loser.write_text(loser.read_text().replace("slot:", "cash:"))
    assert any("sc-a-v1_2026-11-27.json" in d for d in replay(run, evaluator(), SAME_CODE))
    (run / "inputs.json").write_text((run / "inputs.json").read_text().replace('"spot":25000.0', '"spot":25001.0'))
    assert replay(run, evaluator(), SAME_CODE) == ["inputs.json: its SHA-256 differs from the one the records name"]


def test_the_same_inputs_twice_are_refused_new_inputs_make_a_new_run(tmp_path):
    playbook = snapshot(doc("sc-a"))
    first = run_day(tmp_path, playbook)
    with pytest.raises(DuplicateRun, match="already decided"):
        run_day(tmp_path, playbook)
    second = run_day(tmp_path, playbook, the_book=book_with_open(1))
    assert (first.name, second.name) == ("2026-10-13-r1", "2026-10-13-r2")


def test_a_run_is_never_rewritten_and_an_edit_is_found(tmp_path):
    run = run_day(tmp_path, snapshot(doc("sc-a")))
    store = DecisionStore(tmp_path, "book1_rules")
    with pytest.raises(FileExistsError, match="never rewritten"):
        store.write(DAY, run.name, None, [records(run)["no_trade"]])
    assert store.edited(run) == []
    (run / "no_trade.json").write_text("{}")
    assert store.edited(run) == ["no_trade.json"]


def test_a_correction_is_a_new_run_linked_to_the_record_it_corrects(tmp_path):
    run = run_day(tmp_path, snapshot(doc("sc-a")))
    store = DecisionStore(tmp_path, "book1_rules")
    original = records(run)["sc-a-v1_2026-11-27"]
    run_id = store.next_run_id(DAY)
    corrected = {**original, "run_id": run_id, "reason": "corrected: wrong lot size recorded",
                 "corrects": {"run_id": run.name, "opportunity_id": original["opportunity_id"]}}  # fmt: skip
    fixed = store.write(DAY, run_id, None, [corrected])
    assert fixed.name == "2026-10-13-r2" and records(fixed)["sc-a-v1_2026-11-27"]["corrects"]["run_id"] == run.name
    assert records(run)["sc-a-v1_2026-11-27"] == original  # the original stays as written


def test_every_record_matches_its_schema_and_feeds_d6(tmp_path):
    stored = records(run_day(tmp_path, snapshot(doc("sc-a"))))
    for record in stored.values():
        validate_record(record)
    facts = decision_facts(stored["sc-a-v1_2026-11-27"], "d" * 40)
    assert facts.decision_id == "2026-10-13-r1/sc-a-v1:2026-11-27" and set(facts.served) == {"playbook", "config"}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda r: r.pop("forecasts"), "fields missing"),
        (lambda r: r.update(extra=1), "unknown"),
        (lambda r: r.update(schema_version=2), "schema_version"),
        (lambda r: r.update(book="book2_hybrid"), "must fill"),  # Book 2 must name its model and session
        (lambda r: r.update(served={}), "served"),
        (lambda r: r.update(common_pack_sha256=None), "must fill"),
    ],
)
def test_a_record_off_its_schema_is_refused(tmp_path, change, message):
    record = records(run_day(tmp_path, snapshot(doc("sc-a"))))["no_trade"]
    change(record)
    with pytest.raises(RecordError, match=message):
        validate_record(record)


def test_book_3_may_leave_the_rule_default_empty(tmp_path):
    record = records(run_day(tmp_path, snapshot(doc("sc-a"))))["no_trade"]
    record.update(book="book3_ai", rule_default=None, model_served="m", session_id="s", strategy_id="x",
                  strategy_spec_sha256="y")  # fmt: skip
    validate_record(record)
    record["book"] = "book2_hybrid"
    with pytest.raises(RecordError, match="rule_default"):
        validate_record(record)


def test_a_book_and_a_shadow_record_of_one_opportunity_both_survive_and_a_true_clash_is_refused(tmp_path):
    """Story R3 (the orchestrator's store fix): a shadow record's file name carries its mode, so nothing overwrites
    across modes; two records that would still share a file refuse the whole run, never keep one silently."""
    from fno.playbook.decision_store import RecordClash, record_file

    run = run_day(tmp_path / "a", snapshot(doc("sc-a")))
    book = records(run)["sc-a-v1_2026-11-27"]
    shadow = book | {"mode": "shadow"}  # the same opportunity ID
    store = DecisionStore(tmp_path / "b", "book1_rules")
    written = store.write(DAY, f"{DAY}-r1", None, [book, shadow])
    assert record_file(book["opportunity_id"], "shadow") == "shadow_sc-a-v1_2026-11-27.json"
    assert records(written) == {"sc-a-v1_2026-11-27": book, "shadow_sc-a-v1_2026-11-27": shadow}
    with pytest.raises(RecordClash, match="sc-a-v1_2026-11-27.json"):
        store.write(DAY, f"{DAY}-r2", None, [book, book | {"risk": None}])
    assert [r.name for r in store.runs(DAY)] == [f"{DAY}-r1"]  # nothing of the refused run was written


@pytest.mark.parametrize("book", ["book1_rules", "book2_hybrid", "book3_ai"])
@pytest.mark.parametrize("override", ["journal/book2_hybrid/owner_overrides.csv#3", "", {"reason": "x"}])
def test_an_owner_override_is_refused_for_every_book(tmp_path, book, override):
    """DESK_DECISIONS row 229 item 4: the owner never overrides a paper decision; any value but null is refused."""
    record = records(run_day(tmp_path, snapshot(doc("sc-a"))))["no_trade"]
    record.update(book=book, model_served="m", session_id="s", strategy_id="x", strategy_spec_sha256="y",
                  authority_check="allowed: follow_rule")  # fmt: skip
    validate_record(record)
    record["owner_override"] = override
    with pytest.raises(RecordError, match="owner never overrides"):
        validate_record(record)


def test_book_3_s_day_record_alone_may_name_no_strategy(tmp_path):
    """F6 (16 Oct): the day's "no trade" record has no strategy; an opportunity record of Book 3 must name its own."""
    stored = records(run_day(tmp_path, snapshot(doc("sc-a"))))
    three_book = {"book": "book3_ai", "rule_default": None, "authority_check": None, "model_served": "m",
                  "session_id": "s", "strategy_id": None, "strategy_spec_sha256": None}  # fmt: skip
    validate_record(stored["no_trade"] | three_book)
    with pytest.raises(RecordError, match="strategy_id"):
        validate_record(stored["sc-a-v1_2026-11-27"] | three_book)


@pytest.mark.parametrize("field", ["reason", "authority_check", "chosen_action", "rule_default"])
def test_a_book_2_record_must_give_its_reason_and_the_envelope_s_verdict(tmp_path, field):
    """Story D4 criterion 7: present is not enough; an empty reason or verdict is refused for Book 2."""
    record = records(run_day(tmp_path, snapshot(doc("sc-a"))))["no_trade"]
    record.update(book="book2_hybrid", model_served="m", session_id="s", authority_check="allowed: follow_rule")
    validate_record(record)
    record[field] = ""
    with pytest.raises(RecordError, match="non-empty"):
        validate_record(record)
