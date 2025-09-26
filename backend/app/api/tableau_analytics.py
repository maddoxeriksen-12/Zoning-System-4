"""
Tableau Analytics API - Export data for Tableau visualizations
"""

import logging
import csv
import io
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
import pandas as pd

from ..core.database import get_db
from ..core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

def get_supabase():
    """Get Supabase client for analytics"""
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=500, detail="Supabase client not available")
    return client

@router.get("/export/prompt-performance")
async def export_prompt_performance(
    format: str = "csv",
    client = Depends(get_supabase)
):
    """Export prompt performance data for Tableau"""
    try:
        # Get comprehensive prompt performance data
        query = """
        SELECT 
            pe.prompt_name,
            pe.prompt_version,
            pe.llm_model,
            pe.llm_temperature,
            pe.llm_max_tokens,
            pe.total_tests,
            pe.successful_extractions,
            pe.failed_extractions,
            pe.average_accuracy_score,
            pe.average_field_accuracy,
            pe.average_zone_accuracy,
            pe.is_baseline,
            pe.is_active,
            pe.created_at,
            pe.last_tested_at,
            CASE 
                WHEN pe.total_tests > 0 THEN (pe.successful_extractions::FLOAT / pe.total_tests)
                ELSE 0.0 
            END as success_rate,
            pe.experiment_description,
            pe.hypothesis
        FROM prompt_experiments pe
        ORDER BY pe.average_accuracy_score DESC, pe.created_at DESC
        """
        
        result = client.query(query).execute()
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        # Convert to CSV for Tableau
        if not data:
            return StreamingResponse(
                io.StringIO("No data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=prompt_performance.csv"}
            )
        
        # Create DataFrame and CSV
        df = pd.DataFrame(data)
        
        # Convert timestamps to Tableau-friendly format
        for col in ['created_at', 'last_tested_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create CSV string
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=prompt_performance.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting prompt performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/test-results")
async def export_test_results(
    days: int = 30,
    format: str = "csv",
    client = Depends(get_supabase)
):
    """Export detailed test results for Tableau analysis"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Complex query joining all relevant tables
        query = f"""
        SELECT 
            rt.id as test_id,
            rt.test_epoch,
            rt.test_date,
            rt.overall_accuracy_score,
            rt.zone_identification_accuracy,
            rt.field_extraction_accuracy,
            rt.location_extraction_accuracy,
            rt.parsed_zones_count,
            rt.extraction_success,
            rt.processing_time_seconds,
            rt.llm_tokens_used,
            
            -- Prompt experiment details
            pe.prompt_name,
            pe.prompt_version,
            pe.llm_model,
            pe.llm_temperature,
            pe.is_baseline,
            
            -- Ground truth document details
            gtd.document_name,
            gtd.town as gt_town,
            gtd.county as gt_county,
            gtd.state as gt_state,
            gtd.number_of_zones as gt_zones_count,
            gtd.document_complexity,
            gtd.verified_by,
            
            -- Calculate improvement over baseline
            (rt.overall_accuracy_score - COALESCE(baseline.avg_baseline_accuracy, 0)) as improvement_over_baseline
            
        FROM requirements_tests rt
        JOIN prompt_experiments pe ON rt.prompt_experiment_id = pe.id
        JOIN ground_truth_documents gtd ON rt.ground_truth_doc_id = gtd.id
        LEFT JOIN (
            SELECT AVG(rt2.overall_accuracy_score) as avg_baseline_accuracy
            FROM requirements_tests rt2
            JOIN prompt_experiments pe2 ON rt2.prompt_experiment_id = pe2.id
            WHERE pe2.is_baseline = true
        ) baseline ON true
        WHERE rt.test_date >= '{start_date.isoformat()}'
        AND rt.test_date <= '{end_date.isoformat()}'
        ORDER BY rt.test_date DESC
        """
        
        result = client.query(query).execute()
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data, "period": f"Last {days} days"}
        
        # Convert to CSV for Tableau
        if not data:
            return StreamingResponse(
                io.StringIO("No test data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=test_results.csv"}
            )
        
        df = pd.DataFrame(data)
        
        # Convert timestamps to Tableau format
        df['test_date'] = pd.to_datetime(df['test_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add calculated fields for Tableau
        df['accuracy_category'] = df['overall_accuracy_score'].apply(
            lambda x: 'Excellent' if x >= 0.9 else 'Good' if x >= 0.7 else 'Needs Improvement'
        )
        
        df['zone_extraction_category'] = df['zone_identification_accuracy'].apply(
            lambda x: 'Perfect' if x >= 0.95 else 'Good' if x >= 0.8 else 'Poor'
        )
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return StreamingResponse(
            io.StringIO(csv_buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=test_results.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/accuracy-trends")
async def export_accuracy_trends(
    format: str = "csv",
    client = Depends(get_supabase)
):
    """Export accuracy trends over time for Tableau time-series analysis"""
    try:
        query = """
        SELECT 
            DATE(rt.test_date) as test_date,
            pe.prompt_name,
            pe.prompt_version,
            pe.llm_model,
            AVG(rt.overall_accuracy_score) as daily_avg_accuracy,
            AVG(rt.zone_identification_accuracy) as daily_avg_zone_accuracy,
            AVG(rt.field_extraction_accuracy) as daily_avg_field_accuracy,
            COUNT(rt.id) as tests_per_day,
            SUM(CASE WHEN rt.extraction_success THEN 1 ELSE 0 END) as successful_tests,
            AVG(rt.processing_time_seconds) as avg_processing_time,
            AVG(rt.llm_tokens_used) as avg_tokens_used
        FROM requirements_tests rt
        JOIN prompt_experiments pe ON rt.prompt_experiment_id = pe.id
        WHERE rt.test_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE(rt.test_date), pe.prompt_name, pe.prompt_version, pe.llm_model
        ORDER BY test_date DESC, daily_avg_accuracy DESC
        """
        
        result = client.query(query).execute()
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No trend data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=accuracy_trends.csv"}
            )
        
        df = pd.DataFrame(data)
        
        # Add trend indicators for Tableau
        df['accuracy_trend'] = df.groupby(['prompt_name', 'prompt_version'])['daily_avg_accuracy'].diff()
        df['performance_rating'] = df['daily_avg_accuracy'].apply(
            lambda x: 5 if x >= 0.95 else 4 if x >= 0.85 else 3 if x >= 0.75 else 2 if x >= 0.6 else 1
        )
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return StreamingResponse(
            io.StringIO(csv_buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=accuracy_trends.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting accuracy trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/field-accuracy-heatmap")
async def export_field_accuracy_heatmap(
    format: str = "csv",
    client = Depends(get_supabase)
):
    """Export field-level accuracy data for Tableau heatmap visualization"""
    try:
        # Get detailed field accuracy from test_zone_results
        query = """
        SELECT 
            pe.prompt_name,
            pe.prompt_version,
            tzr.predicted_zone,
            tzr.actual_zone,
            
            -- Field accuracy scores (calculated)
            CASE 
                WHEN tzr.predicted_interior_min_lot_area_sqft IS NOT NULL 
                AND gtr.interior_min_lot_area_sqft IS NOT NULL
                THEN ABS(1.0 - ABS(tzr.predicted_interior_min_lot_area_sqft - gtr.interior_min_lot_area_sqft) / gtr.interior_min_lot_area_sqft)
                ELSE NULL
            END as lot_area_accuracy,
            
            CASE 
                WHEN tzr.predicted_principal_front_yard_ft IS NOT NULL 
                AND gtr.principal_front_yard_ft IS NOT NULL
                THEN ABS(1.0 - ABS(tzr.predicted_principal_front_yard_ft - gtr.principal_front_yard_ft) / gtr.principal_front_yard_ft)
                ELSE NULL
            END as front_yard_accuracy,
            
            CASE 
                WHEN tzr.predicted_principal_side_yard_ft IS NOT NULL 
                AND gtr.principal_side_yard_ft IS NOT NULL
                THEN ABS(1.0 - ABS(tzr.predicted_principal_side_yard_ft - gtr.principal_side_yard_ft) / gtr.principal_side_yard_ft)
                ELSE NULL
            END as side_yard_accuracy,
            
            CASE 
                WHEN tzr.predicted_max_height_feet_total IS NOT NULL 
                AND gtr.max_height_feet_total IS NOT NULL
                THEN ABS(1.0 - ABS(tzr.predicted_max_height_feet_total - gtr.max_height_feet_total) / gtr.max_height_feet_total)
                ELSE NULL
            END as height_accuracy,
            
            CASE 
                WHEN tzr.predicted_maximum_far IS NOT NULL 
                AND gtr.maximum_far IS NOT NULL
                THEN ABS(1.0 - ABS(tzr.predicted_maximum_far - gtr.maximum_far) / gtr.maximum_far)
                ELSE NULL
            END as far_accuracy,
            
            rt.test_date,
            gtd.document_complexity
            
        FROM test_zone_results tzr
        JOIN requirements_tests rt ON tzr.requirements_test_id = rt.id
        JOIN prompt_experiments pe ON rt.prompt_experiment_id = pe.id
        JOIN ground_truth_requirements gtr ON tzr.ground_truth_req_id = gtr.id
        JOIN ground_truth_documents gtd ON gtr.ground_truth_doc_id = gtd.id
        WHERE rt.test_date >= CURRENT_DATE - INTERVAL '60 days'
        ORDER BY rt.test_date DESC
        """
        
        result = client.query(query).execute()
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No field accuracy data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=field_accuracy_heatmap.csv"}
            )
        
        df = pd.DataFrame(data)
        
        # Convert timestamps
        df['test_date'] = pd.to_datetime(df['test_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return StreamingResponse(
            io.StringIO(csv_buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=field_accuracy_heatmap.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting field accuracy heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/zone-extraction-analysis")
async def export_zone_extraction_analysis(
    format: str = "csv",
    client = Depends(get_supabase)
):
    """Export zone extraction analysis for Tableau - which zones are hardest to extract"""
    try:
        query = """
        SELECT 
            gtr.zone,
            gtd.town,
            gtd.county,
            gtd.state,
            gtd.document_complexity,
            COUNT(tzr.id) as total_tests,
            AVG(tzr.zone_accuracy_score) as avg_zone_accuracy,
            COUNT(CASE WHEN tzr.predicted_zone = gtr.zone THEN 1 END) as correct_predictions,
            COUNT(CASE WHEN tzr.predicted_zone != gtr.zone THEN 1 END) as incorrect_predictions,
            
            -- Most common incorrect predictions
            MODE() WITHIN GROUP (ORDER BY tzr.predicted_zone) as most_common_prediction,
            
            -- Field extraction success rates for this zone
            AVG(CASE WHEN tzr.predicted_interior_min_lot_area_sqft IS NOT NULL THEN 1.0 ELSE 0.0 END) as lot_area_extraction_rate,
            AVG(CASE WHEN tzr.predicted_principal_front_yard_ft IS NOT NULL THEN 1.0 ELSE 0.0 END) as front_yard_extraction_rate,
            AVG(CASE WHEN tzr.predicted_maximum_far IS NOT NULL THEN 1.0 ELSE 0.0 END) as far_extraction_rate,
            
            MIN(rt.test_date) as first_tested,
            MAX(rt.test_date) as last_tested
            
        FROM ground_truth_requirements gtr
        JOIN ground_truth_documents gtd ON gtr.ground_truth_doc_id = gtd.id
        LEFT JOIN test_zone_results tzr ON gtr.id = tzr.ground_truth_req_id
        LEFT JOIN requirements_tests rt ON tzr.requirements_test_id = rt.id
        WHERE rt.test_date >= CURRENT_DATE - INTERVAL '90 days' OR rt.test_date IS NULL
        GROUP BY gtr.zone, gtd.town, gtd.county, gtd.state, gtd.document_complexity
        ORDER BY avg_zone_accuracy ASC, total_tests DESC
        """
        
        result = client.query(query).execute()
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No zone analysis data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=zone_extraction_analysis.csv"}
            )
        
        df = pd.DataFrame(data)
        
        # Add Tableau-friendly calculations
        df['extraction_difficulty'] = df['avg_zone_accuracy'].apply(
            lambda x: 'Easy' if x >= 0.9 else 'Medium' if x >= 0.7 else 'Hard' if x is not None else 'Untested'
        )
        
        df['prediction_accuracy_percent'] = (df['correct_predictions'] / df['total_tests'] * 100).round(1)
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return StreamingResponse(
            io.StringIO(csv_buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=zone_extraction_analysis.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting zone analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/accuracy-improvement-timeline")
async def export_accuracy_improvement_timeline(
    format: str = "csv",
    client = Depends(get_supabase)
):
    """Export accuracy improvement timeline for Tableau trend analysis"""
    try:
        query = """
        WITH daily_stats AS (
            SELECT 
                DATE(rt.test_date) as test_date,
                pe.prompt_name,
                pe.prompt_version,
                AVG(rt.overall_accuracy_score) as daily_accuracy,
                AVG(rt.zone_identification_accuracy) as daily_zone_accuracy,
                AVG(rt.field_extraction_accuracy) as daily_field_accuracy,
                COUNT(rt.id) as daily_tests,
                pe.is_baseline
            FROM requirements_tests rt
            JOIN prompt_experiments pe ON rt.prompt_experiment_id = pe.id
            WHERE rt.test_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE(rt.test_date), pe.prompt_name, pe.prompt_version, pe.is_baseline
        ),
        baseline_reference AS (
            SELECT 
                test_date,
                AVG(daily_accuracy) as baseline_accuracy
            FROM daily_stats
            WHERE is_baseline = true
            GROUP BY test_date
        )
        SELECT 
            ds.*,
            br.baseline_accuracy,
            (ds.daily_accuracy - COALESCE(br.baseline_accuracy, 0)) as improvement_over_baseline,
            LAG(ds.daily_accuracy) OVER (PARTITION BY ds.prompt_name, ds.prompt_version ORDER BY ds.test_date) as previous_day_accuracy,
            (ds.daily_accuracy - LAG(ds.daily_accuracy) OVER (PARTITION BY ds.prompt_name, ds.prompt_version ORDER BY ds.test_date)) as day_over_day_change
        FROM daily_stats ds
        LEFT JOIN baseline_reference br ON ds.test_date = br.test_date
        ORDER BY ds.test_date DESC, ds.daily_accuracy DESC
        """
        
        result = client.query(query).execute()
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No timeline data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=accuracy_timeline.csv"}
            )
        
        df = pd.DataFrame(data)
        
        # Format for Tableau
        df['test_date'] = pd.to_datetime(df['test_date']).dt.strftime('%Y-%m-%d')
        df['prompt_full_name'] = df['prompt_name'] + ' v' + df['prompt_version']
        
        # Add trend indicators
        df['trend_direction'] = df['day_over_day_change'].apply(
            lambda x: 'Improving' if x > 0.01 else 'Declining' if x < -0.01 else 'Stable' if x is not None else 'New'
        )
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return StreamingResponse(
            io.StringIO(csv_buffer.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=accuracy_timeline.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting accuracy timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tableau/data-sources")
async def get_tableau_data_sources():
    """Get list of available data exports for Tableau"""
    return {
        "success": True,
        "data_sources": [
            {
                "name": "Prompt Performance",
                "endpoint": "/api/tableau/export/prompt-performance",
                "description": "Overall performance metrics for each prompt experiment",
                "fields": ["prompt_name", "prompt_version", "accuracy_score", "success_rate", "total_tests"],
                "visualization_suggestions": ["Bar charts", "Scatter plots", "Performance rankings"]
            },
            {
                "name": "Test Results", 
                "endpoint": "/api/tableau/export/test-results",
                "description": "Detailed test results with accuracy breakdowns",
                "fields": ["test_date", "accuracy_scores", "prompt_details", "document_info"],
                "visualization_suggestions": ["Time series", "Accuracy distributions", "Correlation analysis"]
            },
            {
                "name": "Accuracy Trends",
                "endpoint": "/api/tableau/export/accuracy-trends", 
                "description": "Daily accuracy trends and improvements over time",
                "fields": ["test_date", "daily_accuracy", "trend_direction", "improvement_over_baseline"],
                "visualization_suggestions": ["Line charts", "Trend analysis", "Performance comparison"]
            },
            {
                "name": "Field Accuracy Heatmap",
                "endpoint": "/api/tableau/export/field-accuracy-heatmap",
                "description": "Per-field accuracy scores for heatmap visualization",
                "fields": ["zone", "field_type", "accuracy_score", "prompt_name"],
                "visualization_suggestions": ["Heatmaps", "Field performance comparison", "Zone difficulty analysis"]
            },
            {
                "name": "Zone Extraction Analysis",
                "endpoint": "/api/tableau/export/zone-extraction-analysis",
                "description": "Analysis of which zones are hardest/easiest to extract",
                "fields": ["zone", "location", "extraction_difficulty", "success_rate"],
                "visualization_suggestions": ["Difficulty rankings", "Geographic analysis", "Zone type comparison"]
            }
        ],
        "usage": {
            "csv_format": "Add ?format=csv to any endpoint for CSV download",
            "json_format": "Add ?format=json for JSON response (default)",
            "tableau_connection": "Use these CSV endpoints as data sources in Tableau"
        }
    }
