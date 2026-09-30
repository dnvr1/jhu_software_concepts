-- Read-only evidence: run against gradcafe after least_privilege.sql.
\set ON_ERROR_STOP on
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole,
       rolreplication, rolbypassrls
FROM pg_roles WHERE rolname = 'gradcafe_app' LIMIT 1;

SELECT has_database_privilege('gradcafe_app', 'gradcafe', 'CONNECT') AS can_connect,
       has_database_privilege('gradcafe_app', 'gradcafe', 'CREATE') AS can_create_schema,
       has_schema_privilege('gradcafe_app', 'public', 'USAGE') AS can_use_schema,
       has_schema_privilege('gradcafe_app', 'public', 'CREATE') AS can_create_objects
LIMIT 1;

SELECT privilege,
       has_table_privilege('gradcafe_app', 'public.applicants', privilege) AS granted
FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE',
                  'TRUNCATE', 'REFERENCES', 'TRIGGER']) AS privilege
LIMIT 7;

SELECT pg_get_userbyid(relowner) AS table_owner,
       pg_has_role('gradcafe_app', relowner, 'MEMBER') AS member_of_owner_role
FROM pg_class WHERE oid = 'public.applicants'::regclass LIMIT 1;
