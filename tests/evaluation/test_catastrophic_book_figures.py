"""S1 item 13: `catastrophic_loss_book` states the books' risk figures that `config.yaml` applies (owner, 15 Oct 2026),
so an edit of one alone fails before a freeze."""

from fno.config import ROOT, load_config
from fno.evaluation.protocol import PROTOCOL_FILE, parse_protocol


def rupees(amount: float) -> str:
    """Indian grouping, as the protocol writes it: 120000 -> "Rs 1,20,000"."""
    digits = str(int(amount))
    head, tail = digits[:-3], digits[-3:]
    groups = [head[max(i - 2, 0) : i] for i in range(len(head), 0, -2)][::-1]
    return "Rs " + ",".join([*groups, tail]) if head else f"Rs {tail}"


def test_the_catastrophic_rule_states_the_books_config_figures():
    text = parse_protocol((ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")).items["catastrophic_loss_book"].value
    books = load_config()["risk"]["profiles"]["books"]
    for key in ("drawdown_brake_rs", "bucket_cap_rs", "open_risk_cap_rs", "new_risk_per_day_rs"):
        assert rupees(books[key]) in text, key
    assert "max_open_trades" not in books["rules"] and "Rs 30,000 or more below" not in text


def test_rupees_groups_the_indian_way():
    assert [rupees(x) for x in (30000, 120000, 150000, 2000000)] == ["Rs 30,000", "Rs 1,20,000", "Rs 1,50,000",
                                                                     "Rs 20,00,000"]  # fmt: skip
