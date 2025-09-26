"""
Simplified Tableau Analytics API - Export data for Tableau visualizations
"""

import logging
import io
from typing import Dict, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

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
        # Get prompt experiments data
        result = client.table('prompt_experiments').select(
            'prompt_name, prompt_version, llm_model, total_tests, '
            'successful_extractions, failed_extractions, '
            'average_accuracy_score, average_field_accuracy, average_zone_accuracy, '
            'is_baseline, is_active, created_at, last_tested_at'
        ).execute()
        
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
        
        # Create CSV manually
        csv_lines = []
        
        # Header
        headers = [
            'prompt_name', 'prompt_version', 'llm_model', 'total_tests',
            'successful_extractions', 'failed_extractions', 'average_accuracy_score',
            'average_field_accuracy', 'average_zone_accuracy', 'success_rate',
            'is_baseline', 'is_active', 'created_at', 'last_tested_at'
        ]
        csv_lines.append(','.join(headers))
        
        # Data rows
        for row in data:
            success_rate = row['successful_extractions'] / row['total_tests'] if row['total_tests'] > 0 else 0
            csv_row = [
                str(row.get('prompt_name', '')),
                str(row.get('prompt_version', '')),
                str(row.get('llm_model', '')),
                str(row.get('total_tests', 0)),
                str(row.get('successful_extractions', 0)),
                str(row.get('failed_extractions', 0)),
                str(row.get('average_accuracy_score', 0)),
                str(row.get('average_field_accuracy', 0)),
                str(row.get('average_zone_accuracy', 0)),
                str(success_rate),
                str(row.get('is_baseline', False)),
                str(row.get('is_active', False)),
                str(row.get('created_at', '')),
                str(row.get('last_tested_at', ''))
            ]
            csv_lines.append(','.join(csv_row))
        
        csv_content = '\n'.join(csv_lines)
        
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
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get test results with joins (simplified)
        result = client.table('requirements_tests').select(
            'id, test_epoch, test_date, overall_accuracy_score, '
            'zone_identification_accuracy, field_extraction_accuracy, '
            'location_extraction_accuracy, parsed_zones_count, extraction_success, '
            'processing_time_seconds, llm_tokens_used, '
            'prompt_experiments(prompt_name, prompt_version, llm_model, is_baseline), '
            'ground_truth_documents(document_name, town, county, state, document_complexity)'
        ).gte('test_date', start_date.isoformat()).execute()
        
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data, "period": f"Last {days} days"}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No test data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=test_results.csv"}
            )
        
        # Create CSV manually with flattened structure
        csv_lines = []
        
        headers = [
            'test_id', 'test_epoch', 'test_date', 'overall_accuracy_score',
            'zone_identification_accuracy', 'field_extraction_accuracy',
            'location_extraction_accuracy', 'parsed_zones_count', 'extraction_success',
            'processing_time_seconds', 'llm_tokens_used',
            'prompt_name', 'prompt_version', 'llm_model', 'is_baseline',
            'document_name', 'town', 'county', 'state', 'document_complexity',
            'accuracy_category', 'zone_extraction_category'
        ]
        csv_lines.append(','.join(headers))
        
        for row in data:
            # Flatten nested objects
            prompt_exp = row.get('prompt_experiments', {}) or {}
            gt_doc = row.get('ground_truth_documents', {}) or {}
            
            # Add calculated fields
            accuracy = row.get('overall_accuracy_score', 0)
            accuracy_category = 'Excellent' if accuracy >= 0.9 else 'Good' if accuracy >= 0.7 else 'Needs Improvement'
            
            zone_acc = row.get('zone_identification_accuracy', 0)
            zone_category = 'Perfect' if zone_acc >= 0.95 else 'Good' if zone_acc >= 0.8 else 'Poor'
            
            csv_row = [
                str(row.get('id', '')),
                str(row.get('test_epoch', '')),
                str(row.get('test_date', '')),
                str(row.get('overall_accuracy_score', 0)),
                str(row.get('zone_identification_accuracy', 0)),
                str(row.get('field_extraction_accuracy', 0)),
                str(row.get('location_extraction_accuracy', 0)),
                str(row.get('parsed_zones_count', 0)),
                str(row.get('extraction_success', False)),
                str(row.get('processing_time_seconds', 0)),
                str(row.get('llm_tokens_used', 0)),
                str(prompt_exp.get('prompt_name', '')),
                str(prompt_exp.get('prompt_version', '')),
                str(prompt_exp.get('llm_model', '')),
                str(prompt_exp.get('is_baseline', False)),
                str(gt_doc.get('document_name', '')),
                str(gt_doc.get('town', '')),
                str(gt_doc.get('county', '')),
                str(gt_doc.get('state', '')),
                str(gt_doc.get('document_complexity', '')),
                accuracy_category,
                zone_category
            ]
            csv_lines.append(','.join(csv_row))
        
        csv_content = '\n'.join(csv_lines)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=test_results.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/requirements-data")
async def export_requirements_data(
    format: str = "csv",
    limit: int = 1000,
    client = Depends(get_supabase)
):
    """Export current requirements data for Tableau analysis"""
    try:
        # Get current requirements data
        result = client.table('requirements').select(
            'id, job_id, town, county, state, zone, data_source, '
            'interior_min_lot_area_sqft, interior_min_lot_frontage_ft, '
            'principal_front_yard_ft, principal_side_yard_ft, principal_rear_yard_ft, '
            'max_building_coverage_percent, max_lot_coverage_percent, '
            'max_height_stories, max_height_feet_total, maximum_far, '
            'extraction_confidence, created_at'
        ).limit(limit).execute()
        
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No requirements data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=requirements_data.csv"}
            )
        
        # Create CSV
        csv_lines = []
        
        if data:
            headers = list(data[0].keys())
            csv_lines.append(','.join(headers))
            
            for row in data:
                csv_row = [str(row.get(header, '')) for header in headers]
                csv_lines.append(','.join(csv_row))
        
        csv_content = '\n'.join(csv_lines)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=requirements_data.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting requirements data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/jobs-data")
async def export_jobs_data(
    format: str = "csv",
    limit: int = 1000,
    client = Depends(get_supabase)
):
    """Export jobs data for Tableau analysis"""
    try:
        result = client.table('jobs').select(
            'id, town, county, state, pdf_filename, processing_status, '
            'ai_model_used, created_at, updated_at, processing_started_at, '
            'processing_completed_at'
        ).limit(limit).execute()
        
        data = result.data
        
        if format.lower() == "json":
            return {"success": True, "data": data}
        
        if not data:
            return StreamingResponse(
                io.StringIO("No jobs data available\n"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=jobs_data.csv"}
            )
        
        # Create CSV
        csv_lines = []
        
        if data:
            headers = list(data[0].keys())
            csv_lines.append(','.join(headers))
            
            for row in data:
                csv_row = [str(row.get(header, '')) for header in headers]
                csv_lines.append(','.join(csv_row))
        
        csv_content = '\n'.join(csv_lines)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=jobs_data.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting jobs data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-sources")
async def get_tableau_data_sources():
    """Get list of available data exports for Tableau"""
    return {
        "success": True,
        "message": "Tableau-ready data sources for zoning analysis",
        "data_sources": [
            {
                "name": "Prompt Performance",
                "endpoint": "/api/tableau/export/prompt-performance?format=csv",
                "description": "A/B testing prompt performance metrics",
                "tableau_charts": ["Bar Chart (Accuracy Rankings)", "Scatter Plot (Accuracy vs Tests)", "Heat Map (Model Performance)"]
            },
            {
                "name": "Test Results Detail",
                "endpoint": "/api/tableau/export/test-results?format=csv&days=30",
                "description": "Detailed A/B test results with accuracy breakdowns",
                "tableau_charts": ["Time Series (Accuracy Trends)", "Box Plot (Accuracy Distribution)", "Histogram (Performance)"]
            },
            {
                "name": "Current Requirements Data",
                "endpoint": "/api/tableau/export/requirements-data?format=csv",
                "description": "All extracted zoning requirements from production system",
                "tableau_charts": ["Geographic Map (Requirements by Location)", "Bar Chart (Zone Types)", "Scatter Plot (Lot Size vs Setbacks)"]
            },
            {
                "name": "Processing Jobs Data", 
                "endpoint": "/api/tableau/export/jobs-data?format=csv",
                "description": "Document processing jobs and status tracking",
                "tableau_charts": ["Time Series (Processing Volume)", "Status Dashboard", "Processing Time Analysis"]
            }
        ],
        "tableau_setup": {
            "connection_method": "CSV Data Source",
            "steps": [
                "1. Download CSV from any endpoint above",
                "2. Open Tableau Desktop",
                "3. Connect to Text File (CSV)",
                "4. Select downloaded CSV file",
                "5. Build visualizations using suggested chart types"
            ]
        },
        "key_metrics": {
            "accuracy_kpis": "Target >90% overall accuracy",
            "zone_identification": "Target >95% zone detection rate", 
            "field_extraction": "Target >85% field accuracy",
            "processing_efficiency": "Track time and token usage"
        }
    }
