"""Story A14 on the moved table (O9b step 2: the margins table in Drive with receipts, read here from the verified
cache after `python -m fno data-cache sync data/margins`): A14's columns, one figure per structure, width and day, and
every computed row naming the SPAN file whose SHA-256 is its manifest row."""

import pytest

from fno.constants import MARGIN_SOURCE_NSE_SPAN
from fno.risk.margins import MARGIN_COLUMNS
from fno.storage import wiring as storage
from fno.storage.raw_source import NseSpanBodSource
from fno.storage.receipted_rows import ReceiptedRowLog
from tests.data_cache import cached_series

pytestmark = pytest.mark.data


@pytest.fixture(scope="module")
def table():
    return cached_series(ReceiptedRowLog, "margins/margins")


def test_the_table_has_a14s_columns_and_one_figure_per_structure_width_and_day(table):
    assert table.rebuilt().decode("utf-8").splitlines()[0] == ",".join(MARGIN_COLUMNS)
    keys = [(r["structure"], float(r["width"]), r["as_of"]) for r in table.rows()]
    assert keys and len(keys) == len(set(keys))


def test_every_computed_row_names_its_span_file_and_the_manifests_sha256(table):
    manifest = {f.sha256 for f in storage.build_manifest_folder().read(NseSpanBodSource)}
    computed = [r for r in table.rows() if r["source"].startswith(MARGIN_SOURCE_NSE_SPAN)]
    assert computed
    for row in computed:
        assert row["source"].rsplit("sha256=", 1)[1] in manifest, (row["structure"], row["width"], row["as_of"])
