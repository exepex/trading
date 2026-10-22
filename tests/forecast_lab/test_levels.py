"""FL1-1d-2: the evening's levels and flows, the day's own files only: the nearest expiry's PCR (and the previous
session's), the call and put walls and max pain from the F&O bhavcopy; for NIFTY, FII and DII cash and FIIs' net
index futures. A file not out yet is "not out yet", never an older value as the day's."""

from datetime import date

from fno.forecast_lab.sections.levels import NOT_OUT, Levels, nearest_chain

TUE, WED = date(2026, 10, 20), date(2026, 10, 21)
NEAR, FAR = "2026-10-27", "2026-11-25"


def row(strike, kind, oi, expiry=NEAR, symbol="NIFTY", instrument="IDO"):
    return {"TckrSymb": symbol, "FinInstrmTp": instrument, "OptnTp": kind, "StrkPric": str(strike),
            "OpnIntrst": str(oi), "XpryDt": expiry}  # fmt: skip


ROWS = [row(22000, "PE", 900), row(22500, "PE", 300), row(23000, "CE", 1000), row(22500, "CE", 200),
        row(24000, "CE", 5000, expiry=FAR), row(22000, "CE", 99, symbol="BANKNIFTY"),
        row(0, "XX", 1, instrument="IDF")]  # fmt: skip


def test_the_nearest_expiry_chain_keeps_only_that_expiry_s_options_with_their_oi():
    expired = [row(21000, "PE", 99999, expiry="2026-10-20")]  # expired the day before: never the nearest
    chain = nearest_chain("NIFTY", WED, ROWS + expired)
    assert chain.expiry == date(2026, 10, 27) and sorted(chain.quotes) == [
        (22000.0, "PE"), (22500.0, "CE"), (22500.0, "PE"), (23000.0, "CE")]  # fmt: skip
    assert nearest_chain("FINNIFTY", WED, ROWS) is None


class Files:
    def __init__(self, days, data=b"rows"):
        self.days, self.data = days, data

    def covers(self, day):
        return True

    def get(self, day):
        return f"fo_{day}.csv", (self.data if day in self.days else None)


def levels(fo_days, flows=None, participant=None, monkeypatch=None):
    monkeypatch.setattr("fno.forecast_lab.sections.levels.read_fo_file", lambda name, data: ROWS)
    return Levels((Files(fo_days),), participant or Files(set()), lambda day: flows or {}, lambda day: TUE)


def test_the_day_s_bhavcopy_gives_pcr_walls_and_max_pain(monkeypatch):
    cues = {c.name: c for c in levels({TUE, WED}, monkeypatch=monkeypatch).levels("BANKNIFTY", WED)}
    assert set(cues) == {"PCR", "PCR (previous session)", "Call wall", "Put wall", "Max pain"}
    assert (cues["PCR"].value, cues["Put wall"].text, cues["Call wall"].value) == (0.0, "none in the file", 22000.0)
    nifty = {c.name: c for c in levels({TUE, WED}, monkeypatch=monkeypatch).levels("NIFTY", WED)}
    assert (nifty["PCR"].value, nifty["PCR"].as_of) == (1.0, WED)  # 1,200 put OI over 1,200 call OI
    assert (nifty["Call wall"].value, nifty["Put wall"].value, nifty["Max pain"].value) == (23000.0, 22000.0, 22500.0)
    assert nifty["PCR (previous session)"].as_of == TUE


def test_files_not_out_yet_are_said_so_never_an_older_day_s(monkeypatch):
    nifty = {c.name: c for c in levels({TUE}, monkeypatch=monkeypatch).levels("NIFTY", WED)}
    assert all(nifty[n].text == NOT_OUT and nifty[n].value is None for n in ("PCR", "Call wall", "Max pain"))
    assert nifty["FII cash (Rs crore)"].text == NOT_OUT and nifty["FII index futures (net contracts)"].text == NOT_OUT


def test_nifty_carries_the_day_s_flows_only(monkeypatch):
    flows = {TUE: (-500.0, 700.0), WED: (1022.32, 1614.32)}
    nifty = {c.name: c for c in levels({WED}, flows=flows, monkeypatch=monkeypatch).levels("NIFTY", WED)}
    assert (nifty["FII cash (Rs crore)"].value, nifty["DII cash (Rs crore)"].value) == (1022.32, 1614.32)
    stale = {c.name: c for c in levels({WED}, flows={TUE: (1.0, 2.0)}, monkeypatch=monkeypatch).levels("NIFTY", WED)}
    assert stale["FII cash (Rs crore)"].text == NOT_OUT
