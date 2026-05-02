SELECT COUNT(*) > 0 AS has_tables
FROM pg_tables
WHERE schemaname = 'test'
