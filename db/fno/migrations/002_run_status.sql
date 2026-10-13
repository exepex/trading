-- The fno schema's run-status table (story P7; P3 named it; the W11 catalog's source for the dashboard's bell, W8).
-- One row per product and publish run, written by the runtime publisher role: `running` at the start, then
-- `published`, `failed` (with a reason code) or `skipped` (not a session) at the end. Rows are never deleted; a run
-- that crashed without finishing stays `running` (the dashboard treats a `running` row older than the run's time limit
-- as a run that did not report). Run by the migration role (fno_owner), like 001.

create table if not exists fno.run_status (
    product         text        not null,
    run_id          text        not null,
    session         date        not null,
    started_at      timestamptz not null,
    finished_at     timestamptz,
    result          text        not null check (result in ('running', 'published', 'failed', 'skipped')),
    reason_code     text        check (reason_code is null or reason_code in (
                        'not_a_session', 'archive_incomplete', 'contract_changed', 'schema_invalid', 'publish_refused',
                        'read_back_mismatch', 'database_network', 'database_firewall', 'database_tls',
                        'database_authentication', 'database_privilege', 'database_other', 'crashed')),
    reason          text,
    publication_id  text,
    primary key (product, run_id),
    check ((result = 'running') = (finished_at is null)),
    check ((result in ('failed', 'skipped')) = (reason_code is not null))
);

create index if not exists run_status_latest on fno.run_status (product, started_at desc);

grant select, insert, update on fno.run_status to fno_writer;  -- no delete: the history stays
grant select on fno.run_status to dashboard_app;
