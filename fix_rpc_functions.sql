-- Fix RPC function overloading issue by dropping conflicting versions and creating the correct one

-- Drop all conflicting versions of create_job
DROP FUNCTION IF EXISTS public.create_job(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BIGINT);
DROP FUNCTION IF EXISTS public.create_job(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, BIGINT);
DROP FUNCTION IF EXISTS public.create_job(VARCHAR(255), VARCHAR(255), VARCHAR(2), VARCHAR(500), VARCHAR(500), TEXT, BIGINT);

-- Create the correct version with TEXT for file path
CREATE OR REPLACE FUNCTION public.create_job(
    p_town VARCHAR(255),
    p_county VARCHAR(255),
    p_state VARCHAR(2),
    p_pdf_filename VARCHAR(500),
    p_original_pdf_filename VARCHAR(500),
    p_pdf_file_path TEXT,  -- TEXT for unlimited length
    p_pdf_file_size BIGINT
)
RETURNS UUID AS $$
DECLARE
    new_job_id UUID;
BEGIN
    INSERT INTO jobs (
        town, county, state, 
        pdf_filename, original_pdf_filename, 
        pdf_file_path, pdf_file_size, 
        processing_status, created_at, updated_at
    )
    VALUES (
        p_town, p_county, p_state, 
        p_pdf_filename, p_original_pdf_filename, 
        p_pdf_file_path, p_pdf_file_size, 
        'pending', NOW(), NOW()
    )
    RETURNING id INTO new_job_id;
    
    RETURN new_job_id;
END;
$$ LANGUAGE plpgsql;

-- Verify the function exists correctly
SELECT proname, pg_get_function_arguments(oid) 
FROM pg_proc 
WHERE proname = 'create_job';
