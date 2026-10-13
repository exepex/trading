"""Story P6 criterion 3: publishing is atomic per session (a failure in any block leaves the previous session's blocks
current and unchanged), idempotent, and what is read back is what was published; for the local folder and for the
Postgres `fno` schema (a throwaway PostgreSQL server with db/fno/migrations)."""

import hashlib
from datetime import date

import psycopg
import pytest

from fno.market_read_models.local_publisher import LocalFolderPublisher
from fno.market_read_models.postgres_publisher import PostgresPublisher
from fno.market_read_models.publication import Publication, canonical, hashes
from fno.market_read_models.publisher import PublishFailed

PAGES = ("screener_summary", "screener_stocks", "overview_indices")


def publication(day: date, value: int, page_keys=PAGES) -> Publication:
    publication_id = f"nse-{day}-test{value}"
    records = {}
    for page_key in page_keys:
        payload = {"value": value, "page": page_key, "rows": [{"p": 1.5 * value}]}
        records[page_key] = {
            "market": "india", "page_key": page_key, "as_of": day.isoformat(), "cutoff": f"{day}T12:30:00Z",
            "built_at": f"{day}T12:30:00Z", "schema_version": "2.4.0", "source_commit": "a" * 40,
            "payload_sha256": hashlib.sha256(canonical(payload)).hexdigest(), "product": "fno",
            "publication_id": publication_id, "payload": payload,
        }  # fmt: skip
    return Publication(day, publication_id, records)


FIRST, SECOND = publication(date(2026, 10, 9), 1), publication(date(2026, 10, 12), 2)


class FailsOnThirdBlock(LocalFolderPublisher):
    def __init__(self, folder):
        super().__init__(folder)
        self.written = 0

    def write_record(self, path, record):
        self.written += 1
        if self.written == 3:
            raise OSError("disk full (test)")
        super().write_record(path, record)


def test_the_local_folder_publishes_all_blocks_at_once_and_reads_them_back(tmp_path):
    publisher = LocalFolderPublisher(tmp_path)
    assert publisher.current() == {}
    assert publisher.publish(FIRST) == 3 and publisher.publish(FIRST) == 0
    assert publisher.current() == FIRST.records and publisher.stored(FIRST.publication_id) == hashes(FIRST)
    publisher.publish(SECOND)
    assert publisher.current() == SECOND.records


def test_a_local_failure_part_way_leaves_the_previous_session_current_and_unchanged(tmp_path):
    LocalFolderPublisher(tmp_path).publish(FIRST)
    failing = FailsOnThirdBlock(tmp_path)
    with pytest.raises(PublishFailed):
        failing.publish(SECOND)
    assert failing.written == 3 and LocalFolderPublisher(tmp_path).current() == FIRST.records
    assert not (tmp_path / "publications" / SECOND.publication_id).exists()  # no partial publication left
    LocalFolderPublisher(tmp_path).publish(SECOND)  # a later retry works
    assert LocalFolderPublisher(tmp_path).current() == SECOND.records


def test_the_same_publication_again_changes_nothing_and_a_different_one_under_its_id_is_refused(tmp_path):
    publisher = LocalFolderPublisher(tmp_path)
    publisher.publish(FIRST)
    publisher.publish(FIRST)
    changed = Publication(FIRST.day, FIRST.publication_id, SECOND.records)
    with pytest.raises(PublishFailed):
        publisher.publish(changed)
    assert publisher.current() == FIRST.records


def clean(postgres):
    with psycopg.connect(postgres.url, autocommit=True) as connection:
        connection.execute("truncate fno.pages_history, fno.current_publication")


def stored_rows(postgres) -> int:
    with psycopg.connect(postgres.url) as connection:
        return connection.execute("select count(*) from fno.pages_history").fetchone()[0]


def test_postgres_publishes_all_blocks_in_one_transaction_and_reads_them_back(postgres):
    clean(postgres)
    publisher = PostgresPublisher(postgres.url)
    assert publisher.current() == {}
    publisher.publish(FIRST)
    assert publisher.current() == FIRST.records
    publisher.publish(SECOND)
    assert publisher.current() == SECOND.records and stored_rows(postgres) == 6  # history kept, pointer moved


def test_a_postgres_failure_in_any_block_leaves_the_previous_session_current_and_unchanged(postgres):
    clean(postgres)
    publisher = PostgresPublisher(postgres.url)
    publisher.publish(FIRST)
    broken = publication(date(2026, 10, 12), 3)
    broken.records["overview_indices"]["payload_sha256"] = "not a sha"  # the third insert fails (check constraint)
    with pytest.raises(PublishFailed) as failed:
        publisher.publish(broken)
    assert "CheckViolation" in str(failed.value) and postgres.url not in str(failed.value)
    assert publisher.current() == FIRST.records and stored_rows(postgres) == 3  # the first two inserts rolled back


def pointer_time(postgres):
    with psycopg.connect(postgres.url) as connection:
        return connection.execute("select published_at from fno.current_publication").fetchone()[0]


def test_postgres_publishing_the_same_session_twice_adds_no_rows(postgres):
    clean(postgres)
    publisher = PostgresPublisher(postgres.url)
    assert publisher.publish(FIRST) == 3
    published_at = pointer_time(postgres)
    rerun = Publication(FIRST.day, FIRST.publication_id, {k: {**r, "built_at": f"{FIRST.day}T23:59:00Z"}
                                                          for k, r in FIRST.records.items()})  # fmt: skip
    assert publisher.publish(rerun) == 0 and pointer_time(postgres) == published_at  # a later run: nothing changes
    assert stored_rows(postgres) == 3 and publisher.current() == FIRST.records
    assert publisher.stored(FIRST.publication_id) == hashes(FIRST)  # read back with the publisher's own role
    changed = Publication(FIRST.day, FIRST.publication_id, publication(FIRST.day, 9).records)
    for record in changed.records.values():
        record["publication_id"] = FIRST.publication_id
    with pytest.raises(PublishFailed, match="stored pages differ"):
        publisher.publish(changed)
    assert publisher.current() == FIRST.records
