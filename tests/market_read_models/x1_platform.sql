-- The parts of X1's platform SQL that shape schema fno on Azure (omenix-dashboard platform/sql at 407ead2), so the
-- throwaway server is set up like Azure (judge 59, addendum 1): step 00 (the roles), 20 (schema fno owned by
-- fno_owner), 30 (USAGE for the runtime roles) and step 40's default privileges for fno_owner (every table it creates
-- in fno gives fno_writer SELECT, INSERT, UPDATE, DELETE and dashboard_app SELECT; no function executable by others).
-- Run by the server admin; the migrations then run as fno_owner and the tests act as fno_writer and dashboard_app.
CREATE ROLE stock_owner LOGIN;
CREATE ROLE fno_owner LOGIN;
CREATE ROLE app_owner LOGIN;
CREATE ROLE stock_writer LOGIN;
CREATE ROLE fno_writer LOGIN;
CREATE ROLE dashboard_app LOGIN;
CREATE ROLE stock_inbox_reader LOGIN;
CREATE ROLE db_monitor LOGIN;
CREATE SCHEMA fno AUTHORIZATION fno_owner;
SET ROLE fno_owner;
REVOKE ALL ON SCHEMA fno
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
GRANT USAGE ON SCHEMA fno TO fno_writer, dashboard_app;
ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
ALTER DEFAULT PRIVILEGES REVOKE ALL ON SEQUENCES
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
ALTER DEFAULT PRIVILEGES REVOKE ALL ON FUNCTIONS
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno REVOKE ALL ON TABLES
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno REVOKE ALL ON SEQUENCES
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno REVOKE ALL ON FUNCTIONS
  FROM PUBLIC, stock_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader, db_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fno_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno GRANT USAGE, SELECT ON SEQUENCES TO fno_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno GRANT SELECT ON TABLES TO dashboard_app;
RESET ROLE;
