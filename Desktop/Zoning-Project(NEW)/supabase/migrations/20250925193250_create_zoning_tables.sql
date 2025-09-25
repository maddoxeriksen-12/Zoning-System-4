-- Core database schema for Zoning Project
-- Documents table for storing uploaded zoning documents

-- UUID extension should already be available in Supabase
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    municipality VARCHAR(255),
    state VARCHAR(50) DEFAULT 'NJ',
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'uploaded', -- uploaded, processing, completed, failed
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    grok_response TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_municipality ON documents(municipality);
CREATE INDEX IF NOT EXISTS idx_documents_state ON documents(state);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- RPC Functions for Zoning Project
-- Database functions for document processing and retrieval

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents BIGINT,
    processed_documents BIGINT,
    failed_documents BIGINT,
    total_size BIGINT
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
-- Row Level Security Policies for Zoning Project
-- Note: These are kept for compatibility but may not be needed for local PostgreSQL

-- Enable RLS on documents table (optional for local development)
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy to allow all operations for local development
-- CREATE POLICY "Allow all operations on documents" ON documents
--     FOR ALL USING (true);

-- If you want to enable RLS in the future, uncomment and modify these policies:
-- CREATE POLICY "Users can view all documents" ON documents FOR SELECT USING (true);
-- CREATE POLICY "Users can insert their own documents" ON documents FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Users can update their own documents" ON documents FOR UPDATE USING (true);
-- Sample data for Zoning Project
-- Insert some test documents for development

INSERT INTO documents (
    filename,
    original_filename,
    file_path,
    file_size,
    mime_type,
    municipality,
    state,
    processing_status
) VALUES
(
    'sample_zoning_doc_001.pdf',
    'Sample Zoning Document.pdf',
    '/app/uploads/sample_zoning_doc_001.pdf',
    1024000,
    'application/pdf',
    'Test Municipality',
    'NJ',
    'completed'
),
(
    'monmouth_county_zoning_2024.pdf',
    'Monmouth County Zoning 2024.pdf',
    '/app/uploads/monmouth_county_zoning_2024.pdf',
    2048000,
    'application/pdf',
    'Monmouth County',
    'NJ',
    'processing'
)
ON CONFLICT DO NOTHING;
