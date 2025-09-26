"""
A/B Testing Service for Prompt Optimization and Accuracy Tracking
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

from ..core.supabase_client import get_supabase_client
from ..core.config import settings
from .grok_service import GrokService

logger = logging.getLogger(__name__)

@dataclass
class PromptExperiment:
    """Data class for prompt experiments"""
    id: Optional[str]
    prompt_name: str
    prompt_version: str
    prompt_text: str
    llm_model: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    is_baseline: bool = False
    temperature: float = 0.1
    max_tokens: int = 8000

@dataclass
class GroundTruthDocument:
    """Data class for ground truth documents"""
    id: Optional[str]
    document_name: str
    original_filename: str
    town: str
    county: Optional[str]
    state: str
    verified_by: str
    number_of_zones: int
    complexity: str = 'medium'
    file_path: Optional[str] = None

@dataclass
class GroundTruthRequirement:
    """Data class for ground truth zoning requirements"""
    id: Optional[str]
    ground_truth_doc_id: str
    zone: str
    zone_description: Optional[str] = None
    
    # Zone requirements (same fields as regular requirements)
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

class ABTestingService:
    """Service for managing A/B testing of zoning extraction prompts"""
    
    def __init__(self):
        self.client = get_supabase_client()
        if not self.client:
            raise Exception("Supabase client not initialized")
        self.grok_service = GrokService()
    
    def create_prompt_experiment(self, experiment: PromptExperiment) -> str:
        """Create a new prompt experiment"""
        try:
            result = self.client.rpc('create_prompt_experiment', {
                'p_prompt_name': experiment.prompt_name,
                'p_prompt_version': experiment.prompt_version,
                'p_prompt_text': experiment.prompt_text,
                'p_llm_model': experiment.llm_model,
                'p_description': experiment.description,
                'p_hypothesis': experiment.hypothesis,
                'p_is_baseline': experiment.is_baseline,
                'p_temperature': experiment.temperature,
                'p_max_tokens': experiment.max_tokens
            }).execute()
            
            experiment_id = result.data
            logger.info(f"Created prompt experiment: {experiment.prompt_name} v{experiment.prompt_version}")
            return experiment_id
            
        except Exception as e:
            logger.error(f"Error creating prompt experiment: {e}")
            raise
    
    def create_ground_truth_document(self, doc: GroundTruthDocument) -> str:
        """Create a ground truth document"""
        try:
            result = self.client.rpc('create_ground_truth_document', {
                'p_document_name': doc.document_name,
                'p_original_filename': doc.original_filename,
                'p_town': doc.town,
                'p_county': doc.county,
                'p_state': doc.state,
                'p_verified_by': doc.verified_by,
                'p_number_of_zones': doc.number_of_zones,
                'p_complexity': doc.complexity,
                'p_file_path': doc.file_path
            }).execute()
            
            doc_id = result.data
            logger.info(f"Created ground truth document: {doc.document_name}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error creating ground truth document: {e}")
            raise
    
    def add_ground_truth_requirement(self, req: GroundTruthRequirement) -> str:
        """Add a ground truth zoning requirement"""
        try:
            result = self.client.rpc('add_ground_truth_requirement', {
                'p_ground_truth_doc_id': req.ground_truth_doc_id,
                'p_zone': req.zone,
                'p_zone_description': req.zone_description,
                'p_interior_min_lot_area_sqft': req.interior_min_lot_area_sqft,
                'p_interior_min_lot_frontage_ft': req.interior_min_lot_frontage_ft,
                'p_interior_min_lot_width_ft': req.interior_min_lot_width_ft,
                'p_interior_min_lot_depth_ft': req.interior_min_lot_depth_ft,
                'p_principal_front_yard_ft': req.principal_front_yard_ft,
                'p_principal_side_yard_ft': req.principal_side_yard_ft,
                'p_principal_rear_yard_ft': req.principal_rear_yard_ft,
                'p_max_building_coverage_percent': req.max_building_coverage_percent,
                'p_max_lot_coverage_percent': req.max_lot_coverage_percent,
                'p_max_height_stories': req.max_height_stories,
                'p_max_height_feet_total': req.max_height_feet_total,
                'p_maximum_far': req.maximum_far,
                'p_maximum_density_units_per_acre': req.maximum_density_units_per_acre
            }).execute()
            
            req_id = result.data
            logger.info(f"Added ground truth requirement for zone {req.zone}")
            return req_id
            
        except Exception as e:
            logger.error(f"Error adding ground truth requirement: {e}")
            raise
    
    def run_ab_test(self, 
                    prompt_experiment_id: str,
                    ground_truth_doc_id: str,
                    document_text: str,
                    test_epoch: int = 1,
                    test_batch_id: Optional[str] = None) -> Dict[str, Any]:
        """Run A/B test comparing AI extraction against ground truth"""
        
        start_time = datetime.utcnow()
        
        try:
            # Get prompt experiment details
            prompt_result = self.client.table('prompt_experiments').select('*').eq('id', prompt_experiment_id).execute()
            if not prompt_result.data:
                raise Exception(f"Prompt experiment {prompt_experiment_id} not found")
            
            prompt_exp = prompt_result.data[0]
            
            # Get ground truth data
            gt_result = self.client.table('ground_truth_documents').select('*').eq('id', ground_truth_doc_id).execute()
            if not gt_result.data:
                raise Exception(f"Ground truth document {ground_truth_doc_id} not found")
            
            gt_doc = gt_result.data[0]
            
            # Get ground truth requirements
            gt_reqs_result = self.client.table('ground_truth_requirements').select('*').eq('ground_truth_doc_id', ground_truth_doc_id).execute()
            ground_truth_reqs = gt_reqs_result.data
            
            logger.info(f"🧪 Running A/B test: {prompt_exp['prompt_name']} v{prompt_exp['prompt_version']} on {gt_doc['document_name']}")
            
            # Run AI extraction using the specific prompt
            ai_result = self._run_ai_extraction(prompt_exp, document_text, gt_doc)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate accuracy scores
            accuracy_scores = self._calculate_accuracy(ai_result.get('zones', []), ground_truth_reqs, gt_doc)
            
            # Record test results
            test_result_id = self._record_test_result(
                prompt_experiment_id=prompt_experiment_id,
                ground_truth_doc_id=ground_truth_doc_id,
                test_epoch=test_epoch,
                raw_response=ai_result.get('raw_response', ''),
                parsed_zones=ai_result.get('zones', []),
                extraction_success=ai_result.get('success', False),
                accuracy_scores=accuracy_scores,
                processing_time=processing_time,
                tokens_used=ai_result.get('tokens_used'),
                test_batch_id=test_batch_id
            )
            
            logger.info(f"✅ A/B test completed. Overall accuracy: {accuracy_scores['overall_accuracy']:.2%}")
            
            return {
                'test_id': test_result_id,
                'success': True,
                'accuracy_scores': accuracy_scores,
                'ai_zones_found': len(ai_result.get('zones', [])),
                'ground_truth_zones': len(ground_truth_reqs),
                'processing_time': processing_time,
                'prompt_name': f"{prompt_exp['prompt_name']} v{prompt_exp['prompt_version']}"
            }
            
        except Exception as e:
            logger.error(f"A/B test failed: {e}")
            
            # Still record the failed test
            try:
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                self._record_test_result(
                    prompt_experiment_id=prompt_experiment_id,
                    ground_truth_doc_id=ground_truth_doc_id,
                    test_epoch=test_epoch,
                    raw_response=str(e),
                    parsed_zones=[],
                    extraction_success=False,
                    accuracy_scores={'overall_accuracy': 0.0, 'zone_accuracy': 0.0, 'field_accuracy': 0.0, 'location_accuracy': 0.0},
                    processing_time=processing_time,
                    test_batch_id=test_batch_id
                )
            except:
                pass
            
            return {'success': False, 'error': str(e)}
    
    def _run_ai_extraction(self, prompt_exp: Dict, document_text: str, gt_doc: Dict) -> Dict[str, Any]:
        """Run AI extraction using specific prompt"""
        
        # Create a temporary Grok service with the experiment settings
        temp_grok = GrokService()
        temp_grok.model = prompt_exp['llm_model']
        temp_grok.temperature = prompt_exp['llm_temperature']
        temp_grok.max_tokens = prompt_exp['llm_max_tokens']
        
        # Override the prompt
        original_prompt_method = temp_grok.process_zoning_document
        
        def custom_prompt_extraction(text_content, municipality=None, county=None, state="NJ"):
            """Custom extraction using the experiment prompt"""
            try:
                headers = temp_grok._get_headers()
                
                # Use the experimental prompt
                custom_prompt = prompt_exp['prompt_text'].format(
                    text_content=text_content,
                    municipality=municipality or gt_doc['town'],
                    county=county or gt_doc['county'],
                    state=state
                )
                
                payload = {
                    "model": temp_grok.model,
                    "messages": [{"role": "user", "content": custom_prompt}],
                    "max_tokens": temp_grok.max_tokens,
                    "temperature": temp_grok.temperature
                }
                
                import requests
                response = requests.post(
                    f"{temp_grok.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Parse the response to extract zones
                    zones = self._parse_ai_response(content)
                    
                    return {
                        "success": True,
                        "raw_response": content,
                        "zones": zones,
                        "tokens_used": result.get("usage", {}).get("total_tokens"),
                        "model": temp_grok.model
                    }
                else:
                    return {
                        "success": False,
                        "error": f"AI API error: {response.status_code} - {response.text}",
                        "raw_response": response.text
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "raw_response": ""
                }
        
        # Run extraction
        return custom_prompt_extraction(
            document_text,
            municipality=gt_doc['town'],
            county=gt_doc.get('county'),
            state=gt_doc.get('state', 'NJ')
        )
    
    def _parse_ai_response(self, response_text: str) -> List[Dict]:
        """Parse AI response to extract zones"""
        try:
            # Try to find JSON in the response
            import re
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Look for zones in various possible keys
                for key in ['zones', 'zoning_requirements', 'requirements', 'extracted_zones']:
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
                
                # If it's a single zone, wrap in list
                if 'zone' in parsed or 'zone_name' in parsed:
                    return [parsed]
                    
            return []
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return []
    
    def _calculate_accuracy(self, ai_zones: List[Dict], ground_truth_reqs: List[Dict], gt_doc: Dict) -> Dict[str, float]:
        """Calculate comprehensive accuracy scores"""
        
        if not ground_truth_reqs:
            return {'overall_accuracy': 0.0, 'zone_accuracy': 0.0, 'field_accuracy': 0.0, 'location_accuracy': 0.0}
        
        # Zone identification accuracy
        gt_zone_names = {req['zone'].upper() for req in ground_truth_reqs}
        ai_zone_names = set()
        
        for zone in ai_zones:
            zone_name = zone.get('zone_name') or zone.get('zone', 'unknown')
            ai_zone_names.add(str(zone_name).upper())
        
        zone_accuracy = len(gt_zone_names.intersection(ai_zone_names)) / len(gt_zone_names)
        
        # Field-level accuracy
        total_field_scores = []
        
        for gt_req in ground_truth_reqs:
            # Find matching AI zone
            matching_ai_zone = None
            for ai_zone in ai_zones:
                ai_zone_name = (ai_zone.get('zone_name') or ai_zone.get('zone', '')).upper()
                if ai_zone_name == gt_req['zone'].upper():
                    matching_ai_zone = ai_zone
                    break
            
            if matching_ai_zone:
                # Calculate field accuracy for this zone
                field_scores = self._calculate_zone_field_accuracy(matching_ai_zone, gt_req)
                total_field_scores.extend(field_scores)
        
        field_accuracy = sum(total_field_scores) / len(total_field_scores) if total_field_scores else 0.0
        
        # Location accuracy (if AI extracted location info)
        location_accuracy = 1.0  # Default to perfect if not testing location
        
        # Overall accuracy (weighted combination)
        overall_accuracy = (zone_accuracy * 0.4 + field_accuracy * 0.6)
        
        return {
            'overall_accuracy': overall_accuracy,
            'zone_accuracy': zone_accuracy,
            'field_accuracy': field_accuracy,
            'location_accuracy': location_accuracy
        }
    
    def _calculate_zone_field_accuracy(self, ai_zone: Dict, gt_req: Dict, tolerance_percent: float = 5.0) -> List[float]:
        """Calculate accuracy for individual fields within a zone"""
        
        field_mappings = {
            # Map AI field names to ground truth field names
            'interior_min_lot_area_sqft': 'interior_min_lot_area_sqft',
            'interior_min_lot_frontage_ft': 'interior_min_lot_frontage_ft',
            'interior_min_lot_width_ft': 'interior_min_lot_width_ft',
            'interior_min_lot_depth_ft': 'interior_min_lot_depth_ft',
            'principal_min_front_yard_ft': 'principal_front_yard_ft',
            'principal_front_yard_ft': 'principal_front_yard_ft',
            'principal_min_side_yard_ft': 'principal_side_yard_ft',
            'principal_side_yard_ft': 'principal_side_yard_ft',
            'principal_min_rear_yard_ft': 'principal_rear_yard_ft',
            'principal_rear_yard_ft': 'principal_rear_yard_ft',
            'max_building_coverage_percent': 'max_building_coverage_percent',
            'max_lot_coverage_percent': 'max_lot_coverage_percent',
            'principal_max_height_stories': 'max_height_stories',
            'max_height_stories': 'max_height_stories',
            'principal_max_height_feet': 'max_height_feet_total',
            'max_height_feet_total': 'max_height_feet_total',
            'maximum_far': 'maximum_far',
            'max_far': 'maximum_far',
            'maximum_density_units_per_acre': 'maximum_density_units_per_acre'
        }
        
        scores = []
        
        for ai_field, gt_field in field_mappings.items():
            if ai_field in ai_zone and gt_field in gt_req:
                ai_value = ai_zone[ai_field]
                gt_value = gt_req[gt_field]
                
                score = self._calculate_field_accuracy_score(ai_value, gt_value, tolerance_percent)
                scores.append(score)
        
        return scores
    
    def _calculate_field_accuracy_score(self, predicted: Any, actual: Any, tolerance_percent: float = 5.0) -> float:
        """Calculate accuracy score for a single field"""
        
        # Handle NULL cases
        if predicted is None and actual is None:
            return 1.0  # Both null = perfect match
        
        if (predicted is None) != (actual is None):
            return 0.0  # One null, one not = no match
        
        # Both have values
        try:
            predicted_num = float(predicted)
            actual_num = float(actual)
            
            if actual_num == 0:
                return 1.0 if predicted_num == 0 else 0.0
            
            percent_diff = abs((predicted_num - actual_num) / actual_num) * 100
            
            if percent_diff <= tolerance_percent:
                return 1.0
            else:
                # Linear decay
                return max(0.0, 1.0 - (percent_diff / 100.0))
                
        except (ValueError, TypeError):
            # Handle string comparisons
            return 1.0 if str(predicted).lower() == str(actual).lower() else 0.0
    
    def _record_test_result(self, 
                           prompt_experiment_id: str,
                           ground_truth_doc_id: str,
                           test_epoch: int,
                           raw_response: str,
                           parsed_zones: List[Dict],
                           extraction_success: bool,
                           accuracy_scores: Dict[str, float],
                           processing_time: float,
                           tokens_used: Optional[int] = None,
                           test_batch_id: Optional[str] = None) -> str:
        """Record test results in database"""
        
        try:
            result = self.client.rpc('record_test_result', {
                'p_prompt_experiment_id': prompt_experiment_id,
                'p_ground_truth_doc_id': ground_truth_doc_id,
                'p_test_epoch': test_epoch,
                'p_raw_response': raw_response,
                'p_parsed_zones_count': len(parsed_zones),
                'p_extraction_success': extraction_success,
                'p_overall_accuracy': accuracy_scores['overall_accuracy'],
                'p_zone_accuracy': accuracy_scores['zone_accuracy'],
                'p_field_accuracy': accuracy_scores['field_accuracy'],
                'p_location_accuracy': accuracy_scores['location_accuracy'],
                'p_processing_time': processing_time,
                'p_tokens_used': tokens_used,
                'p_test_batch_id': test_batch_id
            }).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error recording test result: {e}")
            raise
    
    def get_best_prompts(self, min_tests: int = 5, limit: int = 10) -> List[Dict]:
        """Get best performing prompts"""
        
        result = self.client.rpc('get_best_prompts', {
            'p_min_tests': min_tests,
            'p_limit': limit
        }).execute()
        
        return result.data
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get detailed results for a specific experiment"""
        
        # Get experiment details
        exp_result = self.client.table('prompt_experiments').select('*').eq('id', experiment_id).execute()
        if not exp_result.data:
            raise Exception(f"Experiment {experiment_id} not found")
        
        experiment = exp_result.data[0]
        
        # Get test results
        test_results = self.client.table('requirements_tests').select('*').eq('prompt_experiment_id', experiment_id).execute()
        
        return {
            'experiment': experiment,
            'test_results': test_results.data,
            'total_tests': len(test_results.data),
            'avg_accuracy': sum(t['overall_accuracy_score'] for t in test_results.data) / len(test_results.data) if test_results.data else 0.0
        }
