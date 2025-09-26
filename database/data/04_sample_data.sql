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
