DO $$
BEGIN
    CREATE SCHEMA IF NOT EXISTS test;

    DECLARE
        table_row RECORD;
    BEGIN
        FOR table_row IN
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename NOT LIKE 'alembic%'
        LOOP
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS test.%I (
                    LIKE public.%I INCLUDING DEFAULTS INCLUDING CONSTRAINTS
                )
            ', table_row.tablename, table_row.tablename);
        END LOOP;
    END;
END;
$$;
