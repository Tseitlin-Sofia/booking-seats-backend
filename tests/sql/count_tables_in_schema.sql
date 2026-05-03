SELECT COUNT(*)
FROM pg_tables
WHERE schemaname = :schema_name
