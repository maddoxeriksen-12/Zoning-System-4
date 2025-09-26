"""
Requirements processor for extracting and storing zoning requirements
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RequirementsProcessor:
    """Process and store zoning requirements from Grok AI responses"""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def create_job(self, document_data: dict) -> Optional[str]:
        """
        Create a job record for the uploaded document
        
        Args:
            document_data: Document information including municipality, county, state
            
        Returns:
            Job ID if created successfully, None otherwise
        """
        try:
            # Extract location information
            town = document_data.get('municipality', 'Unknown')
            county = document_data.get('county', '')
            state = document_data.get('state', 'NJ')
            
            # Call the Supabase function to create job
            result = self.client.rpc('create_job', {
                'p_town': town,
                'p_county': county,
                'p_state': state,
                'p_pdf_filename': document_data.get('filename', ''),
                'p_original_pdf_filename': document_data.get('original_filename', ''),
                'p_pdf_file_path': document_data.get('file_path', ''),
                'p_pdf_file_size': document_data.get('file_size', 0)
            }).execute()
            
            if result.data:
                job_id = result.data
                logger.info(f"Created job {job_id} for {town}, {county}, {state}")
                return job_id
            else:
                logger.error("Failed to create job: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            return None
    
    def update_job_status(self, job_id: str, status: str, ai_model: str = None) -> bool:
        """
        Update job processing status
        
        Args:
            job_id: Job UUID
            status: New status (pending, processing, completed, failed)
            ai_model: AI model used for processing
            
        Returns:
            True if updated successfully
        """
        try:
            result = self.client.rpc('update_job_status', {
                'p_job_id': job_id,
                'p_status': status,
                'p_ai_model_used': ai_model
            }).execute()
            
            logger.info(f"Updated job {job_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            return False
    
    def process_grok_response(self, job_id: str, grok_response: str, document_data: dict) -> List[str]:
        """
        Process Grok AI response and insert requirements into database
        
        Args:
            job_id: Job UUID
            grok_response: JSON string from Grok AI
            document_data: Document information including location
            
        Returns:
            List of requirement IDs created
        """
        requirement_ids = []
        
        try:
            # Parse Grok response
            if isinstance(grok_response, str):
                try:
                    parsed_data = json.loads(grok_response)
                except json.JSONDecodeError:
                    logger.error("Failed to parse Grok response as JSON")
                    return requirement_ids
            else:
                parsed_data = grok_response
            
            # Extract location information
            town = document_data.get('municipality', 'Unknown')
            county = document_data.get('county', '')
            state = document_data.get('state', 'NJ')
            
            # Get zones from parsed data
            zones = parsed_data.get('zones', [])
            extraction_confidence = parsed_data.get('extraction_confidence', 0.7)
            
            if not zones:
                logger.warning(f"No zones found in Grok response for job {job_id}")
                return requirement_ids
            
            # Process each zone
            for zone_data in zones:
                try:
                    req_id = self._insert_zone_requirements(
                        job_id=job_id,
                        town=town,
                        county=county,
                        state=state,
                        zone_data=zone_data,
                        extraction_confidence=extraction_confidence
                    )
                    
                    if req_id:
                        requirement_ids.append(req_id)
                        logger.info(f"Created requirement {req_id} for zone {zone_data.get('zone')} in {town}, {state}")
                    
                except Exception as e:
                    logger.error(f"Error processing zone {zone_data.get('zone')}: {str(e)}")
                    continue
            
            return requirement_ids
            
        except Exception as e:
            logger.error(f"Error processing Grok response: {str(e)}")
            return requirement_ids
    
    def _insert_zone_requirements(self, job_id: str, town: str, county: str, state: str, 
                                   zone_data: dict, extraction_confidence: float) -> Optional[str]:
        """
        Insert requirements for a specific zone
        
        Args:
            job_id: Job UUID
            town: Town/municipality name
            county: County name
            state: State code
            zone_data: Zone-specific requirements data
            extraction_confidence: Confidence score
            
        Returns:
            Requirement ID if created successfully
        """
        try:
            # Extract all fields from zone data
            interior = zone_data.get('interior_lots', {})
            corner = zone_data.get('corner_lots', {})
            lot_req = zone_data.get('lot_requirements', {})
            principal_yards = zone_data.get('principal_building_yards', {})
            accessory_yards = zone_data.get('accessory_building_yards', {})
            coverage = zone_data.get('coverage_and_height', {})
            floor_area = zone_data.get('floor_area', {})
            intensity = zone_data.get('development_intensity', {})
            
            # Call the Supabase function to insert requirement
            result = self.client.rpc('insert_requirement', {
                'p_job_id': job_id,
                'p_town': town,
                'p_county': county,
                'p_state': state,
                'p_zone': zone_data.get('zone', 'Unknown'),
                'p_data_source': 'AI_Extracted',
                'p_extraction_confidence': extraction_confidence,
                
                # Interior lots
                'p_interior_min_lot_area_sqft': self._safe_numeric(interior.get('min_lot_area_sqft')),
                'p_interior_min_lot_frontage_ft': self._safe_numeric(interior.get('min_lot_frontage_ft')),
                'p_interior_min_lot_width_ft': self._safe_numeric(interior.get('min_lot_width_ft')),
                'p_interior_min_lot_depth_ft': self._safe_numeric(interior.get('min_lot_depth_ft')),
                
                # Corner lots
                'p_corner_min_lot_area_sqft': self._safe_numeric(corner.get('min_lot_area_sqft')),
                'p_corner_min_lot_frontage_ft': self._safe_numeric(corner.get('min_lot_frontage_ft')),
                'p_corner_min_lot_width_ft': self._safe_numeric(corner.get('min_lot_width_ft')),
                'p_corner_min_lot_depth_ft': self._safe_numeric(corner.get('min_lot_depth_ft')),
                
                # Other lot requirements
                'p_min_circle_diameter_ft': self._safe_numeric(lot_req.get('min_circle_diameter_ft')),
                'p_buildable_lot_area_sqft': self._safe_numeric(lot_req.get('buildable_lot_area_sqft')),
                
                # Principal building yards
                'p_principal_front_yard_ft': self._safe_numeric(principal_yards.get('front_yard_ft')),
                'p_principal_side_yard_ft': self._safe_numeric(principal_yards.get('side_yard_ft')),
                'p_principal_street_side_yard_ft': self._safe_numeric(principal_yards.get('street_side_yard_ft')),
                'p_principal_rear_yard_ft': self._safe_numeric(principal_yards.get('rear_yard_ft')),
                'p_principal_street_rear_yard_ft': self._safe_numeric(principal_yards.get('street_rear_yard_ft')),
                
                # Accessory building yards
                'p_accessory_front_yard_ft': self._safe_numeric(accessory_yards.get('front_yard_ft')),
                'p_accessory_side_yard_ft': self._safe_numeric(accessory_yards.get('side_yard_ft')),
                'p_accessory_street_side_yard_ft': self._safe_numeric(accessory_yards.get('street_side_yard_ft')),
                'p_accessory_rear_yard_ft': self._safe_numeric(accessory_yards.get('rear_yard_ft')),
                'p_accessory_street_rear_yard_ft': self._safe_numeric(accessory_yards.get('street_rear_yard_ft')),
                
                # Coverage and height
                'p_max_building_coverage_percent': self._safe_numeric(coverage.get('max_building_coverage_percent')),
                'p_max_lot_coverage_percent': self._safe_numeric(coverage.get('max_lot_coverage_percent')),
                'p_max_height_stories': self._safe_integer(coverage.get('max_height_stories')),
                'p_max_height_feet_total': self._safe_numeric(coverage.get('max_height_feet')),
                
                # Floor area
                'p_min_gross_floor_area_first_floor_sqft': self._safe_numeric(floor_area.get('min_gross_floor_area_first_floor_sqft')),
                'p_min_gross_floor_area_multistory_sqft': self._safe_numeric(floor_area.get('min_gross_floor_area_multistory_sqft')),
                'p_max_gross_floor_area_all_structures_sqft': self._safe_numeric(floor_area.get('max_gross_floor_area_all_structures_sqft')),
                
                # Development intensity
                'p_maximum_far': self._safe_numeric(intensity.get('maximum_far')),
                'p_maximum_density_units_per_acre': self._safe_numeric(intensity.get('maximum_density_units_per_acre'))
            }).execute()
            
            if result.data:
                return result.data
            else:
                logger.error("Failed to insert requirement: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting zone requirements: {str(e)}")
            return None
    
    def _safe_numeric(self, value: Any) -> Optional[float]:
        """Convert value to float or return None"""
        if value is None or value == 'null':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_integer(self, value: Any) -> Optional[int]:
        """Convert value to integer or return None"""
        if value is None or value == 'null':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
