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
            
            # If town is Unknown, use filename as unique identifier to avoid conflicts
            if town == 'Unknown' or not town:
                # Extract a unique identifier from filename
                filename = document_data.get('original_filename', document_data.get('filename', ''))
                if filename:
                    # Use first part of filename as town identifier
                    town = f"Unknown_{filename[:30].replace('.', '_')}"
                else:
                    # Use timestamp to make it unique
                    import time
                    town = f"Unknown_{int(time.time())}"
            
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
    
    def process_grok_response_with_validation(self, job_id: str, grok_response: str, document_data: dict) -> List[str]:
        """
        Process Grok AI response with robust validation and insert requirements into database
        
        Args:
            job_id: Job UUID
            grok_response: JSON string from Grok AI
            document_data: Document information including location
            
        Returns:
            List of requirement IDs created
        """
        # Validate input data first - handle None values
        town = (document_data.get('municipality') or '').strip()
        county = (document_data.get('county') or '').strip() 
        state = (document_data.get('state') or 'NJ').strip()
        
        # Ensure we have a valid town name (NOT NULL constraint)
        if not town or town.lower() == 'unknown':
            # Try to extract from filename as fallback
            filename = document_data.get('original_filename', document_data.get('filename', ''))
            if filename:
                # Clean filename to use as town identifier
                import re
                clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', filename.split('.')[0])[:30]
                town = f"Document_{clean_name}"
                logger.info(f"Using filename-derived town: {town}")
            else:
                town = f"Job_{job_id[:8]}"
                logger.info(f"Using job-derived town: {town}")
        
        if not county:
            county = "Unknown County"
        
        # Update document_data with validated values
        validated_data = document_data.copy()
        validated_data.update({
            'municipality': town,
            'county': county, 
            'state': state
        })
        
        logger.info(f"🔍 Validated data: town='{town}', county='{county}', state='{state}'")
        
        return self.process_grok_response(job_id, grok_response, validated_data)
    
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
            # Log the raw response for debugging
            logger.info(f"Processing Grok response for job {job_id}")
            logger.debug(f"Raw Grok response (first 500 chars): {str(grok_response)[:500]}")
            
            # Parse Grok response with improved error handling
            if isinstance(grok_response, str):
                try:
                    # First try parsing the response as-is
                    parsed_data = json.loads(grok_response)
                except json.JSONDecodeError:
                    try:
                        # Try to find JSON in the response (sometimes Grok adds extra text)
                        json_start = grok_response.find('{')
                        json_end = grok_response.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = grok_response[json_start:json_end]
                            # Try to fix common JSON issues
                            json_str = self._fix_json_string(json_str)
                            parsed_data = json.loads(json_str)
                        else:
                            logger.error("No valid JSON structure found in Grok response")
                            return self._extract_zones_fallback(job_id, grok_response, document_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Grok response as JSON after cleanup: {e}")
                        logger.error(f"Response snippet: {grok_response[:500]}...")
                        # Try to extract zones even from malformed response
                        return self._extract_zones_fallback(job_id, grok_response, document_data)
            else:
                parsed_data = grok_response
            
            # Handle wrapped structures like {"raw_response": "{actual json}"}
            if isinstance(parsed_data, dict) and 'raw_response' in parsed_data:
                raw_str = parsed_data['raw_response']
                if isinstance(raw_str, str):
                    try:
                        parsed_data = json.loads(raw_str)
                        logger.info("Successfully parsed nested raw_response JSON")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse raw_response: {e}")
                        return self._extract_zones_fallback(job_id, grok_response, document_data)

            # Flexible zone key lookup
            zones = []
            possible_zone_keys = ['zones', 'zoning_requirements', 'requirements', 'extracted_zones', 'districts']
            for key in possible_zone_keys:
                if key in parsed_data:
                    zones = parsed_data[key]
                    logger.info(f"Found zones using key '{key}': {len(zones)} zones")
                    break
            
            if not zones and isinstance(parsed_data, dict):
                # Look for any list that looks like zones
                for key, value in parsed_data.items():
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        if any(k in value[0] for k in ['zone', 'district', 'zoning', 'Zone']):
                            zones = value
                            logger.info(f"Found zones using fallback key '{key}': {len(zones)} zones")
                            break

            extraction_confidence = parsed_data.get('extraction_confidence', 0.7)
            
            if not zones:
                logger.warning(f"No zones found in Grok response for job {job_id}")
                return requirement_ids
            
            # Extract location information from document_data
            town = document_data.get('municipality', 'Unknown')
            county = document_data.get('county', '')
            state = document_data.get('state', 'NJ')
            
            # Use extracted location as fallback if user input is missing
            if town == 'Unknown' or not town:
                extracted_town = parsed_data.get('extracted_town')
                if extracted_town:
                    town = extracted_town
                    logger.info(f"Using extracted town '{town}' from Grok response")
            
            if not county:
                extracted_county = parsed_data.get('extracted_county')
                if extracted_county:
                    county = extracted_county
                    logger.info(f"Using extracted county '{county}' from Grok response")
            
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return requirement_ids
    
    def _extract_zones_fallback(self, job_id: str, grok_response: str, document_data: dict, parsed_data: Optional[Dict] = None) -> List[str]:
        """Fallback method to extract zones from malformed Grok response or parsed data"""
        requirement_ids = []
        try:
            # Ensure we have valid data even in fallback - handle None values
            town = (document_data.get('municipality') or '').strip()
            if not town or town.lower() == 'unknown':
                town = f"Fallback_Job_{job_id[:8]}"
            county = (document_data.get('county') or '') or 'Unknown County'
            state = (document_data.get('state') or 'NJ')
            
            logger.info(f"🔧 Fallback extraction using: town='{town}', county='{county}', state='{state}'")
            
            if parsed_data:
                # Try to extract from parsed data first
                zones = []
                possible_keys = ['zones', 'zoning_requirements', 'requirements']
                for key in possible_keys:
                    if key in parsed_data:
                        zones = parsed_data[key]
                        break
                if zones:
                    logger.info(f"Fallback extraction from parsed_data found {len(zones)} zones")
                    # Process zones as normal
                    for zone_data in zones:
                        try:
                            req_id = self._insert_zone_requirements(
                                job_id=job_id,
                                town=town,
                                county=county,
                                state=state,
                                zone_data=zone_data,
                                extraction_confidence=0.5
                            )
                            if req_id:
                                requirement_ids.append(req_id)
                        except Exception as e:
                            logger.error(f"Error in fallback processing: {e}")
                    return requirement_ids
            
            # Original regex fallback if no parsed data
            import re
            
            zone_patterns = [
                r'(?:zone|district)[:\s]*([A-Z0-9\-]+)',
                r'([A-Z]{1,2}-\d+)',
                r'([RC]-\d+)'
            ]
            
            zones_found = set()
            for pattern in zone_patterns:
                matches = re.findall(pattern, grok_response, re.IGNORECASE)
                zones_found.update(matches)
            
            logger.info(f"Regex fallback extraction found zones: {zones_found}")
            
            # Create basic requirements for found zones
            for zone in zones_found:
                if zone and len(zone) < 50:
                    try:
                        req_id = self._insert_zone_requirements(
                            job_id=job_id,
                            town=town,
                            county=county,
                            state=state,
                            zone_data={'zone': zone},
                            extraction_confidence=0.3
                        )
                        if req_id:
                            requirement_ids.append(req_id)
                            logger.info(f"Created regex fallback requirement for zone {zone}")
                    except Exception as e:
                        logger.error(f"Error creating regex fallback requirement: {e}")
            
            return requirement_ids
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {str(e)}")
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
            # Extract all fields from zone data with flexible key mapping
            # Handle various possible JSON structures from Grok
            interior = self._get_nested_dict(zone_data, ['interior_lots', 'interior', 'interior_lot'])
            corner = self._get_nested_dict(zone_data, ['corner_lots', 'corner', 'corner_lot'])
            lot_req = self._get_nested_dict(zone_data, ['lot_requirements', 'additional_lot_requirements', 'lot_req'])
            principal_yards = self._get_nested_dict(zone_data, ['principal_building_yards', 'principal_yards', 'main_building_yards'])
            accessory_yards = self._get_nested_dict(zone_data, ['accessory_building_yards', 'accessory_yards', 'accessory'])
            coverage = self._get_nested_dict(zone_data, ['coverage_and_height', 'coverage', 'building_requirements'])
            floor_area = self._get_nested_dict(zone_data, ['floor_area', 'floor_requirements', 'area_requirements'])
            intensity = self._get_nested_dict(zone_data, ['development_intensity', 'intensity', 'density'])
            
            # Direct table insertion - bypass RPC function complexity
            # Build the requirement record
            requirement_data = {
                'job_id': job_id,
                'town': town,
                'county': county,
                'state': state,
                'zone': zone_data.get('zone', 'Unknown'),
                'data_source': 'AI_Extracted',
                'extraction_confidence': extraction_confidence,
                
                # Interior lots - flexible field mapping
                'interior_min_lot_area_sqft': self._safe_numeric(
                    self._extract_field_value([interior, zone_data], 
                    ['min_lot_area_sqft', 'interior_min_lot_area_sqft', 'lot_area', 'area_sqft'])
                ),
                'interior_min_lot_frontage_ft': self._safe_numeric(
                    self._extract_field_value([interior, zone_data], 
                    ['min_lot_frontage_ft', 'interior_min_lot_frontage_ft', 'frontage', 'frontage_ft'])
                ),
                'interior_min_lot_width_ft': self._safe_numeric(
                    self._extract_field_value([interior, zone_data], 
                    ['min_lot_width_ft', 'interior_min_lot_width_ft', 'width', 'width_ft'])
                ),
                'interior_min_lot_depth_ft': self._safe_numeric(
                    self._extract_field_value([interior, zone_data], 
                    ['min_lot_depth_ft', 'interior_min_lot_depth_ft', 'depth', 'depth_ft'])
                ),
                
                # Corner lots
                'corner_min_lot_area_sqft': self._safe_numeric(corner.get('min_lot_area_sqft')),
                'corner_min_lot_frontage_ft': self._safe_numeric(corner.get('min_lot_frontage_ft')),
                'corner_min_lot_width_ft': self._safe_numeric(corner.get('min_lot_width_ft')),
                'corner_min_lot_depth_ft': self._safe_numeric(corner.get('min_lot_depth_ft')),
                
                # Other lot requirements
                'min_circle_diameter_ft': self._safe_numeric(lot_req.get('min_circle_diameter_ft')),
                'buildable_lot_area_sqft': self._safe_numeric(lot_req.get('buildable_lot_area_sqft')),
                
                # Principal building yards - flexible mapping for setbacks
                'principal_front_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['front_yard_ft', 'front_setback', 'front_yard_setback_ft', 'front_yard', 'setback_front'])
                ),
                'principal_side_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['side_yard_ft', 'side_setback', 'side_yard_setback_ft', 'side_yard', 'setback_side'])
                ),
                'principal_street_side_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['street_side_yard_ft', 'street_side_setback', 'street_side_yard_setback_ft'])
                ),
                'principal_rear_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['rear_yard_ft', 'rear_setback', 'rear_yard_setback_ft', 'rear_yard', 'setback_rear'])
                ),
                'principal_street_rear_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['street_rear_yard_ft', 'street_rear_setback', 'street_rear_yard_setback_ft'])
                ),
                
                # Accessory building yards
                'accessory_front_yard_ft': self._safe_numeric(accessory_yards.get('front_yard_ft')),
                'accessory_side_yard_ft': self._safe_numeric(accessory_yards.get('side_yard_ft')),
                'accessory_street_side_yard_ft': self._safe_numeric(accessory_yards.get('street_side_yard_ft')),
                'accessory_rear_yard_ft': self._safe_numeric(accessory_yards.get('rear_yard_ft')),
                'accessory_street_rear_yard_ft': self._safe_numeric(accessory_yards.get('street_rear_yard_ft')),
                
                # Coverage and height - flexible mapping for common fields
                'max_building_coverage_percent': self._safe_numeric(
                    self._extract_field_value([coverage, zone_data], 
                    ['max_building_coverage_percent', 'building_coverage', 'coverage_percent', 'max_coverage'])
                ),
                'max_lot_coverage_percent': self._safe_numeric(
                    self._extract_field_value([coverage, zone_data], 
                    ['max_lot_coverage_percent', 'lot_coverage', 'max_lot_coverage', 'coverage'])
                ),
                'max_height_stories': self._safe_integer(
                    self._extract_field_value([coverage, zone_data], 
                    ['max_height_stories', 'height_stories', 'max_stories', 'stories', 'floors'])
                ),
                'max_height_feet_total': self._safe_numeric(
                    self._extract_field_value([coverage, zone_data], 
                    ['max_height_feet', 'max_height_feet_total', 'height_ft', 'maximum_height', 'height'])
                ),
                
                # Floor area
                'min_gross_floor_area_first_floor_sqft': self._safe_numeric(floor_area.get('min_gross_floor_area_first_floor_sqft')),
                'min_gross_floor_area_multistory_sqft': self._safe_numeric(floor_area.get('min_gross_floor_area_multistory_sqft')),
                'max_gross_floor_area_all_structures_sqft': self._safe_numeric(floor_area.get('max_gross_floor_area_all_structures_sqft')),
                
                # Development intensity - flexible mapping for FAR and density
                'maximum_far': self._safe_numeric(
                    self._extract_field_value([intensity, zone_data], 
                    ['maximum_far', 'max_far', 'far', 'floor_area_ratio', 'maximum_floor_area_ratio'])
                ),
                'maximum_density_units_per_acre': self._safe_numeric(
                    self._extract_field_value([intensity, zone_data], 
                    ['maximum_density_units_per_acre', 'max_density', 'density', 'units_per_acre'])
                ),
                
                # Timestamps
                'extracted_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Use upsert to handle conflicts (update existing records for same town/county/state/zone)
            result = self.client.table('requirements').upsert(
                requirement_data,
                on_conflict='town,county,state,zone'
            ).execute()
            
            if result.data and len(result.data) > 0:
                requirement_id = result.data[0].get('id')
                logger.info(f"Successfully inserted/updated requirement {requirement_id} for zone {zone_data.get('zone')} in {town}, {state}")
                return requirement_id
            else:
                logger.error("Failed to insert requirement: No data returned from upsert")
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
    
    def _get_nested_dict(self, data: dict, possible_keys: list) -> dict:
        """Get nested dictionary using flexible key lookup"""
        for key in possible_keys:
            if key in data and isinstance(data[key], dict):
                return data[key]
        return {}
    
    def _extract_field_value(self, nested_dicts: list, field_keys: list) -> Any:
        """Extract field value from multiple possible locations"""
        for nested_dict in nested_dicts:
            for field_key in field_keys:
                if field_key in nested_dict:
                    return nested_dict[field_key]
        return None
    
    def _fix_json_string(self, json_str: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix unescaped quotes in strings (basic attempt)
        # This is a simple fix - for more complex cases, we'd need a proper JSON parser
        
        # Remove control characters that can break JSON
        json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
        
        # Fix unterminated strings by finding the last quote and ensuring it's properly closed
        # This is a basic attempt - in practice, malformed JSON can be very complex to fix
        
        return json_str
