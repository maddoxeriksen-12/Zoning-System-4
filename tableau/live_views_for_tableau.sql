-- Live Views for Tableau Real-Time Analytics
-- Run this in Supabase SQL Editor to create optimized views for Tableau

-- View 1: Live Requirements Dashboard Data
CREATE OR REPLACE VIEW tableau_requirements_live AS
SELECT 
    r.id,
    r.town,
    r.county,
    r.state,
    r.zone,
    r.data_source,
    r.extraction_confidence,
    
    -- Key zoning metrics for visualization
    r.interior_min_lot_area_sqft,
    r.interior_min_lot_frontage_ft,
    r.principal_front_yard_ft,
    r.principal_side_yard_ft, 
    r.principal_rear_yard_ft,
    r.max_building_coverage_percent,
    r.max_lot_coverage_percent,
    r.max_height_stories,
    r.max_height_feet_total,
    r.maximum_far,
    r.maximum_density_units_per_acre,
    
    -- Calculated fields for Tableau
    CASE 
        WHEN LEFT(r.zone, 1) = 'R' THEN 'Residential'
        WHEN LEFT(r.zone, 1) = 'C' THEN 'Commercial'  
        WHEN LEFT(r.zone, 1) = 'I' THEN 'Industrial'
        WHEN LEFT(r.zone, 1) = 'M' THEN 'Mixed Use'
        ELSE 'Other'
    END as zone_category,
    
    CASE 
        WHEN r.interior_min_lot_area_sqft >= 20000 THEN 'Large (20k+ sqft)'
        WHEN r.interior_min_lot_area_sqft >= 10000 THEN 'Medium (10k-20k sqft)'
        WHEN r.interior_min_lot_area_sqft >= 5000 THEN 'Small (5k-10k sqft)'
        WHEN r.interior_min_lot_area_sqft > 0 THEN 'Very Small (<5k sqft)'
        ELSE 'Not Specified'
    END as lot_size_category,
    
    CASE 
        WHEN r.extraction_confidence >= 0.9 THEN 'High Confidence'
        WHEN r.extraction_confidence >= 0.7 THEN 'Medium Confidence'
        WHEN r.extraction_confidence >= 0.5 THEN 'Low Confidence'
        ELSE 'Very Low Confidence'
    END as confidence_level,
    
    -- Job information
    j.pdf_filename,
    j.processing_status,
    j.ai_model_used,
    j.created_at as job_created_at,
    j.processing_completed_at,
    
    -- Document information
    d.original_filename,
    d.file_size,
    d.upload_date,
    d.processing_status as document_status,
    
    -- Time calculations
    r.created_at as requirement_created_at,
    DATE(r.created_at) as extraction_date,
    EXTRACT(HOUR FROM r.created_at) as extraction_hour,
    EXTRACT(DOW FROM r.created_at) as day_of_week,
    
    -- Geographic grouping
    CONCAT(r.town, ', ', COALESCE(r.county, ''), ', ', r.state) as full_location,
    r.state || '-' || COALESCE(r.county, 'Unknown') as state_county
    
FROM requirements r
LEFT JOIN jobs j ON r.job_id = j.id
LEFT JOIN documents d ON j.pdf_filename = d.filename
ORDER BY r.created_at DESC;

-- View 2: Live Processing Performance
CREATE OR REPLACE VIEW tableau_processing_performance AS
SELECT 
    DATE(j.created_at) as processing_date,
    j.town,
    j.county,
    j.state,
    j.processing_status,
    j.ai_model_used,
    
    -- Counts by status
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN j.processing_status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN j.processing_status = 'failed' THEN 1 END) as failed_jobs,
    COUNT(CASE WHEN j.processing_status = 'processing' THEN 1 END) as processing_jobs,
    
    -- Success metrics
    ROUND(
        COUNT(CASE WHEN j.processing_status = 'completed' THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as success_rate_percent,
    
    -- Requirements metrics
    COUNT(r.id) as requirements_created,
    ROUND(AVG(r.extraction_confidence), 3) as avg_confidence,
    COUNT(DISTINCT r.zone) as unique_zones_found,
    
    -- Processing time (if available)
    AVG(
        CASE 
            WHEN j.processing_completed_at IS NOT NULL AND j.processing_started_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (j.processing_completed_at - j.processing_started_at))
            ELSE NULL
        END
    ) as avg_processing_time_seconds,
    
    -- Geographic grouping
    CONCAT(j.state, '-', COALESCE(j.county, 'Unknown')) as state_county_group
    
FROM jobs j
LEFT JOIN requirements r ON j.id = r.job_id
WHERE j.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 
    DATE(j.created_at), j.town, j.county, j.state, 
    j.processing_status, j.ai_model_used
ORDER BY processing_date DESC, success_rate_percent DESC;

-- View 3: Live Zone Analysis
CREATE OR REPLACE VIEW tableau_zone_analysis AS
SELECT 
    r.zone,
    r.town,
    r.county,
    r.state,
    
    -- Zone statistics
    COUNT(*) as total_extractions,
    ROUND(AVG(r.extraction_confidence), 3) as avg_confidence,
    
    -- Common field availability
    COUNT(CASE WHEN r.interior_min_lot_area_sqft IS NOT NULL THEN 1 END) as has_lot_area,
    COUNT(CASE WHEN r.principal_front_yard_ft IS NOT NULL THEN 1 END) as has_front_yard,
    COUNT(CASE WHEN r.principal_side_yard_ft IS NOT NULL THEN 1 END) as has_side_yard,
    COUNT(CASE WHEN r.max_height_feet_total IS NOT NULL THEN 1 END) as has_height,
    COUNT(CASE WHEN r.maximum_far IS NOT NULL THEN 1 END) as has_far,
    
    -- Completion percentages
    ROUND(COUNT(CASE WHEN r.interior_min_lot_area_sqft IS NOT NULL THEN 1 END)::FLOAT / COUNT(*) * 100, 1) as lot_area_completion_pct,
    ROUND(COUNT(CASE WHEN r.principal_front_yard_ft IS NOT NULL THEN 1 END)::FLOAT / COUNT(*) * 100, 1) as setback_completion_pct,
    ROUND(COUNT(CASE WHEN r.maximum_far IS NOT NULL THEN 1 END)::FLOAT / COUNT(*) * 100, 1) as far_completion_pct,
    
    -- Average values (for comparison)
    ROUND(AVG(r.interior_min_lot_area_sqft), 0) as avg_lot_area_sqft,
    ROUND(AVG(r.principal_front_yard_ft), 1) as avg_front_yard_ft,
    ROUND(AVG(r.maximum_far), 2) as avg_far,
    
    -- Zone categorization
    CASE 
        WHEN LEFT(r.zone, 1) = 'R' THEN 'Residential'
        WHEN LEFT(r.zone, 1) = 'C' THEN 'Commercial'
        WHEN LEFT(r.zone, 1) = 'I' THEN 'Industrial'
        ELSE 'Other'
    END as zone_type,
    
    -- Time data
    MIN(r.created_at) as first_extracted,
    MAX(r.created_at) as last_extracted,
    DATE(MAX(r.created_at)) as last_extraction_date,
    
    -- Full location string
    CONCAT(r.town, ', ', COALESCE(r.county, ''), ', ', r.state) as full_location
    
FROM requirements r
WHERE r.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY r.zone, r.town, r.county, r.state
HAVING COUNT(*) >= 1  -- Only include zones with at least 1 extraction
ORDER BY total_extractions DESC, avg_confidence DESC;

-- View 4: Live Geographic Summary
CREATE OR REPLACE VIEW tableau_geographic_summary AS
SELECT 
    r.town,
    r.county,
    r.state,
    
    -- Location statistics
    COUNT(*) as total_requirements,
    COUNT(DISTINCT r.zone) as unique_zones,
    COUNT(DISTINCT r.job_id) as documents_processed,
    
    -- Quality metrics
    ROUND(AVG(r.extraction_confidence), 3) as avg_extraction_confidence,
    COUNT(CASE WHEN r.extraction_confidence >= 0.8 THEN 1 END) as high_confidence_extractions,
    ROUND(
        COUNT(CASE WHEN r.extraction_confidence >= 0.8 THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100, 1
    ) as high_confidence_pct,
    
    -- Data completeness
    ROUND(
        COUNT(CASE WHEN r.interior_min_lot_area_sqft IS NOT NULL THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100, 1
    ) as lot_area_completeness_pct,
    
    ROUND(
        COUNT(CASE WHEN r.principal_front_yard_ft IS NOT NULL THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100, 1
    ) as setback_completeness_pct,
    
    -- Most common zone
    MODE() WITHIN GROUP (ORDER BY r.zone) as most_common_zone,
    
    -- Time data
    MIN(r.created_at) as first_extraction,
    MAX(r.created_at) as last_extraction,
    
    -- State grouping for regional analysis
    r.state as state_code,
    CASE 
        WHEN r.state = 'NJ' THEN 'New Jersey'
        WHEN r.state = 'NY' THEN 'New York'
        WHEN r.state = 'PA' THEN 'Pennsylvania'
        WHEN r.state = 'CT' THEN 'Connecticut'
        ELSE r.state
    END as state_name
    
FROM requirements r
WHERE r.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY r.town, r.county, r.state
ORDER BY total_requirements DESC, avg_extraction_confidence DESC;

-- View 5: Live Daily Processing Stats (for real-time monitoring)
CREATE OR REPLACE VIEW tableau_daily_stats AS
SELECT 
    DATE(r.created_at) as extraction_date,
    
    -- Daily volumes
    COUNT(*) as requirements_extracted,
    COUNT(DISTINCT r.job_id) as documents_processed,
    COUNT(DISTINCT r.zone) as unique_zones_found,
    COUNT(DISTINCT CONCAT(r.town, r.county, r.state)) as unique_locations,
    
    -- Daily quality metrics
    ROUND(AVG(r.extraction_confidence), 3) as avg_daily_confidence,
    COUNT(CASE WHEN r.extraction_confidence >= 0.8 THEN 1 END) as high_confidence_count,
    
    -- Data completeness trends
    ROUND(
        COUNT(CASE WHEN r.interior_min_lot_area_sqft IS NOT NULL THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100, 1
    ) as daily_lot_area_completion,
    
    ROUND(
        COUNT(CASE WHEN r.principal_front_yard_ft IS NOT NULL THEN 1 END)::FLOAT / 
        NULLIF(COUNT(*), 0) * 100, 1
    ) as daily_setback_completion,
    
    -- Zone type breakdown
    COUNT(CASE WHEN LEFT(r.zone, 1) = 'R' THEN 1 END) as residential_zones,
    COUNT(CASE WHEN LEFT(r.zone, 1) = 'C' THEN 1 END) as commercial_zones,
    COUNT(CASE WHEN LEFT(r.zone, 1) = 'I' THEN 1 END) as industrial_zones,
    
    -- Rolling averages (7-day)
    ROUND(
        AVG(COUNT(*)) OVER (
            ORDER BY DATE(r.created_at) 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 1
    ) as rolling_7day_avg_extractions,
    
    -- Week and month for grouping
    EXTRACT(WEEK FROM r.created_at) as week_number,
    EXTRACT(MONTH FROM r.created_at) as month_number,
    TO_CHAR(r.created_at, 'YYYY-MM') as year_month
    
FROM requirements r
WHERE r.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(r.created_at)
ORDER BY extraction_date DESC;

-- Grant permissions for Tableau access
GRANT SELECT ON tableau_requirements_live TO authenticated;
GRANT SELECT ON tableau_processing_performance TO authenticated; 
GRANT SELECT ON tableau_zone_analysis TO authenticated;
GRANT SELECT ON tableau_geographic_summary TO authenticated;
GRANT SELECT ON tableau_daily_stats TO authenticated;

-- Also grant on the underlying tables that Tableau might query directly
GRANT SELECT ON requirements TO authenticated;
GRANT SELECT ON jobs TO authenticated;
GRANT SELECT ON documents TO authenticated;
GRANT SELECT ON prompt_experiments TO authenticated;
GRANT SELECT ON requirements_tests TO authenticated;
GRANT SELECT ON ground_truth_documents TO authenticated;
