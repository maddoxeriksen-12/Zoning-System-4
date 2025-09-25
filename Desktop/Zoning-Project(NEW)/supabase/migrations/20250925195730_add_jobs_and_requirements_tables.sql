-- Jobs and Requirements Tables for Zoning Project
-- Jobs table tracks PDF uploads from GUI
-- Requirements table contains standardized zoning information per jurisdiction

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    town VARCHAR(255) NOT NULL,
    county VARCHAR(255),
    state VARCHAR(50) NOT NULL,
    pdf_filename VARCHAR(255),
    original_pdf_filename VARCHAR(255),
    pdf_file_path VARCHAR(500),
    pdf_file_size BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    ai_model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique jobs per jurisdiction
    UNIQUE(town, county, state)
);

-- Requirements table - standardized zoning information per jurisdiction and zone
CREATE TABLE IF NOT EXISTS requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

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

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_jobs_town_county_state ON jobs(town, county, state);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(processing_status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_requirements_jurisdiction ON requirements(town, county, state);
CREATE INDEX IF NOT EXISTS idx_requirements_zone ON requirements(zone);
CREATE INDEX IF NOT EXISTS idx_requirements_job_id ON requirements(job_id);
CREATE INDEX IF NOT EXISTS idx_requirements_data_source ON requirements(data_source);
CREATE INDEX IF NOT EXISTS idx_requirements_created_at ON requirements(created_at);

-- Function to update updated_at timestamp for jobs table
CREATE OR REPLACE FUNCTION update_jobs_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update updated_at timestamp for requirements table
CREATE OR REPLACE FUNCTION update_requirements_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating timestamps
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_jobs_updated_at_column();

CREATE TRIGGER update_requirements_updated_at
    BEFORE UPDATE ON requirements
    FOR EACH ROW EXECUTE FUNCTION update_requirements_updated_at_column();

-- Functions for jobs and requirements management
CREATE OR REPLACE FUNCTION create_job(
    p_town VARCHAR(255),
    p_county VARCHAR(255),
    p_state VARCHAR(50),
    p_pdf_filename VARCHAR(255),
    p_original_pdf_filename VARCHAR(255),
    p_pdf_file_path VARCHAR(500),
    p_pdf_file_size BIGINT
)
RETURNS UUID AS $$
DECLARE
    job_id UUID;
BEGIN
    INSERT INTO jobs (
        town, county, state, pdf_filename, original_pdf_filename,
        pdf_file_path, pdf_file_size, processing_status
    )
    VALUES (
        p_town, p_county, p_state, p_pdf_filename, p_original_pdf_filename,
        p_pdf_file_path, p_pdf_file_size, 'pending'
    )
    RETURNING id INTO job_id;

    RETURN job_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_job_status(
    p_job_id UUID,
    p_status VARCHAR(50),
    p_ai_model_used VARCHAR(100)
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE jobs
    SET
        processing_status = p_status,
        ai_model_used = COALESCE(p_ai_model_used, ai_model_used),
        processing_started_at = CASE
            WHEN p_status = 'processing' AND processing_started_at IS NULL THEN NOW()
            ELSE processing_started_at
        END,
        processing_completed_at = CASE
            WHEN p_status IN ('completed', 'failed') THEN NOW()
            ELSE processing_completed_at
        END,
        updated_at = NOW()
    WHERE id = p_job_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_jobs_summary()
RETURNS TABLE (
    total_jobs BIGINT,
    pending_jobs BIGINT,
    processing_jobs BIGINT,
    completed_jobs BIGINT,
    failed_jobs BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_jobs,
        COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_jobs,
        COUNT(*) FILTER (WHERE processing_status = 'processing') as processing_jobs,
        COUNT(*) FILTER (WHERE processing_status = 'completed') as completed_jobs,
        COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_jobs
    FROM jobs;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_requirement(
    p_job_id UUID,
    p_town VARCHAR(255),
    p_county VARCHAR(255),
    p_state VARCHAR(50),
    p_zone VARCHAR(255),
    p_data_source VARCHAR(255),
    p_extraction_confidence NUMERIC,

    -- Interior lots
    p_interior_min_lot_area_sqft NUMERIC,
    p_interior_min_lot_frontage_ft NUMERIC,
    p_interior_min_lot_width_ft NUMERIC,
    p_interior_min_lot_depth_ft NUMERIC,

    -- Corner lots
    p_corner_min_lot_area_sqft NUMERIC,
    p_corner_min_lot_frontage_ft NUMERIC,
    p_corner_min_lot_width_ft NUMERIC,
    p_corner_min_lot_depth_ft NUMERIC,

    -- Other lot requirements
    p_min_circle_diameter_ft NUMERIC,
    p_buildable_lot_area_sqft NUMERIC,

    -- Principal building yards
    p_principal_front_yard_ft NUMERIC,
    p_principal_side_yard_ft NUMERIC,
    p_principal_street_side_yard_ft NUMERIC,
    p_principal_rear_yard_ft NUMERIC,
    p_principal_street_rear_yard_ft NUMERIC,

    -- Accessory building yards
    p_accessory_front_yard_ft NUMERIC,
    p_accessory_side_yard_ft NUMERIC,
    p_accessory_street_side_yard_ft NUMERIC,
    p_accessory_rear_yard_ft NUMERIC,
    p_accessory_street_rear_yard_ft NUMERIC,

    -- Coverage and height
    p_max_building_coverage_percent NUMERIC,
    p_max_lot_coverage_percent NUMERIC,
    p_max_height_stories INTEGER,
    p_max_height_feet_total NUMERIC,

    -- Floor area
    p_min_gross_floor_area_first_floor_sqft NUMERIC,
    p_min_gross_floor_area_multistory_sqft NUMERIC,
    p_max_gross_floor_area_all_structures_sqft NUMERIC,

    -- Development intensity
    p_maximum_far NUMERIC,
    p_maximum_density_units_per_acre NUMERIC
)
RETURNS UUID AS $$
DECLARE
    req_id UUID;
BEGIN
    INSERT INTO requirements (
        job_id, town, county, state, zone, data_source, extraction_confidence,
        interior_min_lot_area_sqft, interior_min_lot_frontage_ft,
        interior_min_lot_width_ft, interior_min_lot_depth_ft,
        corner_min_lot_area_sqft, corner_min_lot_frontage_ft,
        corner_min_lot_width_ft, corner_min_lot_depth_ft,
        min_circle_diameter_ft, buildable_lot_area_sqft,
        principal_front_yard_ft, principal_side_yard_ft,
        principal_street_side_yard_ft, principal_rear_yard_ft,
        principal_street_rear_yard_ft, accessory_front_yard_ft,
        accessory_side_yard_ft, accessory_street_side_yard_ft,
        accessory_rear_yard_ft, accessory_street_rear_yard_ft,
        max_building_coverage_percent, max_lot_coverage_percent,
        max_height_stories, max_height_feet_total,
        min_gross_floor_area_first_floor_sqft,
        min_gross_floor_area_multistory_sqft,
        max_gross_floor_area_all_structures_sqft,
        maximum_far, maximum_density_units_per_acre,
        extracted_at
    )
    VALUES (
        p_job_id, p_town, p_county, p_state, p_zone, p_data_source, p_extraction_confidence,
        p_interior_min_lot_area_sqft, p_interior_min_lot_frontage_ft,
        p_interior_min_lot_width_ft, p_interior_min_lot_depth_ft,
        p_corner_min_lot_area_sqft, p_corner_min_lot_frontage_ft,
        p_corner_min_lot_width_ft, p_corner_min_lot_depth_ft,
        p_min_circle_diameter_ft, p_buildable_lot_area_sqft,
        p_principal_front_yard_ft, p_principal_side_yard_ft,
        p_principal_street_side_yard_ft, p_principal_rear_yard_ft,
        p_principal_street_rear_yard_ft, p_accessory_front_yard_ft,
        p_accessory_side_yard_ft, p_accessory_street_side_yard_ft,
        p_accessory_rear_yard_ft, p_accessory_street_rear_yard_ft,
        p_max_building_coverage_percent, p_max_lot_coverage_percent,
        p_max_height_stories, p_max_height_feet_total,
        p_min_gross_floor_area_first_floor_sqft,
        p_min_gross_floor_area_multistory_sqft,
        p_max_gross_floor_area_all_structures_sqft,
        p_maximum_far, p_maximum_density_units_per_acre,
        NOW()
    )
    ON CONFLICT (town, county, state, zone)
    DO UPDATE SET
        job_id = EXCLUDED.job_id,
        data_source = EXCLUDED.data_source,
        extraction_confidence = EXCLUDED.extraction_confidence,
        interior_min_lot_area_sqft = EXCLUDED.interior_min_lot_area_sqft,
        interior_min_lot_frontage_ft = EXCLUDED.interior_min_lot_frontage_ft,
        interior_min_lot_width_ft = EXCLUDED.interior_min_lot_width_ft,
        interior_min_lot_depth_ft = EXCLUDED.interior_min_lot_depth_ft,
        corner_min_lot_area_sqft = EXCLUDED.corner_min_lot_area_sqft,
        corner_min_lot_frontage_ft = EXCLUDED.corner_min_lot_frontage_ft,
        corner_min_lot_width_ft = EXCLUDED.corner_min_lot_width_ft,
        corner_min_lot_depth_ft = EXCLUDED.corner_min_lot_depth_ft,
        min_circle_diameter_ft = EXCLUDED.min_circle_diameter_ft,
        buildable_lot_area_sqft = EXCLUDED.buildable_lot_area_sqft,
        principal_front_yard_ft = EXCLUDED.principal_front_yard_ft,
        principal_side_yard_ft = EXCLUDED.principal_side_yard_ft,
        principal_street_side_yard_ft = EXCLUDED.principal_street_side_yard_ft,
        principal_rear_yard_ft = EXCLUDED.principal_rear_yard_ft,
        principal_street_rear_yard_ft = EXCLUDED.principal_street_rear_yard_ft,
        accessory_front_yard_ft = EXCLUDED.accessory_front_yard_ft,
        accessory_side_yard_ft = EXCLUDED.accessory_side_yard_ft,
        accessory_street_side_yard_ft = EXCLUDED.accessory_street_side_yard_ft,
        accessory_rear_yard_ft = EXCLUDED.accessory_rear_yard_ft,
        accessory_street_rear_yard_ft = EXCLUDED.accessory_street_rear_yard_ft,
        max_building_coverage_percent = EXCLUDED.max_building_coverage_percent,
        max_lot_coverage_percent = EXCLUDED.max_lot_coverage_percent,
        max_height_stories = EXCLUDED.max_height_stories,
        max_height_feet_total = EXCLUDED.max_height_feet_total,
        min_gross_floor_area_first_floor_sqft = EXCLUDED.min_gross_floor_area_first_floor_sqft,
        min_gross_floor_area_multistory_sqft = EXCLUDED.min_gross_floor_area_multistory_sqft,
        max_gross_floor_area_all_structures_sqft = EXCLUDED.max_gross_floor_area_all_structures_sqft,
        maximum_far = EXCLUDED.maximum_far,
        maximum_density_units_per_acre = EXCLUDED.maximum_density_units_per_acre,
        extracted_at = NOW(),
        updated_at = NOW()
    RETURNING id INTO req_id;

    RETURN req_id;
END;
$$ LANGUAGE plpgsql;
