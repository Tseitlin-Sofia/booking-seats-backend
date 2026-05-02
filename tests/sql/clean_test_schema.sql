DO $$
DECLARE
    table_row RECORD;
BEGIN
    SET CONSTRAINTS ALL DEFERRED;

    FOR table_row IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'test'
          AND tablename NOT LIKE 'alembic%'
    LOOP
        EXECUTE format('TRUNCATE TABLE test.%I CASCADE', table_row.tablename);
    END LOOP;

    FOR table_row IN
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'test'
    LOOP
        EXECUTE format('ALTER SEQUENCE test.%I RESTART WITH 1', table_row.sequence_name);
    END LOOP;

    RAISE NOTICE 'Test schema cleaned successfully';
END;
$$;
