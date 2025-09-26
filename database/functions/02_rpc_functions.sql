-- RPC Functions for Zoning Project
-- Database functions for document processing and retrieval

-- Function to get document statistics
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

-- Function to update document processing status
CREATE OR REPLACE FUNCTION update_document_status(
    p_document_id UUID,
    p_status VARCHAR(50),
    p_grok_response TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE documents
    SET
        processing_status = p_status,
        grok_response = COALESCE(p_grok_response, grok_response),
        error_message = COALESCE(p_error_message, error_message),
        processing_completed_at = CASE WHEN p_status IN ('completed', 'failed') THEN NOW() ELSE processing_completed_at END,
        updated_at = NOW()
    WHERE id = p_document_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to mark processing started
CREATE OR REPLACE FUNCTION start_document_processing(p_document_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE documents
    SET
        processing_status = 'processing',
        processing_started_at = NOW(),
        updated_at = NOW()
    WHERE id = p_document_id
    AND processing_status = 'uploaded';

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
