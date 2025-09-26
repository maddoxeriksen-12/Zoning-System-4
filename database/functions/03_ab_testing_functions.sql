-- RPC Functions for A/B Testing and Accuracy Tracking System

-- Function 1: Create a new prompt experiment
CREATE OR REPLACE FUNCTION create_prompt_experiment(
    p_prompt_name VARCHAR,
    p_prompt_version VARCHAR,
    p_prompt_text TEXT,
    p_llm_model VARCHAR,
    p_description TEXT DEFAULT NULL,
    p_hypothesis TEXT DEFAULT NULL,
    p_is_baseline BOOLEAN DEFAULT false,
    p_temperature FLOAT DEFAULT 0.1,
    p_max_tokens INTEGER DEFAULT 8000
)
RETURNS UUID AS $$
DECLARE
    new_experiment_id UUID;
BEGIN
    INSERT INTO prompt_experiments (
        prompt_name, prompt_version, prompt_text, llm_model,
        experiment_description, hypothesis, is_baseline,
        llm_temperature, llm_max_tokens, is_active
    )
    VALUES (
        p_prompt_name, p_prompt_version, p_prompt_text, p_llm_model,
        p_description, p_hypothesis, p_is_baseline,
        p_temperature, p_max_tokens, true
    )
    RETURNING id INTO new_experiment_id;
    
    RETURN new_experiment_id;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Create ground truth document
CREATE OR REPLACE FUNCTION create_ground_truth_document(
    p_document_name VARCHAR,
    p_original_filename VARCHAR,
    p_town VARCHAR,
    p_county VARCHAR,
    p_state VARCHAR,
    p_verified_by VARCHAR,
    p_number_of_zones INTEGER,
    p_complexity VARCHAR DEFAULT 'medium',
    p_file_path TEXT DEFAULT NULL,
    p_verification_notes TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    new_doc_id UUID;
BEGIN
    INSERT INTO ground_truth_documents (
        document_name, original_filename, town, county, state,
        verified_by, number_of_zones, document_complexity,
        file_path, verification_notes
    )
    VALUES (
        p_document_name, p_original_filename, p_town, p_county, p_state,
        p_verified_by, p_number_of_zones, p_complexity,
        p_file_path, p_verification_notes
    )
    RETURNING id INTO new_doc_id;
    
    RETURN new_doc_id;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Add ground truth requirement
CREATE OR REPLACE FUNCTION add_ground_truth_requirement(
    p_ground_truth_doc_id UUID,
    p_zone VARCHAR,
    p_zone_description TEXT DEFAULT NULL,
    p_interior_min_lot_area_sqft FLOAT DEFAULT NULL,
    p_interior_min_lot_frontage_ft FLOAT DEFAULT NULL,
    p_interior_min_lot_width_ft FLOAT DEFAULT NULL,
    p_interior_min_lot_depth_ft FLOAT DEFAULT NULL,
    p_principal_front_yard_ft FLOAT DEFAULT NULL,
    p_principal_side_yard_ft FLOAT DEFAULT NULL,
    p_principal_rear_yard_ft FLOAT DEFAULT NULL,
    p_max_building_coverage_percent FLOAT DEFAULT NULL,
    p_max_lot_coverage_percent FLOAT DEFAULT NULL,
    p_max_height_stories INTEGER DEFAULT NULL,
    p_max_height_feet_total FLOAT DEFAULT NULL,
    p_maximum_far FLOAT DEFAULT NULL,
    p_maximum_density_units_per_acre FLOAT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    new_req_id UUID;
BEGIN
    INSERT INTO ground_truth_requirements (
        ground_truth_doc_id, zone, zone_description,
        interior_min_lot_area_sqft, interior_min_lot_frontage_ft,
        interior_min_lot_width_ft, interior_min_lot_depth_ft,
        principal_front_yard_ft, principal_side_yard_ft, principal_rear_yard_ft,
        max_building_coverage_percent, max_lot_coverage_percent,
        max_height_stories, max_height_feet_total,
        maximum_far, maximum_density_units_per_acre
    )
    VALUES (
        p_ground_truth_doc_id, p_zone, p_zone_description,
        p_interior_min_lot_area_sqft, p_interior_min_lot_frontage_ft,
        p_interior_min_lot_width_ft, p_interior_min_lot_depth_ft,
        p_principal_front_yard_ft, p_principal_side_yard_ft, p_principal_rear_yard_ft,
        p_max_building_coverage_percent, p_max_lot_coverage_percent,
        p_max_height_stories, p_max_height_feet_total,
        p_maximum_far, p_maximum_density_units_per_acre
    )
    RETURNING id INTO new_req_id;
    
    RETURN new_req_id;
END;
$$ LANGUAGE plpgsql;

-- Function 4: Record test results
CREATE OR REPLACE FUNCTION record_test_result(
    p_prompt_experiment_id UUID,
    p_ground_truth_doc_id UUID,
    p_test_epoch INTEGER,
    p_raw_response TEXT,
    p_parsed_zones_count INTEGER,
    p_extraction_success BOOLEAN,
    p_overall_accuracy FLOAT,
    p_zone_accuracy FLOAT,
    p_field_accuracy FLOAT,
    p_location_accuracy FLOAT,
    p_processing_time FLOAT DEFAULT NULL,
    p_tokens_used INTEGER DEFAULT NULL,
    p_test_batch_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    new_test_id UUID;
    batch_id UUID;
BEGIN
    -- Generate batch ID if not provided
    IF p_test_batch_id IS NULL THEN
        batch_id := gen_random_uuid();
    ELSE
        batch_id := p_test_batch_id;
    END IF;
    
    INSERT INTO requirements_tests (
        prompt_experiment_id, ground_truth_doc_id, test_batch_id,
        test_epoch, raw_llm_response, parsed_zones_count,
        extraction_success, overall_accuracy_score,
        zone_identification_accuracy, field_extraction_accuracy,
        location_extraction_accuracy, processing_time_seconds, llm_tokens_used
    )
    VALUES (
        p_prompt_experiment_id, p_ground_truth_doc_id, batch_id,
        p_test_epoch, p_raw_response, p_parsed_zones_count,
        p_extraction_success, p_overall_accuracy,
        p_zone_accuracy, p_field_accuracy,
        p_location_accuracy, p_processing_time, p_tokens_used
    )
    RETURNING id INTO new_test_id;
    
    -- Update prompt experiment statistics
    PERFORM update_prompt_experiment_stats(p_prompt_experiment_id);
    
    RETURN new_test_id;
END;
$$ LANGUAGE plpgsql;

-- Function 5: Update prompt experiment statistics
CREATE OR REPLACE FUNCTION update_prompt_experiment_stats(
    p_experiment_id UUID
)
RETURNS VOID AS $$
DECLARE
    total_tests INTEGER;
    successful_tests INTEGER;
    failed_tests INTEGER;
    avg_accuracy FLOAT;
    avg_field_accuracy FLOAT;
    avg_zone_accuracy FLOAT;
BEGIN
    -- Calculate statistics from all test results for this experiment
    SELECT 
        COUNT(*),
        SUM(CASE WHEN extraction_success THEN 1 ELSE 0 END),
        SUM(CASE WHEN NOT extraction_success THEN 1 ELSE 0 END),
        AVG(overall_accuracy_score),
        AVG(field_extraction_accuracy),
        AVG(zone_identification_accuracy)
    INTO 
        total_tests,
        successful_tests, 
        failed_tests,
        avg_accuracy,
        avg_field_accuracy,
        avg_zone_accuracy
    FROM requirements_tests
    WHERE prompt_experiment_id = p_experiment_id;
    
    -- Update the prompt experiment record
    UPDATE prompt_experiments
    SET 
        total_tests = COALESCE(total_tests, 0),
        successful_extractions = COALESCE(successful_tests, 0),
        failed_extractions = COALESCE(failed_tests, 0),
        average_accuracy_score = COALESCE(avg_accuracy, 0.0),
        average_field_accuracy = COALESCE(avg_field_accuracy, 0.0),
        average_zone_accuracy = COALESCE(avg_zone_accuracy, 0.0),
        last_tested_at = NOW(),
        updated_at = NOW()
    WHERE id = p_experiment_id;
END;
$$ LANGUAGE plpgsql;

-- Function 6: Calculate accuracy between predicted and actual values
CREATE OR REPLACE FUNCTION calculate_field_accuracy(
    predicted_value FLOAT,
    actual_value FLOAT,
    tolerance_percent FLOAT DEFAULT 5.0
)
RETURNS FLOAT AS $$
BEGIN
    -- Handle NULL cases
    IF predicted_value IS NULL AND actual_value IS NULL THEN
        RETURN 1.0; -- Both null = perfect match
    END IF;
    
    IF (predicted_value IS NULL) != (actual_value IS NULL) THEN
        RETURN 0.0; -- One null, one not = no match
    END IF;
    
    -- Both have values - calculate percentage difference
    IF actual_value = 0 THEN
        -- Avoid division by zero
        RETURN CASE WHEN predicted_value = 0 THEN 1.0 ELSE 0.0 END;
    END IF;
    
    DECLARE
        percent_diff FLOAT;
    BEGIN
        percent_diff := ABS((predicted_value - actual_value) / actual_value) * 100;
        
        -- Return accuracy score (1.0 for perfect, decreasing with error)
        IF percent_diff <= tolerance_percent THEN
            RETURN 1.0;
        ELSE
            -- Linear decay: 100% error = 0 accuracy
            RETURN GREATEST(0.0, 1.0 - (percent_diff / 100.0));
        END IF;
    END;
END;
$$ LANGUAGE plpgsql;

-- Function 7: Get best performing prompts
CREATE OR REPLACE FUNCTION get_best_prompts(
    p_min_tests INTEGER DEFAULT 5,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    prompt_name VARCHAR,
    prompt_version VARCHAR,
    llm_model VARCHAR,
    total_tests INTEGER,
    success_rate FLOAT,
    avg_accuracy FLOAT,
    avg_field_accuracy FLOAT,
    avg_zone_accuracy FLOAT,
    last_tested TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pe.prompt_name,
        pe.prompt_version,
        pe.llm_model,
        pe.total_tests,
        CASE 
            WHEN pe.total_tests > 0 THEN (pe.successful_extractions::FLOAT / pe.total_tests)
            ELSE 0.0 
        END as success_rate,
        pe.average_accuracy_score,
        pe.average_field_accuracy,
        pe.average_zone_accuracy,
        pe.last_tested_at
    FROM prompt_experiments pe
    WHERE pe.total_tests >= p_min_tests
    ORDER BY pe.average_accuracy_score DESC, pe.total_tests DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function 8: Get test results for a specific document
CREATE OR REPLACE FUNCTION get_document_test_results(
    p_ground_truth_doc_id UUID
)
RETURNS TABLE(
    test_id UUID,
    prompt_name VARCHAR,
    prompt_version VARCHAR,
    test_epoch INTEGER,
    overall_accuracy FLOAT,
    zone_accuracy FLOAT,
    field_accuracy FLOAT,
    zones_found INTEGER,
    test_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rt.id,
        pe.prompt_name,
        pe.prompt_version,
        rt.test_epoch,
        rt.overall_accuracy_score,
        rt.zone_identification_accuracy,
        rt.field_extraction_accuracy,
        rt.parsed_zones_count,
        rt.test_date
    FROM requirements_tests rt
    JOIN prompt_experiments pe ON rt.prompt_experiment_id = pe.id
    WHERE rt.ground_truth_doc_id = p_ground_truth_doc_id
    ORDER BY rt.test_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function 9: Generate test summary report
CREATE OR REPLACE FUNCTION generate_test_summary(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE(
    total_experiments INTEGER,
    total_tests INTEGER,
    avg_accuracy FLOAT,
    best_prompt VARCHAR,
    improvement_over_baseline FLOAT
) AS $$
DECLARE
    baseline_accuracy FLOAT;
BEGIN
    -- Set default dates if not provided
    IF p_start_date IS NULL THEN
        p_start_date := NOW() - INTERVAL '30 days';
    END IF;
    
    IF p_end_date IS NULL THEN
        p_end_date := NOW();
    END IF;
    
    -- Get baseline accuracy
    SELECT COALESCE(pe.average_accuracy_score, 0.0) INTO baseline_accuracy
    FROM prompt_experiments pe
    WHERE pe.is_baseline = true
    ORDER BY pe.created_at DESC
    LIMIT 1;
    
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT pe.id)::INTEGER as total_experiments,
        COUNT(rt.id)::INTEGER as total_tests,
        AVG(rt.overall_accuracy_score) as avg_accuracy,
        (SELECT pe2.prompt_name || ' v' || pe2.prompt_version
         FROM prompt_experiments pe2
         WHERE pe2.total_tests >= 3
         ORDER BY pe2.average_accuracy_score DESC
         LIMIT 1) as best_prompt,
        CASE 
            WHEN baseline_accuracy > 0 THEN 
                (MAX(pe.average_accuracy_score) - baseline_accuracy) / baseline_accuracy * 100
            ELSE 0.0
        END as improvement_over_baseline
    FROM prompt_experiments pe
    LEFT JOIN requirements_tests rt ON pe.id = rt.prompt_experiment_id
    WHERE rt.test_date BETWEEN p_start_date AND p_end_date
       OR rt.test_date IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Function 10: Activate/Deactivate prompt experiments  
CREATE OR REPLACE FUNCTION toggle_prompt_experiment(
    p_experiment_id UUID,
    p_is_active BOOLEAN
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE prompt_experiments
    SET is_active = p_is_active, updated_at = NOW()
    WHERE id = p_experiment_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
