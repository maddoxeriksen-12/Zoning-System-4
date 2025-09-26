-- Clean up duplicate documents and requirements
-- Run this in Supabase SQL Editor

-- Step 1: Identify and remove duplicate documents (keep the latest one)
WITH duplicate_docs AS (
    SELECT 
        original_filename,
        COUNT(*) as count,
        ARRAY_AGG(id ORDER BY created_at DESC) as doc_ids
    FROM documents 
    WHERE original_filename IS NOT NULL
    GROUP BY original_filename
    HAVING COUNT(*) > 1
),
docs_to_delete AS (
    SELECT UNNEST(doc_ids[2:]) as id_to_delete
    FROM duplicate_docs
)
-- Delete older duplicate documents (this will cascade to requirements due to foreign key)
DELETE FROM documents 
WHERE id IN (SELECT id_to_delete FROM docs_to_delete);

-- Step 2: Clean up orphaned requirements (just in case)
DELETE FROM requirements 
WHERE job_id NOT IN (SELECT id FROM jobs);

-- Step 3: Clean up orphaned jobs  
DELETE FROM jobs
WHERE id NOT IN (
    SELECT DISTINCT job_id 
    FROM requirements 
    WHERE job_id IS NOT NULL
    UNION
    SELECT id FROM jobs WHERE processing_status = 'pending'
);

-- Step 4: Show cleanup results
SELECT 
    'documents' as table_name,
    COUNT(*) as remaining_records
FROM documents
UNION ALL
SELECT 
    'jobs' as table_name,
    COUNT(*) as remaining_records  
FROM jobs
UNION ALL
SELECT 
    'requirements' as table_name,
    COUNT(*) as remaining_records
FROM requirements
ORDER BY table_name;
