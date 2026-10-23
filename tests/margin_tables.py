"""A14's margins table on a local file for tests (story O9b step 2: the wired table is a receipt-backed Drive series,
read through `fno.storage.data_wiring.build_data_table`)."""

from fno.storage.table_source import FileTable


def local_tables(path):
    """`build_risk_manager(..., tables=local_tables(path))`: every table name reads `path`."""
    return lambda name: FileTable(path)
