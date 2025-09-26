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
