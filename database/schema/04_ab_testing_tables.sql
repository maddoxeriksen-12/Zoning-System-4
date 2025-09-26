-- A/B Testing and Accuracy Tracking Tables for Zoning Prompts
-- This schema supports prompt experimentation and accuracy measurement

-- Table 1: prompt_experiments - Track different prompts and their performance
CREATE TABLE IF NOT EXISTS prompt_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name VARCHAR(100) NOT NULL, -- e.g., "grok_v1_detailed", "grok_v2_structured"
    prompt_version VARCHAR(20) NOT NULL, -- e.g., "1.0", "1.1", "2.0"
    prompt_text TEXT NOT NULL, -- The actual prompt sent to LLM
    llm_model VARCHAR(50) NOT NULL, -- e.g., "grok-4-fast-reasoning", "gpt-4"
    llm_temperature FLOAT DEFAULT 0.1,
    llm_max_tokens INTEGER DEFAULT 8000,
    
    -- Experiment metadata
    experiment_description TEXT,
    hypothesis TEXT, -- What improvement is this prompt trying to achieve
    is_active BOOLEAN DEFAULT true, -- Currently being tested
    is_baseline BOOLEAN DEFAULT false, -- Is this the baseline/control prompt
    
    -- Performance tracking
    total_tests INTEGER DEFAULT 0,
    successful_extractions INTEGER DEFAULT 0,
    failed_extractions INTEGER DEFAULT 0,
    average_accuracy_score FLOAT DEFAULT 0.0, -- Overall accuracy (0-1)
    average_field_accuracy FLOAT DEFAULT 0.0, -- Field-level accuracy
    average_zone_accuracy FLOAT DEFAULT 0.0, -- Zone-level accuracy
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_tested_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT unique_prompt_version UNIQUE(prompt_name, prompt_version),
    CONSTRAINT valid_accuracy_range CHECK (average_accuracy_score >= 0.0 AND average_accuracy_score <= 1.0),
    CONSTRAINT valid_temperature CHECK (llm_temperature >= 0.0 AND llm_temperature <= 2.0)
);

-- Table 2: ground_truth_documents - Store human-verified ground truth data
CREATE TABLE IF NOT EXISTS ground_truth_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    
    -- Location metadata
    town VARCHAR(255) NOT NULL,
    county VARCHAR(255),
    state VARCHAR(2) NOT NULL DEFAULT 'NJ',
    
    -- Human verification
    verified_by VARCHAR(100) NOT NULL, -- Who verified this ground truth
    verification_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verification_notes TEXT,
    
    -- Document characteristics
    document_complexity VARCHAR(20) CHECK (document_complexity IN ('simple', 'medium', 'complex')),
    number_of_zones INTEGER NOT NULL,
    has_tables BOOLEAN DEFAULT false,
    has_charts BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 3: ground_truth_requirements - Human-verified zoning requirements (ground truth)
CREATE TABLE IF NOT EXISTS ground_truth_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ground_truth_doc_id UUID NOT NULL REFERENCES ground_truth_documents(id) ON DELETE CASCADE,
    
    -- Zone identification
    zone VARCHAR(100) NOT NULL,
    zone_description TEXT,
    
    -- All the same fields as requirements table for comparison
    interior_min_lot_area_sqft FLOAT,
    interior_min_lot_frontage_ft FLOAT,
    interior_min_lot_width_ft FLOAT,
    interior_min_lot_depth_ft FLOAT,
    corner_min_lot_area_sqft FLOAT,
    corner_min_lot_frontage_ft FLOAT,
    corner_min_lot_width_ft FLOAT,
    corner_min_lot_depth_ft FLOAT,
    min_circle_diameter_ft FLOAT,
    buildable_lot_area_sqft FLOAT,
    
    -- Principal building yards
    principal_front_yard_ft FLOAT,
    principal_side_yard_ft FLOAT,
    principal_street_side_yard_ft FLOAT,
    principal_rear_yard_ft FLOAT,
    principal_street_rear_yard_ft FLOAT,
    
    -- Accessory building yards
    accessory_front_yard_ft FLOAT,
    accessory_side_yard_ft FLOAT,
    accessory_street_side_yard_ft FLOAT,
    accessory_rear_yard_ft FLOAT,
    accessory_street_rear_yard_ft FLOAT,
    
    -- Coverage and height
    max_building_coverage_percent FLOAT,
    max_lot_coverage_percent FLOAT,
    max_height_stories INTEGER,
    max_height_feet_total FLOAT,
    
    -- Floor area
    min_gross_floor_area_first_floor_sqft FLOAT,
    min_gross_floor_area_multistory_sqft FLOAT,
    max_gross_floor_area_all_structures_sqft FLOAT,
    
    -- Development intensity
    maximum_far FLOAT,
    maximum_density_units_per_acre FLOAT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_ground_truth_zone UNIQUE(ground_truth_doc_id, zone)
);

-- Table 4: requirements_tests - Store test results comparing AI vs ground truth
CREATE TABLE IF NOT EXISTS requirements_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_experiment_id UUID NOT NULL REFERENCES prompt_experiments(id) ON DELETE CASCADE,
    ground_truth_doc_id UUID NOT NULL REFERENCES ground_truth_documents(id) ON DELETE CASCADE,
    
    -- Test execution metadata
    test_batch_id UUID DEFAULT gen_random_uuid(), -- Group related tests
    test_epoch INTEGER NOT NULL, -- Track which testing round this was
    test_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- LLM Response data
    raw_llm_response TEXT NOT NULL,
    parsed_zones_count INTEGER DEFAULT 0,
    extraction_success BOOLEAN DEFAULT false,
    extraction_error TEXT,
    
    -- Accuracy scores (0.0 to 1.0)
    overall_accuracy_score FLOAT DEFAULT 0.0,
    zone_identification_accuracy FLOAT DEFAULT 0.0, -- How well did it identify zones
    field_extraction_accuracy FLOAT DEFAULT 0.0, -- How accurate were the field values
    location_extraction_accuracy FLOAT DEFAULT 0.0, -- Town/county accuracy
    
    -- Detailed field-level accuracy (JSON storing per-field scores)
    field_accuracy_breakdown JSONB,
    zone_accuracy_breakdown JSONB,
    
    -- Performance metrics
    processing_time_seconds FLOAT,
    llm_tokens_used INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_accuracy_scores CHECK (
        overall_accuracy_score >= 0.0 AND overall_accuracy_score <= 1.0 AND
        zone_identification_accuracy >= 0.0 AND zone_identification_accuracy <= 1.0 AND
        field_extraction_accuracy >= 0.0 AND field_extraction_accuracy <= 1.0 AND
        location_extraction_accuracy >= 0.0 AND location_extraction_accuracy <= 1.0
    )
);

-- Table 5: test_zone_results - Individual zone test results for detailed analysis
CREATE TABLE IF NOT EXISTS test_zone_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirements_test_id UUID NOT NULL REFERENCES requirements_tests(id) ON DELETE CASCADE,
    ground_truth_req_id UUID REFERENCES ground_truth_requirements(id) ON DELETE CASCADE,
    
    -- Zone matching
    predicted_zone VARCHAR(100),
    actual_zone VARCHAR(100),
    zone_match_score FLOAT DEFAULT 0.0, -- How well zone names matched
    
    -- All predicted fields (same structure as ground_truth_requirements)
    predicted_interior_min_lot_area_sqft FLOAT,
    predicted_interior_min_lot_frontage_ft FLOAT,
    predicted_interior_min_lot_width_ft FLOAT,
    predicted_interior_min_lot_depth_ft FLOAT,
    predicted_corner_min_lot_area_sqft FLOAT,
    predicted_corner_min_lot_frontage_ft FLOAT,
    predicted_corner_min_lot_width_ft FLOAT,
    predicted_corner_min_lot_depth_ft FLOAT,
    predicted_min_circle_diameter_ft FLOAT,
    predicted_buildable_lot_area_sqft FLOAT,
    predicted_principal_front_yard_ft FLOAT,
    predicted_principal_side_yard_ft FLOAT,
    predicted_principal_street_side_yard_ft FLOAT,
    predicted_principal_rear_yard_ft FLOAT,
    predicted_principal_street_rear_yard_ft FLOAT,
    predicted_accessory_front_yard_ft FLOAT,
    predicted_accessory_side_yard_ft FLOAT,
    predicted_accessory_street_side_yard_ft FLOAT,
    predicted_accessory_rear_yard_ft FLOAT,
    predicted_accessory_street_rear_yard_ft FLOAT,
    predicted_max_building_coverage_percent FLOAT,
    predicted_max_lot_coverage_percent FLOAT,
    predicted_max_height_stories INTEGER,
    predicted_max_height_feet_total FLOAT,
    predicted_min_gross_floor_area_first_floor_sqft FLOAT,
    predicted_min_gross_floor_area_multistory_sqft FLOAT,
    predicted_max_gross_floor_area_all_structures_sqft FLOAT,
    predicted_maximum_far FLOAT,
    predicted_maximum_density_units_per_acre FLOAT,
    
    -- Individual field accuracy scores
    field_accuracy_scores JSONB, -- Store accuracy for each field
    zone_accuracy_score FLOAT DEFAULT 0.0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompt_experiments_active ON prompt_experiments(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_prompt_experiments_accuracy ON prompt_experiments(average_accuracy_score DESC);
CREATE INDEX IF NOT EXISTS idx_ground_truth_doc_location ON ground_truth_documents(town, county, state);
CREATE INDEX IF NOT EXISTS idx_requirements_tests_prompt ON requirements_tests(prompt_experiment_id);
CREATE INDEX IF NOT EXISTS idx_requirements_tests_batch ON requirements_tests(test_batch_id);
CREATE INDEX IF NOT EXISTS idx_requirements_tests_epoch ON requirements_tests(test_epoch);
CREATE INDEX IF NOT EXISTS idx_test_zone_results_test ON test_zone_results(requirements_test_id);

-- Views for easy analysis
CREATE OR REPLACE VIEW prompt_performance_summary AS
SELECT 
    pe.prompt_name,
    pe.prompt_version,
    pe.llm_model,
    pe.total_tests,
    pe.average_accuracy_score,
    pe.average_field_accuracy,
    pe.average_zone_accuracy,
    CASE 
        WHEN pe.total_tests > 0 THEN (pe.successful_extractions::FLOAT / pe.total_tests) 
        ELSE 0.0 
    END as success_rate,
    pe.last_tested_at,
    pe.is_active
FROM prompt_experiments pe
ORDER BY pe.average_accuracy_score DESC;

-- View for ground truth document overview  
CREATE OR REPLACE VIEW ground_truth_overview AS
SELECT 
    gtd.document_name,
    gtd.town,
    gtd.county,
    gtd.state,
    gtd.number_of_zones,
    gtd.document_complexity,
    gtd.verified_by,
    COUNT(gtr.id) as verified_zones,
    gtd.verification_date
FROM ground_truth_documents gtd
LEFT JOIN ground_truth_requirements gtr ON gtd.id = gtr.ground_truth_doc_id
GROUP BY gtd.id, gtd.document_name, gtd.town, gtd.county, gtd.state, 
         gtd.number_of_zones, gtd.document_complexity, gtd.verified_by, gtd.verification_date
ORDER BY gtd.verification_date DESC;

-- Comments for documentation
COMMENT ON TABLE prompt_experiments IS 'Tracks different LLM prompts and their performance metrics for A/B testing';
COMMENT ON TABLE ground_truth_documents IS 'Human-verified documents that serve as ground truth for accuracy testing';
COMMENT ON TABLE ground_truth_requirements IS 'Human-verified zoning requirements extracted from ground truth documents';
COMMENT ON TABLE requirements_tests IS 'Results of testing AI extraction against ground truth data';
COMMENT ON TABLE test_zone_results IS 'Detailed per-zone test results for granular accuracy analysis';
