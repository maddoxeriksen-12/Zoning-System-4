-- Create the RPC function to parse and insert zoning requirements
CREATE OR REPLACE FUNCTION parse_zoning_requirements(input_json jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_town text;
    v_county text;
    v_requirement jsonb;
    v_inserted_count integer := 0;
    v_error_count integer := 0;
    v_result jsonb;
BEGIN
    -- Extract town and county from the input JSON
    v_town := input_json->>'extracted_town';
    v_county := input_json->>'extracted_county';
    
    -- Validate input
    IF v_town IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', 'Missing required field: extracted_town'
        );
    END IF;
    
    -- Loop through each zoning requirement
    FOR v_requirement IN SELECT * FROM jsonb_array_elements(input_json->'zoning_requirements')
    LOOP
        BEGIN
            -- Insert into the requirements table
            -- Adjust the table name and column names according to your actual schema
            INSERT INTO requirements (
                town,
                county,
                zone_name,
                interior_min_lot_area_sqft,
                interior_min_lot_frontage_ft,
                interior_min_lot_width_ft,
                interior_min_lot_depth_ft,
                corner_min_lot_area_sqft,
                corner_min_lot_frontage_ft,
                corner_min_lot_width_ft,
                corner_min_lot_depth_ft,
                min_circle_diameter_ft,
                buildable_lot_area_sqft,
                principal_front_yard_ft,
                principal_side_yard_ft,
                principal_street_side_yard_ft,
                principal_rear_yard_ft,
                principal_street_rear_yard_ft,
                accessory_front_yard_ft,
                accessory_side_yard_ft,
                accessory_street_side_yard_ft,
                accessory_rear_yard_ft,
                accessory_street_rear_yard_ft,
                max_building_coverage_pct,
                max_lot_coverage_pct,
                principal_height_stories,
                principal_height_ft,
                min_gross_floor_area_first_floor_sqft,
                min_gross_floor_area_multistory_sqft,
                max_gross_floor_area_all_sqft,
                max_far,
                max_density_units_per_acre,
                created_at,
                updated_at
            ) VALUES (
                v_town,
                v_county,
                v_requirement->>'zone_name',
                (v_requirement->>'interior_min_lot_area_sqft')::integer,
                (v_requirement->>'interior_min_lot_frontage_ft')::integer,
                (v_requirement->>'interior_min_lot_width_ft')::integer,
                (v_requirement->>'interior_min_lot_depth_ft')::integer,
                (v_requirement->>'corner_min_lot_area_sqft')::integer,
                (v_requirement->>'corner_min_lot_frontage_ft')::integer,
                (v_requirement->>'corner_min_lot_width_ft')::integer,
                (v_requirement->>'corner_min_lot_depth_ft')::integer,
                (v_requirement->>'min_circle_diameter_ft')::numeric,
                (v_requirement->>'buildable_lot_area_sqft')::integer,
                (v_requirement->>'principal_front_yard_ft')::numeric,
                (v_requirement->>'principal_side_yard_ft')::numeric,
                (v_requirement->>'principal_street_side_yard_ft')::numeric,
                (v_requirement->>'principal_rear_yard_ft')::numeric,
                (v_requirement->>'principal_street_rear_yard_ft')::numeric,
                (v_requirement->>'accessory_front_yard_ft')::numeric,
                (v_requirement->>'accessory_side_yard_ft')::numeric,
                (v_requirement->>'accessory_street_side_yard_ft')::numeric,
                (v_requirement->>'accessory_rear_yard_ft')::numeric,
                (v_requirement->>'accessory_street_rear_yard_ft')::numeric,
                (v_requirement->>'max_building_coverage_pct')::numeric,
                (v_requirement->>'max_lot_coverage_pct')::numeric,
                (v_requirement->>'principal_height_stories')::numeric,
                (v_requirement->>'principal_height_ft')::numeric,
                (v_requirement->>'min_gross_floor_area_first_floor_sqft')::integer,
                (v_requirement->>'min_gross_floor_area_multistory_sqft')::integer,
                (v_requirement->>'max_gross_floor_area_all_sqft')::integer,
                (v_requirement->>'max_far')::numeric,
                (v_requirement->>'max_density_units_per_acre')::numeric,
                NOW(),
                NOW()
            )
            ON CONFLICT (town, zone_name) 
            DO UPDATE SET
                county = EXCLUDED.county,
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
                max_building_coverage_pct = EXCLUDED.max_building_coverage_pct,
                max_lot_coverage_pct = EXCLUDED.max_lot_coverage_pct,
                principal_height_stories = EXCLUDED.principal_height_stories,
                principal_height_ft = EXCLUDED.principal_height_ft,
                min_gross_floor_area_first_floor_sqft = EXCLUDED.min_gross_floor_area_first_floor_sqft,
                min_gross_floor_area_multistory_sqft = EXCLUDED.min_gross_floor_area_multistory_sqft,
                max_gross_floor_area_all_sqft = EXCLUDED.max_gross_floor_area_all_sqft,
                max_far = EXCLUDED.max_far,
                max_density_units_per_acre = EXCLUDED.max_density_units_per_acre,
                updated_at = NOW();
            
            v_inserted_count := v_inserted_count + 1;
            
        EXCEPTION
            WHEN OTHERS THEN
                v_error_count := v_error_count + 1;
                RAISE WARNING 'Error inserting zone %: %', v_requirement->>'zone_name', SQLERRM;
        END;
    END LOOP;
    
    -- Return result summary
    v_result := jsonb_build_object(
        'success', true,
        'message', format('Successfully processed %s zones, %s errors', v_inserted_count, v_error_count),
        'inserted_count', v_inserted_count,
        'error_count', v_error_count,
        'town', v_town,
        'county', v_county
    );
    
    RETURN v_result;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', format('Error processing JSON: %s', SQLERRM)
        );
END;
$$;

-- Grant execute permission to authenticated users (adjust as needed)
GRANT EXECUTE ON FUNCTION parse_zoning_requirements(jsonb) TO authenticated;

-- Example usage:
/*
SELECT parse_zoning_requirements('{
    "extracted_town": "Linwood",
    "extracted_county": null,
    "zoning_requirements": [
        {
            "zone_name": "R-20",
            "interior_min_lot_area_sqft": 20000,
            "interior_min_lot_frontage_ft": 100,
            ...
        }
    ]
}'::jsonb);
*/

-- Alternative version with document_id reference if you need to link back to the documents table
CREATE OR REPLACE FUNCTION parse_zoning_requirements_with_doc_ref(
    input_json jsonb,
    document_id uuid DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_town text;
    v_county text;
    v_requirement jsonb;
    v_inserted_count integer := 0;
    v_error_count integer := 0;
    v_result jsonb;
BEGIN
    -- Extract town and county from the input JSON
    v_town := input_json->>'extracted_town';
    v_county := input_json->>'extracted_county';
    
    -- Validate input
    IF v_town IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', 'Missing required field: extracted_town'
        );
    END IF;
    
    -- Loop through each zoning requirement
    FOR v_requirement IN SELECT * FROM jsonb_array_elements(input_json->'zoning_requirements')
    LOOP
        BEGIN
            -- Insert with document reference if needed
            INSERT INTO requirements (
                town,
                county,
                document_id, -- Add this column if you need to track source document
                zone_name,
                interior_min_lot_area_sqft,
                interior_min_lot_frontage_ft,
                interior_min_lot_width_ft,
                interior_min_lot_depth_ft,
                corner_min_lot_area_sqft,
                corner_min_lot_frontage_ft,
                corner_min_lot_width_ft,
                corner_min_lot_depth_ft,
                min_circle_diameter_ft,
                buildable_lot_area_sqft,
                principal_front_yard_ft,
                principal_side_yard_ft,
                principal_street_side_yard_ft,
                principal_rear_yard_ft,
                principal_street_rear_yard_ft,
                accessory_front_yard_ft,
                accessory_side_yard_ft,
                accessory_street_side_yard_ft,
                accessory_rear_yard_ft,
                accessory_street_rear_yard_ft,
                max_building_coverage_pct,
                max_lot_coverage_pct,
                principal_height_stories,
                principal_height_ft,
                min_gross_floor_area_first_floor_sqft,
                min_gross_floor_area_multistory_sqft,
                max_gross_floor_area_all_sqft,
                max_far,
                max_density_units_per_acre,
                created_at,
                updated_at
            ) VALUES (
                v_town,
                v_county,
                document_id,
                v_requirement->>'zone_name',
                (v_requirement->>'interior_min_lot_area_sqft')::integer,
                (v_requirement->>'interior_min_lot_frontage_ft')::integer,
                (v_requirement->>'interior_min_lot_width_ft')::integer,
                (v_requirement->>'interior_min_lot_depth_ft')::integer,
                (v_requirement->>'corner_min_lot_area_sqft')::integer,
                (v_requirement->>'corner_min_lot_frontage_ft')::integer,
                (v_requirement->>'corner_min_lot_width_ft')::integer,
                (v_requirement->>'corner_min_lot_depth_ft')::integer,
                (v_requirement->>'min_circle_diameter_ft')::numeric,
                (v_requirement->>'buildable_lot_area_sqft')::integer,
                (v_requirement->>'principal_front_yard_ft')::numeric,
                (v_requirement->>'principal_side_yard_ft')::numeric,
                (v_requirement->>'principal_street_side_yard_ft')::numeric,
                (v_requirement->>'principal_rear_yard_ft')::numeric,
                (v_requirement->>'principal_street_rear_yard_ft')::numeric,
                (v_requirement->>'accessory_front_yard_ft')::numeric,
                (v_requirement->>'accessory_side_yard_ft')::numeric,
                (v_requirement->>'accessory_street_side_yard_ft')::numeric,
                (v_requirement->>'accessory_rear_yard_ft')::numeric,
                (v_requirement->>'accessory_street_rear_yard_ft')::numeric,
                (v_requirement->>'max_building_coverage_pct')::numeric,
                (v_requirement->>'max_lot_coverage_pct')::numeric,
                (v_requirement->>'principal_height_stories')::numeric,
                (v_requirement->>'principal_height_ft')::numeric,
                (v_requirement->>'min_gross_floor_area_first_floor_sqft')::integer,
                (v_requirement->>'min_gross_floor_area_multistory_sqft')::integer,
                (v_requirement->>'max_gross_floor_area_all_sqft')::integer,
                (v_requirement->>'max_far')::numeric,
                (v_requirement->>'max_density_units_per_acre')::numeric,
                NOW(),
                NOW()
            )
            ON CONFLICT (town, zone_name) 
            DO UPDATE SET
                county = EXCLUDED.county,
                document_id = EXCLUDED.document_id,
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
                max_building_coverage_pct = EXCLUDED.max_building_coverage_pct,
                max_lot_coverage_pct = EXCLUDED.max_lot_coverage_pct,
                principal_height_stories = EXCLUDED.principal_height_stories,
                principal_height_ft = EXCLUDED.principal_height_ft,
                min_gross_floor_area_first_floor_sqft = EXCLUDED.min_gross_floor_area_first_floor_sqft,
                min_gross_floor_area_multistory_sqft = EXCLUDED.min_gross_floor_area_multistory_sqft,
                max_gross_floor_area_all_sqft = EXCLUDED.max_gross_floor_area_all_sqft,
                max_far = EXCLUDED.max_far,
                max_density_units_per_acre = EXCLUDED.max_density_units_per_acre,
                updated_at = NOW();
            
            v_inserted_count := v_inserted_count + 1;
            
        EXCEPTION
            WHEN OTHERS THEN
                v_error_count := v_error_count + 1;
                RAISE WARNING 'Error inserting zone %: %', v_requirement->>'zone_name', SQLERRM;
        END;
    END LOOP;
    
    -- Update the document processing status if document_id is provided
    IF document_id IS NOT NULL THEN
        UPDATE documents 
        SET 
            processing_status = 'completed',
            processing_completed_at = NOW(),
            updated_at = NOW()
        WHERE id = document_id;
    END IF;
    
    -- Return result summary
    v_result := jsonb_build_object(
        'success', true,
        'message', format('Successfully processed %s zones, %s errors', v_inserted_count, v_error_count),
        'inserted_count', v_inserted_count,
        'error_count', v_error_count,
        'town', v_town,
        'county', v_county,
        'document_id', document_id
    );
    
    RETURN v_result;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Update document status to failed if there's an error
        IF document_id IS NOT NULL THEN
            UPDATE documents 
            SET 
                processing_status = 'failed',
                error_message = SQLERRM,
                updated_at = NOW()
            WHERE id = document_id;
        END IF;
        
        RETURN jsonb_build_object(
            'success', false,
            'message', format('Error processing JSON: %s', SQLERRM)
        );
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION parse_zoning_requirements_with_doc_ref(jsonb, uuid) TO authenticated;