-- Run with psql as a database administrator connected to gradcafe.
-- psql prompts privately for the new role password.
\set ON_ERROR_STOP on
CREATE ROLE gradcafe_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;
\password gradcafe_app
GRANT CONNECT ON DATABASE gradcafe TO gradcafe_app;
GRANT USAGE ON SCHEMA public TO gradcafe_app;
GRANT SELECT, INSERT ON TABLE public.applicants TO gradcafe_app;
GRANT USAGE ON SEQUENCE public.applicants_p_id_seq TO gradcafe_app;

-- The app reads for analysis and inserts new records through Pull Data.
-- It owns no objects and receives no CREATE, ALTER, DROP, UPDATE, DELETE,
-- or SUPERUSER privilege. Use a separate administrator role for schema setup.
