-- Recreate Requirements Table in Supabase
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/xympjhgrdvcrpdvftgyu/sql

-- Create the requirements table with all 40+ zoning fields
CREATE TABLE IF NOT EXISTS requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Location information
    town VARCHAR(255) NOT NULL,
    county VARCHAR(255),
    state VARCHAR(2) NOT NULL DEFAULT 'NJ',
    zone VARCHAR(100) NOT NULL,
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'AI_Extracted',
    extraction_confidence FLOAT DEFAULT 0.7,
    
    -- Interior lot requirements
    interior_min_lot_area_sqft FLOAT,
    interior_min_lot_frontage_ft FLOAT,
    interior_min_lot_width_ft FLOAT,
    interior_min_lot_depth_ft FLOAT,
    
    -- Corner lot requirements  
    corner_min_lot_area_sqft FLOAT,
    corner_min_lot_frontage_ft FLOAT,
    corner_min_lot_width_ft FLOAT,
    corner_min_lot_depth_ft FLOAT,
    
    -- Additional lot requirements
    min_circle_diameter_ft FLOAT,
    buildable_lot_area_sqft FLOAT,
    
    -- Principal building yard requirements (setbacks)
    principal_front_yard_ft FLOAT,
    principal_side_yard_ft FLOAT,
    principal_street_side_yard_ft FLOAT,
    principal_rear_yard_ft FLOAT,
    principal_street_rear_yard_ft FLOAT,
    
    -- Accessory building yard requirements
    accessory_front_yard_ft FLOAT,
    accessory_side_yard_ft FLOAT,
    accessory_street_side_yard_ft FLOAT,
    accessory_rear_yard_ft FLOAT,
    accessory_street_rear_yard_ft FLOAT,
    
    -- Coverage and height restrictions
    max_building_coverage_percent FLOAT,
    max_lot_coverage_percent FLOAT,
    max_height_stories INTEGER,
    max_height_feet_total FLOAT,
    
    -- Floor area requirements
    min_gross_floor_area_first_floor_sqft FLOAT,
    min_gross_floor_area_multistory_sqft FLOAT,
    max_gross_floor_area_all_structures_sqft FLOAT,
    
    -- Development intensity
    maximum_far FLOAT,
    maximum_density_units_per_acre FLOAT,
    
    -- Timestamps
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_location_zone UNIQUE(town, county, state, zone),
    CONSTRAINT valid_confidence CHECK (extraction_confidence >= 0.0 AND extraction_confidence <= 1.0),
    CONSTRAINT valid_percentages CHECK (
        (max_building_coverage_percent IS NULL OR (max_building_coverage_percent >= 0 AND max_building_coverage_percent <= 100)) AND
        (max_lot_coverage_percent IS NULL OR (max_lot_coverage_percent >= 0 AND max_lot_coverage_percent <= 100))
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_requirements_location ON requirements(town, county, state);
CREATE INDEX IF NOT EXISTS idx_requirements_zone ON requirements(zone);
CREATE INDEX IF NOT EXISTS idx_requirements_job_id ON requirements(job_id);
CREATE INDEX IF NOT EXISTS idx_requirements_confidence ON requirements(extraction_confidence);
CREATE INDEX IF NOT EXISTS idx_requirements_created_at ON requirements(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE requirements ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Enable read access for authenticated users" ON requirements
FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Enable insert for authenticated users" ON requirements
FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Enable update for authenticated users" ON requirements
FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Enable delete for authenticated users" ON requirements
FOR DELETE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Insert some sample data to verify table structure
INSERT INTO requirements (
    town, county, state, zone, data_source, extraction_confidence,
    interior_min_lot_area_sqft, interior_min_lot_frontage_ft,
    principal_front_yard_ft, principal_side_yard_ft, principal_rear_yard_ft,
    max_height_feet_total, maximum_far
) VALUES (
    'Test Town', 'Test County', 'NJ', 'R-1', 'Manual_Test', 1.0,
    10000, 100, 25, 10, 30, 35, 1.5
) ON CONFLICT (town, county, state, zone) DO NOTHING;

-- Verify table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'requirements' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- Test the table
SELECT COUNT(*) as total_records FROM requirements;

-- Clean up test data
DELETE FROM requirements WHERE town = 'Test Town';
