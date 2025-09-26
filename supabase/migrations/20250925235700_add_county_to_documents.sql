-- Add county column to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS county VARCHAR(255);

-- Update the index to include county
DROP INDEX IF EXISTS idx_documents_municipality_state;
CREATE INDEX IF NOT EXISTS idx_documents_municipality_county_state 
ON documents(municipality, county, state);
