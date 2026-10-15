"""Story E2b criterion 1: the committed common pack holds no per-contract quote figure (owner "8 A", decision B): no
`option:` item, no field named bid, ask or a size, and no number equal to any row's bid or ask; each chain's spot, the
capture's counts, India VIX, the NSE futures and both hashes are kept. A chain with two spots is refused."""

import csv
import json

import pytest

from fno.desk.pack_items import PackError

from .builders import CUTOFF, DAY, SNAPSHOT, builder, snapshot_folder

RAW_FIELDS = {"bid", "ask", "bid_qty", "ask_qty", "quote_bid", "quote_ask"}


def numbers_and_keys(value, numbers, keys):
    if isinstance(value, dict):
        for key, inner in value.items():
            keys.add(key)
            numbers_and_keys(inner, numbers, keys)
    elif isinstance(value, list):
        for inner in value:
            numbers_and_keys(inner, numbers, keys)
    elif isinstance(value, int | float) and not isinstance(value, bool):
        numbers.add(float(value))


def golden_rows(folder):
    return list(csv.DictReader((folder / f"{SNAPSHOT}.csv").open(encoding="utf-8")))


def test_no_per_contract_quote_and_no_raw_value_anywhere_in_the_pack(tmp_path):
    folder = snapshot_folder(tmp_path)
    pack = builder(tmp_path).build(DAY, CUTOFF)
    numbers, keys = set(), set()
    numbers_and_keys(pack.body, numbers, keys)
    raw = {float(r[k]) for r in golden_rows(folder) for k in ("bid", "ask") if r[k]}
    assert not any(i["name"].startswith("option:") for i in pack.body["items"]) and not RAW_FIELDS & keys
    assert raw and not raw & numbers, f"raw quote values in the pack: {sorted(raw & numbers)}"
    assert pack.body["schema_version"] == 2


def test_spot_per_chain_counts_vix_futures_and_hashes_are_kept(tmp_path):
    folder = snapshot_folder(tmp_path)
    rows, meta = golden_rows(folder), json.loads((folder / f"{SNAPSHOT}.meta.json").read_text(encoding="utf-8"))
    items = {i["name"]: i for i in builder(tmp_path).build(DAY, CUTOFF).body["items"]}
    for expiry in {r["expiry"] for r in rows}:
        chain = [r for r in rows if r["expiry"] == expiry]
        spot = items[f"spot:{expiry}"]
        assert spot["value"] == float(chain[0]["spot"])
        assert spot["available_at"] == min(r["response_received_at"] for r in chain)  # known with the first row
    counts = items["quote_counts"]["value"]
    expected = {  # the golden sidecar predates A4's count keys: absent counts stay absent (None), never zero
        "expected_contracts": meta.get("expected_contracts"),
        "recorded_contracts": meta.get("recorded_contracts"),
        "valid_contracts": sum(r["valid"] == "true" for r in rows),
        "complete": bool(meta.get("complete")),
    }
    assert counts == expected
    assert {"india_vix", *(f"future:{f['expiry']}" for f in meta["futures"])} <= set(items)


def test_a_chain_carrying_two_spots_is_refused_naming_its_expiry(tmp_path):
    folder = snapshot_folder(tmp_path)
    path = folder / f"{SNAPSHOT}.csv"
    rows = golden_rows(folder)
    rows[-1]["spot"] = str(float(rows[-1]["spot"]) + 0.05)
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(PackError, match=f"chain {rows[-1]['expiry']} carries 2 different spots"):
        builder(tmp_path).build(DAY, CUTOFF)


def test_a_chain_without_any_spot_keeps_its_item_with_no_value_for_c3_to_name(tmp_path):
    folder = snapshot_folder(tmp_path)
    path = folder / f"{SNAPSHOT}.csv"
    rows = [r | {"spot": ""} for r in golden_rows(folder)]
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    items = {i["name"]: i["value"] for i in builder(tmp_path).build(DAY, CUTOFF).body["items"]}
    spots = {name: value for name, value in items.items() if name.startswith("spot:")}
    assert spots and set(spots.values()) == {None} and "quote_counts" in items


def test_no_reader_in_the_app_looks_up_a_per_contract_pack_item():
    """Criterion 7: nothing in `fno/` names an `option:` pack item (the C3 spot check reads `spot:` items)."""
    from fno.config import ROOT

    found = [str(p.relative_to(ROOT)) for p in (ROOT / "fno").rglob("*.py")
             if any(f"{quote}option:" in p.read_text(encoding="utf-8") for quote in ("'", '"'))]  # fmt: skip
    assert found == []


def test_the_valid_count_counts_only_valid_rows(tmp_path):
    folder = snapshot_folder(tmp_path)
    path = folder / f"{SNAPSHOT}.csv"
    rows = golden_rows(folder)
    rows[0]["valid"], rows[0]["invalid_reason"] = "false", "no trade today"
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    items = {i["name"]: i["value"] for i in builder(tmp_path).build(DAY, CUTOFF).body["items"]}
    assert items["quote_counts"]["valid_contracts"] == sum(r["valid"] == "true" for r in rows) == len(rows) - 1


def test_a_chain_the_sidecar_names_without_rows_gets_an_item_with_no_value(tmp_path):
    """Judge 118 addendum 2, minor 2: the chain list is the sidecar's `expiries` (rows as the fallback)."""
    folder = snapshot_folder(tmp_path)
    meta_path = folder / f"{SNAPSHOT}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["expiries"] = sorted({r["expiry"] for r in golden_rows(folder)} | {"2026-12-29"})
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    items = {i["name"]: i["value"] for i in builder(tmp_path).build(DAY, CUTOFF).body["items"]}
    assert items["spot:2026-12-29"] is None and all(items[f"spot:{e}"] for e in meta["expiries"][:-1])
