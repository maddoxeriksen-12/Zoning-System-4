"""
API endpoints for A/B testing and prompt optimization system
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, validator
from fastapi.responses import JSONResponse

from ..core.database import get_db
from ..services.ab_testing_service import ABTestingService, PromptExperiment, GroundTruthDocument, GroundTruthRequirement

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class PromptExperimentCreate(BaseModel):
    prompt_name: str
    prompt_version: str
    prompt_text: str
    llm_model: str = "grok-4-fast-reasoning"
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    is_baseline: bool = False
    temperature: float = 0.1
    max_tokens: int = 8000
    
    @validator('prompt_name')
    def validate_prompt_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Prompt name must be at least 2 characters')
        return v.strip()

class GroundTruthDocumentCreate(BaseModel):
    document_name: str
    original_filename: str
    town: str
    county: Optional[str] = None
    state: str = "NJ"
    verified_by: str
    number_of_zones: int
    complexity: str = "medium"
    file_path: Optional[str] = None
    verification_notes: Optional[str] = None
    
    @validator('complexity')
    def validate_complexity(cls, v):
        if v not in ['simple', 'medium', 'complex']:
            raise ValueError('Complexity must be simple, medium, or complex')
        return v

class GroundTruthRequirementCreate(BaseModel):
    ground_truth_doc_id: str
    zone: str
    zone_description: Optional[str] = None
    
    # Zoning fields (matching database schema)
    interior_min_lot_area_sqft: Optional[float] = None
    interior_min_lot_frontage_ft: Optional[float] = None
    interior_min_lot_width_ft: Optional[float] = None
    interior_min_lot_depth_ft: Optional[float] = None
    principal_front_yard_ft: Optional[float] = None
    principal_side_yard_ft: Optional[float] = None
    principal_rear_yard_ft: Optional[float] = None
    max_building_coverage_percent: Optional[float] = None
    max_lot_coverage_percent: Optional[float] = None
    max_height_stories: Optional[int] = None
    max_height_feet_total: Optional[float] = None
    maximum_far: Optional[float] = None
    maximum_density_units_per_acre: Optional[float] = None

class ABTestRequest(BaseModel):
    prompt_experiment_id: str
    ground_truth_doc_id: str
    document_text: str
    test_epoch: int = 1
    test_batch_id: Optional[str] = None

# Get AB testing service
def get_ab_testing_service() -> ABTestingService:
    return ABTestingService()

@router.get("/experiments")
async def list_prompt_experiments(
    active_only: bool = True,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """List all prompt experiments"""
    try:
        experiments = ab_service.client.table('prompt_experiments').select('*')
        if active_only:
            experiments = experiments.eq('is_active', True)
        
        result = experiments.order('average_accuracy_score', desc=True).execute()
        
        return {
            "success": True,
            "experiments": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiments")
async def create_prompt_experiment(
    experiment_data: PromptExperimentCreate,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Create a new prompt experiment"""
    try:
        experiment = PromptExperiment(
            id=None,
            prompt_name=experiment_data.prompt_name,
            prompt_version=experiment_data.prompt_version,
            prompt_text=experiment_data.prompt_text,
            llm_model=experiment_data.llm_model,
            description=experiment_data.description,
            hypothesis=experiment_data.hypothesis,
            is_baseline=experiment_data.is_baseline,
            temperature=experiment_data.temperature,
            max_tokens=experiment_data.max_tokens
        )
        
        experiment_id = ab_service.create_prompt_experiment(experiment)
        
        return {
            "success": True,
            "experiment_id": experiment_id,
            "message": f"Created experiment: {experiment_data.prompt_name} v{experiment_data.prompt_version}"
        }
        
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/{experiment_id}")
async def get_experiment_details(
    experiment_id: str,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get detailed information about a specific experiment"""
    try:
        results = ab_service.get_experiment_results(experiment_id)
        return {
            "success": True,
            "experiment": results['experiment'],
            "test_results": results['test_results'],
            "summary": {
                "total_tests": results['total_tests'],
                "average_accuracy": results['avg_accuracy']
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting experiment details: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/experiments/{experiment_id}/toggle")
async def toggle_experiment(
    experiment_id: str,
    is_active: bool,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Activate or deactivate an experiment"""
    try:
        result = ab_service.client.rpc('toggle_prompt_experiment', {
            'p_experiment_id': experiment_id,
            'p_is_active': is_active
        }).execute()
        
        status = "activated" if is_active else "deactivated"
        return {
            "success": True,
            "message": f"Experiment {status} successfully"
        }
        
    except Exception as e:
        logger.error(f"Error toggling experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ground-truth/documents")
async def list_ground_truth_documents(
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """List all ground truth documents"""
    try:
        result = ab_service.client.from_('ground_truth_overview').select('*').execute()
        
        return {
            "success": True,
            "documents": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        logger.error(f"Error listing ground truth documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ground-truth/documents")
async def create_ground_truth_document(
    doc_data: GroundTruthDocumentCreate,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Create a new ground truth document"""
    try:
        document = GroundTruthDocument(
            id=None,
            document_name=doc_data.document_name,
            original_filename=doc_data.original_filename,
            town=doc_data.town,
            county=doc_data.county,
            state=doc_data.state,
            verified_by=doc_data.verified_by,
            number_of_zones=doc_data.number_of_zones,
            complexity=doc_data.complexity,
            file_path=doc_data.file_path
        )
        
        doc_id = ab_service.create_ground_truth_document(document)
        
        return {
            "success": True,
            "document_id": doc_id,
            "message": f"Created ground truth document: {doc_data.document_name}"
        }
        
    except Exception as e:
        logger.error(f"Error creating ground truth document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ground-truth/requirements")
async def add_ground_truth_requirement(
    req_data: GroundTruthRequirementCreate,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Add a ground truth zoning requirement"""
    try:
        requirement = GroundTruthRequirement(
            id=None,
            ground_truth_doc_id=req_data.ground_truth_doc_id,
            zone=req_data.zone,
            zone_description=req_data.zone_description,
            interior_min_lot_area_sqft=req_data.interior_min_lot_area_sqft,
            interior_min_lot_frontage_ft=req_data.interior_min_lot_frontage_ft,
            interior_min_lot_width_ft=req_data.interior_min_lot_width_ft,
            interior_min_lot_depth_ft=req_data.interior_min_lot_depth_ft,
            principal_front_yard_ft=req_data.principal_front_yard_ft,
            principal_side_yard_ft=req_data.principal_side_yard_ft,
            principal_rear_yard_ft=req_data.principal_rear_yard_ft,
            max_building_coverage_percent=req_data.max_building_coverage_percent,
            max_lot_coverage_percent=req_data.max_lot_coverage_percent,
            max_height_stories=req_data.max_height_stories,
            max_height_feet_total=req_data.max_height_feet_total,
            maximum_far=req_data.maximum_far,
            maximum_density_units_per_acre=req_data.maximum_density_units_per_acre
        )
        
        req_id = ab_service.add_ground_truth_requirement(requirement)
        
        return {
            "success": True,
            "requirement_id": req_id,
            "message": f"Added ground truth requirement for zone {req_data.zone}"
        }
        
    except Exception as e:
        logger.error(f"Error adding ground truth requirement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ground-truth/documents/{doc_id}/requirements")
async def get_ground_truth_requirements(
    doc_id: str,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get all requirements for a ground truth document"""
    try:
        result = ab_service.client.table('ground_truth_requirements').select('*').eq('ground_truth_doc_id', doc_id).execute()
        
        return {
            "success": True,
            "requirements": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        logger.error(f"Error getting ground truth requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/run")
async def run_ab_test(
    test_request: ABTestRequest,
    background_tasks: BackgroundTasks,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Run an A/B test comparing AI extraction against ground truth"""
    try:
        # Run test in background to avoid timeouts
        def run_test_background():
            try:
                result = ab_service.run_ab_test(
                    prompt_experiment_id=test_request.prompt_experiment_id,
                    ground_truth_doc_id=test_request.ground_truth_doc_id,
                    document_text=test_request.document_text,
                    test_epoch=test_request.test_epoch,
                    test_batch_id=test_request.test_batch_id
                )
                logger.info(f"A/B test completed: {result}")
            except Exception as e:
                logger.error(f"Background A/B test failed: {e}")
        
        background_tasks.add_task(run_test_background)
        
        return {
            "success": True,
            "message": "A/B test started in background",
            "test_batch_id": test_request.test_batch_id
        }
        
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/best-prompts")
async def get_best_prompts(
    min_tests: int = 5,
    limit: int = 10,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get the best performing prompts"""
    try:
        best_prompts = ab_service.get_best_prompts(min_tests=min_tests, limit=limit)
        
        return {
            "success": True,
            "best_prompts": best_prompts,
            "criteria": f"Minimum {min_tests} tests, sorted by accuracy"
        }
        
    except Exception as e:
        logger.error(f"Error getting best prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/summary")
async def get_test_summary(
    days: int = 30,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get summary of testing results"""
    try:
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        result = ab_service.client.rpc('generate_test_summary', {
            'p_start_date': start_date.isoformat(),
            'p_end_date': end_date.isoformat()
        }).execute()
        
        summary = result.data[0] if result.data else {}
        
        return {
            "success": True,
            "summary": summary,
            "period": f"Last {days} days"
        }
        
    except Exception as e:
        logger.error(f"Error generating test summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/document/{doc_id}")
async def get_document_test_results(
    doc_id: str,
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get all test results for a specific ground truth document"""
    try:
        result = ab_service.client.rpc('get_document_test_results', {
            'p_ground_truth_doc_id': doc_id
        }).execute()
        
        return {
            "success": True,
            "document_id": doc_id,
            "test_results": result.data,
            "total_tests": len(result.data)
        }
        
    except Exception as e:
        logger.error(f"Error getting document test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ab_testing_health_check():
    """Health check for A/B testing service"""
    try:
        ab_service = ABTestingService()
        
        # Check if we can connect to database
        result = ab_service.client.table('prompt_experiments').select('count').execute()
        
        return {
            "status": "healthy",
            "service": "A/B Testing API",
            "experiments_count": result.count if hasattr(result, 'count') else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"A/B testing health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
