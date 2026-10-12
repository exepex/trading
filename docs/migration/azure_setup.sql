-- Azure Database for PostgreSQL (Flexible Server, PostgreSQL 16): database, schemas and least-privilege roles for the
-- shared dashboard (design 13.3, story X1). Run in psql as the server admin. No passwords in this file: after running
-- it, set each role's password interactively with \password (see docs/migration/README.md step A8).
-- Safe to read before running; run it once on a new server.

-- Run the whole file at once:  psql "host=<server>.postgres.database.azure.com port=5432 dbname=postgres user=<admin> sslmode=require" -f azure_setup.sql
-- (psql may ask for the admin password twice: once to connect, once when it switches to the new database).
CREATE DATABASE omenix;
\c omenix
-- Nobody gets anything by default.
REVOKE ALL ON DATABASE omenix FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Owner roles: create and change tables. Used only to run migrations by hand, never by a running app or routine.
CREATE ROLE stock_owner LOGIN;
CREATE ROLE fno_owner LOGIN;
CREATE ROLE app_owner LOGIN;

-- Runtime roles: what the apps and routines use.
CREATE ROLE stock_writer LOGIN CONNECTION LIMIT 5;        -- stock routines: write the stock read models
CREATE ROLE fno_writer LOGIN CONNECTION LIMIT 5;          -- F&O routine: write the F&O read models
CREATE ROLE dashboard_app LOGIN CONNECTION LIMIT 20;      -- the dashboard: read stock and fno, write its own app tables
CREATE ROLE stock_inbox_reader LOGIN CONNECTION LIMIT 5;  -- stock routines: read the dashboard inbox

ALTER ROLE stock_writer SET statement_timeout = '60s';
ALTER ROLE fno_writer SET statement_timeout = '60s';
ALTER ROLE dashboard_app SET statement_timeout = '15s';
ALTER ROLE stock_inbox_reader SET statement_timeout = '30s';

GRANT CONNECT ON DATABASE omenix
  TO stock_owner, fno_owner, app_owner, stock_writer, fno_writer, dashboard_app, stock_inbox_reader;

-- Let the admin act as each owner role (needed to create their schemas), without inheriting their rights.
GRANT stock_owner, fno_owner, app_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA stock AUTHORIZATION stock_owner;
CREATE SCHEMA fno AUTHORIZATION fno_owner;
CREATE SCHEMA app AUTHORIZATION app_owner;

-- Each owner grants, on its own schema, exactly what the runtime roles need, for every table it creates later.
SET ROLE stock_owner;
GRANT USAGE ON SCHEMA stock TO stock_writer, dashboard_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA stock GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO stock_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA stock GRANT USAGE, SELECT ON SEQUENCES TO stock_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA stock GRANT SELECT ON TABLES TO dashboard_app;
RESET ROLE;

SET ROLE fno_owner;
GRANT USAGE ON SCHEMA fno TO fno_writer, dashboard_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fno_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno GRANT USAGE, SELECT ON SEQUENCES TO fno_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA fno GRANT SELECT ON TABLES TO dashboard_app;
RESET ROLE;

SET ROLE app_owner;
GRANT USAGE ON SCHEMA app TO dashboard_app, stock_inbox_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT, INSERT, UPDATE ON TABLES TO dashboard_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE, SELECT ON SEQUENCES TO dashboard_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO stock_inbox_reader;
RESET ROLE;

-- Check: list roles and schemas.
\du
\dn+
