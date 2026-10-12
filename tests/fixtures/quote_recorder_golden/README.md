# Quote recorder baseline (clean-slate criterion 9)

Written by the recorder **before** the old desk was removed (commit 184ff7e9acca6fd1b47598f69fbac5bb1b3b5914, then
`fno/live/quote_recorder.py`), from the four fixed scenarios in `tests/quotes/test_recorder_baseline.py`: a normal day,
an incomplete attempt then a retry, a day with no complete attempt ("none"), and December with the NSE expiry
fallback. The test re-runs the same scenarios with the moved recorder and requires identical bytes. Never edit these
files: a real change of output format needs a new, reviewed baseline.
