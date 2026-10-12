# NIFTY capacity screen (2024-2026)

Would a NIFTY debit spread have fitted the risk cap on each trading day? Agreed in ChatGPT review 4 and Claude
response 3. **No strategy and no profit or loss**: only whether a trade would have been admissible, by direction.

## Commands (from the repository root)

```
python research/2026-10-12-capacity-screen/fetch.py   # NSE daily F&O files -> data/ (one request a second, resumable)
python research/2026-10-12-capacity-screen/screen.py  # screen.csv and summary.md
python -m pytest -q tests/research                    # the screen's rules as fixtures
```

## Data

- NSE daily F&O files in the UDiFF format, `BhavCopy_NSE_FO_0_0_0_<yyyymmdd>_F_0000.csv.zip`, from 1 Jan 2024 to
  9 Oct 2026. NSE serves this format for every date from January 2024 (checked: 2 Jan 2024 is available, 2023 is
  not), so no legacy-format file is used and no underlying-price or lot-size join is needed.
- `data/manifest.csv`: every weekday asked for, its URL, HTTP status (404 = no file: market closed) and the SHA-256
  of the ZIP bytes.
- `data/nifty_options.csv.gz`: only NIFTY option rows 20-55 calendar days to expiry with strikes within 1,500
  points of the underlying (enough for the screen; the full files are not stored).
- Fields kept: close, previous close, settlement price, underlying price, volume, number of trades, open interest,
  historical lot size. **No bid/ask** in these files.

## Rules (frozen before the run)

| Rule | Value |
|---|---|
| Expiry | The month's last listed expiry, 30-45 calendar days away; none in range = `no_eligible_expiry` (never forced) |
| Strike | Nearest listed strike to the underlying close; a tie goes to the lower strike |
| Spreads | Bull call: buy that strike, sell the strike `width` above. Bear put: buy that strike, sell `width` below. Widths 50 / 100 / 200 |
| Price | The day's closing price of each leg (`ClsPric`); settlement price kept but not used as a fill |
| Usable price | Positive price and volume > 0 on both legs on that day; a minimum, not proof of a fresh or tradable price |
| Anomaly | Debit not between 0 and the width = `nonsynchronous_price_anomaly` (not repaired, not admitted) |
| Quantity | Today's NIFTY lot, 65 (a labelled counterfactual for older dates; the historical lot is recorded) |
| Charges | Today's Groww/NSE charges (frozen `research/2026-10-12-backtest/inputs/config.yaml`, STT 0.15% on sales) |
| Pad | One-way adverse price pad per leg per order: Rs 0, 0.50, 1, 2 (assumptions, not measured costs) |
| Admission | Padded entry debit (long - short + 2 x pad) x lot + entry charges on padded prices + exit-charge reserve at entry prices padded adversely + remaining exit pads 2 x pad x lot. The four orders carry 4 x pad x lot of padding in total, counted once |
| Profiles | Reference Rs 2 lakh at 1% (Rs 2,000); sensitivities Rs 2 lakh at 2% (Rs 4,000) and Rs 5 lakh at 1% (Rs 5,000) |

Every day and spread gets one status: `priced`, `no_eligible_expiry`, `contract_unavailable`,
`missing_required_leg`, `invalid_price`, `zero_volume_price_unusable` or `nonsynchronous_price_anomaly`. Missing
or unusable prices are never counted as a failure of the risk cap.

## Limits

Closing prices of two legs are not one simultaneous executable quote; the exit-charge reserve is a stated
assumption, not a worst case; the pads are not calibrated to real bid/ask. This screen shows how often each spread
fits under these assumptions; it says nothing about profit.
