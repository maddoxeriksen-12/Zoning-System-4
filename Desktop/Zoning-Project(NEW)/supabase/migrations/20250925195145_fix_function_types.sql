-- Fix function return types
-- Drop and recreate get_document_stats with correct return types

DROP FUNCTION IF EXISTS get_document_stats();

CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents BIGINT,
    processed_documents BIGINT,
    failed_documents BIGINT,
    total_size NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_documents,
        COUNT(*) FILTER (WHERE processing_status = 'completed') as processed_documents,
        COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_documents,
        COALESCE(SUM(file_size), 0) as total_size
    FROM documents;
END;
$$ LANGUAGE plpgsql;
