-- Nuclear option: Rename the function to avoid conflicts
-- This creates a new function with a different name

-- Create new function with different name
CREATE OR REPLACE FUNCTION public.insert_zoning_requirement(
    p_job_id UUID,
    p_town VARCHAR(255),
    p_county VARCHAR(255),
    p_state VARCHAR(2),
    p_zone VARCHAR(100),
    p_data_source VARCHAR(50),
    p_extraction_confidence FLOAT,
    p_interior_min_lot_area_sqft FLOAT DEFAULT NULL,
    p_interior_min_lot_frontage_ft FLOAT DEFAULT NULL,
    p_interior_min_lot_width_ft FLOAT DEFAULT NULL,
    p_interior_min_lot_depth_ft FLOAT DEFAULT NULL,
    p_corner_min_lot_area_sqft FLOAT DEFAULT NULL,
    p_corner_min_lot_frontage_ft FLOAT DEFAULT NULL,
    p_corner_min_lot_width_ft FLOAT DEFAULT NULL,
    p_corner_min_lot_depth_ft FLOAT DEFAULT NULL,
    p_min_circle_diameter_ft FLOAT DEFAULT NULL,
    p_buildable_lot_area_sqft FLOAT DEFAULT NULL,
    p_principal_front_yard_ft FLOAT DEFAULT NULL,
    p_principal_side_yard_ft FLOAT DEFAULT NULL,
    p_principal_street_side_yard_ft FLOAT DEFAULT NULL,
    p_principal_rear_yard_ft FLOAT DEFAULT NULL,
    p_principal_street_rear_yard_ft FLOAT DEFAULT NULL,
    p_accessory_front_yard_ft FLOAT DEFAULT NULL,
    p_accessory_side_yard_ft FLOAT DEFAULT NULL,
    p_accessory_street_side_yard_ft FLOAT DEFAULT NULL,
    p_accessory_rear_yard_ft FLOAT DEFAULT NULL,
    p_accessory_street_rear_yard_ft FLOAT DEFAULT NULL,
    p_max_building_coverage_percent FLOAT DEFAULT NULL,
    p_max_lot_coverage_percent FLOAT DEFAULT NULL,
    p_max_height_stories INTEGER DEFAULT NULL,
    p_max_height_feet_total FLOAT DEFAULT NULL,
    p_min_gross_floor_area_first_floor_sqft FLOAT DEFAULT NULL,
    p_min_gross_floor_area_multistory_sqft FLOAT DEFAULT NULL,
    p_max_gross_floor_area_all_structures_sqft FLOAT DEFAULT NULL,
    p_maximum_far FLOAT DEFAULT NULL,
    p_maximum_density_units_per_acre FLOAT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    new_req_id UUID;
BEGIN
    INSERT INTO requirements (
        job_id, town, county, state, zone, data_source, extraction_confidence,
        interior_min_lot_area_sqft, interior_min_lot_frontage_ft, interior_min_lot_width_ft, interior_min_lot_depth_ft,
        corner_min_lot_area_sqft, corner_min_lot_frontage_ft, corner_min_lot_width_ft, corner_min_lot_depth_ft,
        min_circle_diameter_ft, buildable_lot_area_sqft,
        principal_front_yard_ft, principal_side_yard_ft, principal_street_side_yard_ft, 
        principal_rear_yard_ft, principal_street_rear_yard_ft,
        accessory_front_yard_ft, accessory_side_yard_ft, accessory_street_side_yard_ft, 
        accessory_rear_yard_ft, accessory_street_rear_yard_ft,
        max_building_coverage_percent, max_lot_coverage_percent,
        max_height_stories, max_height_feet_total,
        min_gross_floor_area_first_floor_sqft, min_gross_floor_area_multistory_sqft, 
        max_gross_floor_area_all_structures_sqft,
        maximum_far, maximum_density_units_per_acre,
        extracted_at, created_at, updated_at
    )
    VALUES (
        p_job_id, p_town, p_county, p_state, p_zone, p_data_source, p_extraction_confidence,
        p_interior_min_lot_area_sqft, p_interior_min_lot_frontage_ft, p_interior_min_lot_width_ft, p_interior_min_lot_depth_ft,
        p_corner_min_lot_area_sqft, p_corner_min_lot_frontage_ft, p_corner_min_lot_width_ft, p_corner_min_lot_depth_ft,
        p_min_circle_diameter_ft, p_buildable_lot_area_sqft,
        p_principal_front_yard_ft, p_principal_side_yard_ft, p_principal_street_side_yard_ft, 
        p_principal_rear_yard_ft, p_principal_street_rear_yard_ft,
        p_accessory_front_yard_ft, p_accessory_side_yard_ft, p_accessory_street_side_yard_ft, 
        p_accessory_rear_yard_ft, p_accessory_street_rear_yard_ft,
        p_max_building_coverage_percent, p_max_lot_coverage_percent,
        p_max_height_stories, p_max_height_feet_total,
        p_min_gross_floor_area_first_floor_sqft, p_min_gross_floor_area_multistory_sqft, 
        p_max_gross_floor_area_all_structures_sqft,
        p_maximum_far, p_maximum_density_units_per_acre,
        NOW(), NOW(), NOW()
    )
    ON CONFLICT (town, county, state, zone) 
    DO UPDATE SET
        job_id = EXCLUDED.job_id,
        data_source = EXCLUDED.data_source,
        extraction_confidence = EXCLUDED.extraction_confidence,
        interior_min_lot_area_sqft = COALESCE(EXCLUDED.interior_min_lot_area_sqft, requirements.interior_min_lot_area_sqft),
        interior_min_lot_frontage_ft = COALESCE(EXCLUDED.interior_min_lot_frontage_ft, requirements.interior_min_lot_frontage_ft),
        interior_min_lot_width_ft = COALESCE(EXCLUDED.interior_min_lot_width_ft, requirements.interior_min_lot_width_ft),
        interior_min_lot_depth_ft = COALESCE(EXCLUDED.interior_min_lot_depth_ft, requirements.interior_min_lot_depth_ft),
        corner_min_lot_area_sqft = COALESCE(EXCLUDED.corner_min_lot_area_sqft, requirements.corner_min_lot_area_sqft),
        corner_min_lot_frontage_ft = COALESCE(EXCLUDED.corner_min_lot_frontage_ft, requirements.corner_min_lot_frontage_ft),
        corner_min_lot_width_ft = COALESCE(EXCLUDED.corner_min_lot_width_ft, requirements.corner_min_lot_width_ft),
        corner_min_lot_depth_ft = COALESCE(EXCLUDED.corner_min_lot_depth_ft, requirements.corner_min_lot_depth_ft),
        min_circle_diameter_ft = COALESCE(EXCLUDED.min_circle_diameter_ft, requirements.min_circle_diameter_ft),
        buildable_lot_area_sqft = COALESCE(EXCLUDED.buildable_lot_area_sqft, requirements.buildable_lot_area_sqft),
        principal_front_yard_ft = COALESCE(EXCLUDED.principal_front_yard_ft, requirements.principal_front_yard_ft),
        principal_side_yard_ft = COALESCE(EXCLUDED.principal_side_yard_ft, requirements.principal_side_yard_ft),
        principal_street_side_yard_ft = COALESCE(EXCLUDED.principal_street_side_yard_ft, requirements.principal_street_side_yard_ft),
        principal_rear_yard_ft = COALESCE(EXCLUDED.principal_rear_yard_ft, requirements.principal_rear_yard_ft),
        principal_street_rear_yard_ft = COALESCE(EXCLUDED.principal_street_rear_yard_ft, requirements.principal_street_rear_yard_ft),
        accessory_front_yard_ft = COALESCE(EXCLUDED.accessory_front_yard_ft, requirements.accessory_front_yard_ft),
        accessory_side_yard_ft = COALESCE(EXCLUDED.accessory_side_yard_ft, requirements.accessory_side_yard_ft),
        accessory_street_side_yard_ft = COALESCE(EXCLUDED.accessory_street_side_yard_ft, requirements.accessory_street_side_yard_ft),
        accessory_rear_yard_ft = COALESCE(EXCLUDED.accessory_rear_yard_ft, requirements.accessory_rear_yard_ft),
        accessory_street_rear_yard_ft = COALESCE(EXCLUDED.accessory_street_rear_yard_ft, requirements.accessory_street_rear_yard_ft),
        max_building_coverage_percent = COALESCE(EXCLUDED.max_building_coverage_percent, requirements.max_building_coverage_percent),
        max_lot_coverage_percent = COALESCE(EXCLUDED.max_lot_coverage_percent, requirements.max_lot_coverage_percent),
        max_height_stories = COALESCE(EXCLUDED.max_height_stories, requirements.max_height_stories),
        max_height_feet_total = COALESCE(EXCLUDED.max_height_feet_total, requirements.max_height_feet_total),
        min_gross_floor_area_first_floor_sqft = COALESCE(EXCLUDED.min_gross_floor_area_first_floor_sqft, requirements.min_gross_floor_area_first_floor_sqft),
        min_gross_floor_area_multistory_sqft = COALESCE(EXCLUDED.min_gross_floor_area_multistory_sqft, requirements.min_gross_floor_area_multistory_sqft),
        max_gross_floor_area_all_structures_sqft = COALESCE(EXCLUDED.max_gross_floor_area_all_structures_sqft, requirements.max_gross_floor_area_all_structures_sqft),
        maximum_far = COALESCE(EXCLUDED.maximum_far, requirements.maximum_far),
        maximum_density_units_per_acre = COALESCE(EXCLUDED.maximum_density_units_per_acre, requirements.maximum_density_units_per_acre),
        updated_at = NOW()
    RETURNING id INTO new_req_id;
    
    RETURN new_req_id;
END;
$$ LANGUAGE plpgsql;

-- Test it (first create a test job, then use its ID)
DO $$
DECLARE
    test_job_id UUID;
BEGIN
    -- Create a test job first
    INSERT INTO jobs (town, county, state, pdf_filename, processing_status)
    VALUES ('TestTown', 'TestCounty', 'NJ', 'test.pdf', 'completed')
    RETURNING id INTO test_job_id;
    
    -- Now test the insert_zoning_requirement function with the real job_id
    PERFORM insert_zoning_requirement(
        test_job_id,
        'TestTown',
        'TestCounty', 
        'NJ',
        'R-1',
        'AI_Extracted',
        0.95,
        10000.0,
        100.0
    );
    
    RAISE NOTICE 'Test successful! Created requirement for job %', test_job_id;
    
    -- Clean up test data
    DELETE FROM requirements WHERE job_id = test_job_id;
    DELETE FROM jobs WHERE id = test_job_id;
END $$;
