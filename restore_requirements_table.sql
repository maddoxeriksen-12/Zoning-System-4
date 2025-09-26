-- Restore Requirements Table
-- Copy and run this in Supabase SQL Editor

-- First, create requirements table with all zoning fields
CREATE TABLE IF NOT EXISTS requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,

    -- Jurisdiction identification
    town VARCHAR(255) NOT NULL,
    county VARCHAR(255),
    state VARCHAR(50) NOT NULL,

    -- Zone identification
    zone VARCHAR(255) NOT NULL,

    -- Minimum Lot Size (Interior Lots)
    interior_min_lot_area_sqft NUMERIC,
    interior_min_lot_frontage_ft NUMERIC,
    interior_min_lot_width_ft NUMERIC,
    interior_min_lot_depth_ft NUMERIC,

    -- Minimum Lot Size (Corner Lots)
    corner_min_lot_area_sqft NUMERIC,
    corner_min_lot_frontage_ft NUMERIC,
    corner_min_lot_width_ft NUMERIC,
    corner_min_lot_depth_ft NUMERIC,

    -- Additional lot requirements
    min_circle_diameter_ft NUMERIC,
    buildable_lot_area_sqft NUMERIC,

    -- Minimum Required Yard Areas (feet) - Principal Building
    principal_front_yard_ft NUMERIC,
    principal_side_yard_ft NUMERIC,
    principal_street_side_yard_ft NUMERIC,
    principal_rear_yard_ft NUMERIC,
    principal_street_rear_yard_ft NUMERIC,

    -- Minimum Required Yard Areas (feet) - Accessory Building
    accessory_front_yard_ft NUMERIC,
    accessory_side_yard_ft NUMERIC,
    accessory_street_side_yard_ft NUMERIC,
    accessory_rear_yard_ft NUMERIC,
    accessory_street_rear_yard_ft NUMERIC,

    -- Coverage and density requirements
    max_building_coverage_percent NUMERIC,
    max_lot_coverage_percent NUMERIC,

    -- Height restrictions - Principal Building
    max_height_stories INTEGER,
    max_height_feet_total NUMERIC,

    -- Floor area requirements
    min_gross_floor_area_first_floor_sqft NUMERIC,
    min_gross_floor_area_multistory_sqft NUMERIC,
    max_gross_floor_area_all_structures_sqft NUMERIC,

    -- Development intensity
    maximum_far NUMERIC, -- Floor Area Ratio
    maximum_density_units_per_acre NUMERIC,

    -- Metadata
    data_source VARCHAR(255), -- e.g., 'AI_Extracted', 'Manual_Entry'
    extraction_confidence NUMERIC, -- 0.0 to 1.0
    extracted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique requirements per jurisdiction and zone
    UNIQUE(town, county, state, zone)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_requirements_jurisdiction ON requirements(town, county, state);
CREATE INDEX IF NOT EXISTS idx_requirements_zone ON requirements(zone);
CREATE INDEX IF NOT EXISTS idx_requirements_job_id ON requirements(job_id);
CREATE INDEX IF NOT EXISTS idx_requirements_data_source ON requirements(data_source);
CREATE INDEX IF NOT EXISTS idx_requirements_created_at ON requirements(created_at);

-- Function to update updated_at timestamp for requirements table
CREATE OR REPLACE FUNCTION update_requirements_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for auto-updating timestamps
DROP TRIGGER IF EXISTS update_requirements_updated_at ON requirements;
CREATE TRIGGER update_requirements_updated_at
    BEFORE UPDATE ON requirements
    FOR EACH ROW EXECUTE FUNCTION update_requirements_updated_at_column();

-- Enable Row Level Security
ALTER TABLE requirements ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for requirements table
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON requirements;
CREATE POLICY "Enable read access for authenticated users" ON requirements
FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Enable insert for authenticated users" ON requirements;
CREATE POLICY "Enable insert for authenticated users" ON requirements
FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Enable update for authenticated users" ON requirements;
CREATE POLICY "Enable update for authenticated users" ON requirements
FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Enable delete for authenticated users" ON requirements;
CREATE POLICY "Enable delete for authenticated users" ON requirements
FOR DELETE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Test the table
INSERT INTO requirements (
    town, county, state, zone, data_source, extraction_confidence,
    interior_min_lot_area_sqft, principal_front_yard_ft, max_height_feet_total
) VALUES (
    'Test Restore', 'Test County', 'NJ', 'R-TEST', 'Manual_Test', 1.0,
    10000, 25, 35
) ON CONFLICT (town, county, state, zone) DO NOTHING;

-- Verify table works
SELECT 
    'requirements table' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as latest_record
FROM requirements;

-- Clean up test
DELETE FROM requirements WHERE town = 'Test Restore';

-- Show table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'requirements' 
AND table_schema = 'public'
ORDER BY ordinal_position
LIMIT 20;
