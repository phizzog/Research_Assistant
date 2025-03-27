-- Get list of all tables
SELECT 
    table_schema,
    table_name
FROM 
    information_schema.tables
WHERE 
    table_schema NOT IN ('pg_catalog', 'information_schema')
    AND table_type = 'BASE TABLE'
ORDER BY 
    table_schema, table_name;

-- Get detailed information about the 'sources' table (columns and data types)
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'sources'
ORDER BY 
    ordinal_position;

-- Get all PostgreSQL functions (stored procedures)
SELECT 
    n.nspname as schema_name,
    p.proname as function_name,
    pg_get_function_arguments(p.oid) as function_arguments,
    CASE 
        WHEN l.lanname = 'internal' THEN 'SQL'
        ELSE l.lanname
    END as language,
    CASE 
        WHEN p.provolatile = 'i' THEN 'IMMUTABLE'
        WHEN p.provolatile = 's' THEN 'STABLE'
        WHEN p.provolatile = 'v' THEN 'VOLATILE'
    END as volatility
FROM 
    pg_proc p
LEFT JOIN 
    pg_namespace n ON p.pronamespace = n.oid
LEFT JOIN 
    pg_language l ON p.prolang = l.oid
WHERE 
    n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY 
    schema_name, function_name;

-- Get all triggers in the database
SELECT 
    t.tgname as trigger_name,
    c.relname as table_name,
    n.nspname as schema_name,
    CASE 
        WHEN t.tgtype & 1 = 1 THEN 'ROW' 
        ELSE 'STATEMENT' 
    END as trigger_level,
    CASE 
        WHEN t.tgtype & 2 = 2 THEN 'BEFORE' 
        WHEN t.tgtype & 64 = 64 THEN 'INSTEAD OF' 
        ELSE 'AFTER' 
    END as trigger_timing,
    CASE 
        WHEN t.tgtype & 4 = 4 THEN 'INSERT' 
        WHEN t.tgtype & 8 = 8 THEN 'DELETE' 
        WHEN t.tgtype & 16 = 16 THEN 'UPDATE' 
        WHEN t.tgtype & 28 = 28 THEN 'INSERT, DELETE, UPDATE'
        WHEN t.tgtype & 20 = 20 THEN 'INSERT, UPDATE' 
        WHEN t.tgtype & 12 = 12 THEN 'INSERT, DELETE' 
        WHEN t.tgtype & 24 = 24 THEN 'DELETE, UPDATE' 
    END as trigger_events,
    pg_get_functiondef(p.oid) as trigger_function
FROM 
    pg_trigger t
JOIN 
    pg_class c ON t.tgrelid = c.oid
JOIN 
    pg_namespace n ON c.relnamespace = n.oid
JOIN 
    pg_proc p ON t.tgfoid = p.oid
WHERE 
    NOT t.tgisinternal
    AND n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY 
    schema_name, table_name, trigger_name;

-- Get Row Level Security (RLS) policies that might affect the sources table
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM 
    pg_policies
WHERE 
    tablename = 'sources';

-- Check if there are any constraints on the sources table (like primary keys, unique)
SELECT 
    con.conname as constraint_name,
    con.contype as constraint_type,
    rel.relname as table_name,
    att.attname as column_name
FROM 
    pg_constraint con
JOIN 
    pg_class rel ON rel.oid = con.conrelid
JOIN 
    pg_namespace nsp ON nsp.oid = rel.relnamespace
JOIN 
    pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
WHERE 
    rel.relname = 'sources'
    AND nsp.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY 
    constraint_name, column_name;

-- Get vector extension information
SELECT
    name,
    default_version,
    installed_version
FROM
    pg_available_extensions
WHERE
    name = 'pgvector';

-- Get information about match_chunks function (if it exists)
SELECT
    pg_get_functiondef(oid)
FROM
    pg_proc
WHERE
    proname = 'match_chunks'; 