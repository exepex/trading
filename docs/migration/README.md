# Owner's hands-on steps: Azure PostgreSQL and the shared dashboard

Companion to `docs/MIGRATION_PLAN.md` (the why and the order). These are the clicks and commands for the owner.
**Never paste a password, token or connection string into a chat, a file or a commit**; keep them in a password
manager and enter them only into the Azure portal, psql, Vercel settings or a cloud environment's settings.

## Environment variable names (fixed now, so the code uses the same names)

| Name | Holds | Set where | When |
|---|---|---|---|
| `OMENIX_DB_URL` | `dashboard_app` connection URL | Vercel projects (staging, later production) | when the Azure read path (W2, W6) is deployed |
| `FNO_DB_URL` | `fno_writer` connection URL | this repository's cloud environment | when the F&O publisher (P3) is ready |
| `STOCK_DB_URL` | `stock_writer` connection URL | the stock tool's cloud environment | when its Azure writer (K1) is ready |
| `STOCK_INBOX_DB_URL` | `stock_inbox_reader` connection URL | the stock tool's cloud environment | when K3 is ready |

Owner roles (`stock_owner`, `fno_owner`, `app_owner`) are never stored in any app or routine environment: they are
used only by the owner from Azure Cloud Shell to run table migrations that sessions prepare as SQL files.

URL format (use long passwords of letters and digits only, so nothing needs URL-encoding):
`postgresql://<role>:<password>@<server>.postgres.database.azure.com:5432/omenix?sslmode=verify-full`

Steps A (Azure), B (repository and staging), C (after code), D (cutover) and E (clean-up) are in the conversation
log of 12 Oct 2026 and summarised in `docs/MIGRATION_PLAN.md`; `azure_setup.sql` is the script for step A7.

## Tested (12 Oct 2026)

`azure_setup.sql` was run on a local PostgreSQL 16.15 as a non-superuser admin with only `CREATEDB` and `CREATEROLE`
(like Azure's admin). Role matrix: the three owner roles could create tables in their own schema; 8 allowed runtime
actions succeeded (writers insert and update their own schema, the dashboard reads both schemas and inserts into
`app`, the inbox reader reads `app`); 15 forbidden actions were refused (create, drop or alter tables, writing or
reading another tool's schema, creating in `public`, temporary tables, the dashboard deleting rows, the inbox reader
writing, a writer switching to its owner role).
