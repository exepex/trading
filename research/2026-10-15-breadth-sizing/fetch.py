"""Read-only: copy recent UDiFF F&O bhavcopies from the Drive raw archive into a scratch folder."""
import csv, sys, time
from datetime import date
from pathlib import Path
sys.path.insert(0, "/home/user/trading")
from fno.storage.wiring import build_drive_reader
from fno.storage.raw_source import NseDailyFoSource
out = Path(sys.argv[1]); n = int(sys.argv[2])
days = [date.fromisoformat(r["date"]) for r in csv.DictReader(open("/home/user/trading/research/data/manifests/fo-bhavcopy.csv"))]
store = build_drive_reader(); t = time.time(); got = 0
for d in days[-n:]:
    f = out / f"{d}.zip"
    if f.exists(): continue
    data = store.get(NseDailyFoSource.path_for(d))
    if data is None: print("missing", d); continue
    f.write_bytes(data); got += 1
print("fetched", got, "in", round(time.time()-t), "s")
