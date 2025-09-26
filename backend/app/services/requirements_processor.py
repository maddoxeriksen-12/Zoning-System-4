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
            # IMPORTANT: Don't use filename as town name yet - we'll try to extract from Grok first
            town = "PENDING_EXTRACTION"  # Temporary placeholder
            logger.info(f"Town pending extraction from Grok response")
        
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
            
            # Extract location information with priority: User Input > Grok Extraction > Fallback
            town = document_data.get('municipality', '').strip()
            county = document_data.get('county', '').strip()
            state = document_data.get('state', 'NJ').strip()
            
            # Priority 1: Use Grok extracted location if user didn't provide good data
            if not town or town.lower() in ['unknown', 'pending_extraction']:
                extracted_town = parsed_data.get('extracted_town')
                if extracted_town and extracted_town.strip():
                    town = extracted_town.strip()
                    logger.info(f"✅ Using Grok-extracted town: '{town}'")
                else:
                    # Fallback to filename-based identifier
                    filename = document_data.get('original_filename', document_data.get('filename', ''))
                    if filename:
                        import re
                        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', filename.split('.')[0])[:20]
                        town = f"Doc_{clean_name}"
                        logger.warning(f"⚠️ Fallback to filename-based town: '{town}'")
                    else:
                        town = f"Job_{job_id[:8]}"
                        logger.warning(f"⚠️ Final fallback town: '{town}'")
            
            if not county or county == 'Unknown County':
                extracted_county = parsed_data.get('extracted_county')
                if extracted_county and extracted_county.strip():
                    county = extracted_county.strip()
                    logger.info(f"✅ Using Grok-extracted county: '{county}'")
                else:
                    county = "Unknown County"
            
            logger.info(f"🏘️ Final location: {town}, {county}, {state}")
            
            # Process each zone - ensure unique zones only
            processed_zones = set()
            logger.info(f"🔄 Processing {len(zones)} zones for {town}, {county}, {state}")
            
            for i, zone_data in enumerate(zones):
                try:
                    zone_name = self._extract_zone_name(zone_data)
                    
                    # Skip duplicate zones
                    zone_key = f"{town}_{county}_{state}_{zone_name}".lower()
                    if zone_key in processed_zones:
                        logger.info(f"⏭️  Skipping duplicate zone {zone_name}")
                        continue
                    processed_zones.add(zone_key)
                    
                    logger.info(f"🏗️  Processing zone {i+1}/{len(zones)}: '{zone_name}' with {len([k for k,v in zone_data.items() if v is not None])} non-null fields")
                    
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
                        logger.info(f"✅ Created requirement {req_id} for zone '{zone_name}' in {town}, {county}, {state}")
                    
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
                'zone': self._extract_zone_name(zone_data),
                'data_source': 'AI_Extracted',
                'extraction_confidence': extraction_confidence,
                
                # Interior lots - enhanced with fallback logic and contamination fixing
                'interior_min_lot_area_sqft': self._fix_contaminated_lot_area(
                    self._extract_field_value([interior, zone_data], 
                    ['min_lot_area_sqft', 'interior_min_lot_area_sqft', 'lot_area', 'area_sqft', 'minimum_area_sqft']),
                    zone_data.get('zone_name', '')
                ),
                'interior_min_lot_frontage_ft': self._get_frontage_with_fallback(interior, zone_data),
                'interior_min_lot_width_ft': self._get_width_with_frontage_fallback(interior, zone_data),
                'interior_min_lot_depth_ft': self._get_depth_with_fallback(interior, zone_data),
                
                # Corner lots
                'corner_min_lot_area_sqft': self._safe_numeric(corner.get('min_lot_area_sqft')),
                'corner_min_lot_frontage_ft': self._safe_numeric(corner.get('min_lot_frontage_ft')),
                'corner_min_lot_width_ft': self._safe_numeric(corner.get('min_lot_width_ft')),
                'corner_min_lot_depth_ft': self._safe_numeric(corner.get('min_lot_depth_ft')),
                
                # Other lot requirements
                'min_circle_diameter_ft': self._safe_numeric(lot_req.get('min_circle_diameter_ft')),
                'buildable_lot_area_sqft': self._safe_numeric(lot_req.get('buildable_lot_area_sqft')),
                
                # Principal building yards - match Grok's actual field names
                'principal_front_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['principal_min_front_yard_ft', 'front_yard_ft', 'front_setback', 'principal_front_yard_ft'])
                ),
                'principal_side_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['principal_min_side_yard_ft', 'side_yard_ft', 'side_setback', 'principal_side_yard_ft'])
                ),
                'principal_street_side_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['principal_min_street_side_yard_ft', 'street_side_yard_ft', 'street_side_setback'])
                ),
                'principal_rear_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['principal_min_rear_yard_ft', 'rear_yard_ft', 'rear_setback', 'principal_rear_yard_ft'])
                ),
                'principal_street_rear_yard_ft': self._safe_numeric(
                    self._extract_field_value([principal_yards, zone_data], 
                    ['principal_min_street_rear_yard_ft', 'street_rear_yard_ft', 'street_rear_setback'])
                ),
                
                # Accessory building yards - enhanced extraction with fallbacks
                'accessory_front_yard_ft': self._get_accessory_setback_with_fallback(
                    accessory_yards, zone_data, 'front', 
                    ['accessory_min_front_yard_ft', 'accessory_front_yard_ft', 'garage_front_setback', 'outbuilding_front']
                ),
                'accessory_side_yard_ft': self._get_accessory_setback_with_fallback(
                    accessory_yards, zone_data, 'side',
                    ['accessory_min_side_yard_ft', 'accessory_side_yard_ft', 'garage_side_setback', 'outbuilding_side']
                ),
                'accessory_street_side_yard_ft': self._safe_numeric(
                    self._extract_field_value([accessory_yards, zone_data], 
                    ['accessory_min_street_side_yard_ft', 'accessory_street_side_yard_ft'])
                ),
                'accessory_rear_yard_ft': self._get_accessory_setback_with_fallback(
                    accessory_yards, zone_data, 'rear',
                    ['accessory_min_rear_yard_ft', 'accessory_rear_yard_ft', 'garage_rear_setback', 'outbuilding_rear']
                ),
                'accessory_street_rear_yard_ft': self._safe_numeric(
                    self._extract_field_value([accessory_yards, zone_data], 
                    ['accessory_min_street_rear_yard_ft', 'accessory_street_rear_yard_ft'])
                ),
                
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
                    ['principal_max_height_stories', 'max_height_stories', 'height_stories', 'max_stories'])
                ),
                'max_height_feet_total': self._safe_numeric(
                    self._extract_field_value([coverage, zone_data], 
                    ['principal_max_height_feet', 'max_height_feet_total', 'max_height_feet', 'height_ft'])
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
        """Convert value to float or return None, with footnote exponent cleaning"""
        if value is None or value == 'null':
            return None
        try:
            # Clean footnote exponents that contaminate numeric values
            if isinstance(value, str):
                cleaned_value = self._clean_numeric_footnotes(value)
                return float(cleaned_value)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _clean_numeric_footnotes(self, value: str) -> str:
        """Remove footnote exponents from numeric values - AGGRESSIVE CLEANING"""
        import re
        
        value = str(value).strip()
        original_value = value
        
        # Remove superscript numbers anywhere in the string
        cleaned = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]+', '', value)
        cleaned = re.sub(r'\^[0-9]+', '', cleaned)
        cleaned = re.sub(r'\([0-9]+\)', '', cleaned)
        
        # AGGRESSIVE: Check for contaminated lot areas
        # Pattern: Leading digit(s) from footnote + actual area value
        try:
            # Remove commas for analysis
            num_str = cleaned.replace(',', '').replace(' ', '')
            
            if num_str.isdigit() and len(num_str) >= 4:
                num_val = int(num_str)
                
                # Common contamination patterns:
                # 15000 (1 + 5000) → should be 5000
                # 28000 (2 + 8000) → should be 8000
                # 312000 (3 + 12000) → should be 12000
                
                if num_val > 50000:  # Suspiciously large for most residential lots
                    # Try removing first digit
                    if len(num_str) == 5 and num_str[0] in '123456789':  # 5-digit number
                        candidate = num_str[1:]  # Remove first digit
                        candidate_val = int(candidate)
                        if 1000 <= candidate_val <= 50000:  # Reasonable residential lot
                            logger.warning(f"🔧 FOOTNOTE CONTAMINATION FIXED: {original_value} → {candidate} (removed leading footnote digit)")
                            return candidate
                    
                    # Try removing first 2 digits for extreme cases
                    elif len(num_str) == 6 and num_str[:2] in ['10', '11', '12', '20', '21', '22', '30', '31', '32']:
                        candidate = num_str[2:]  # Remove first 2 digits
                        candidate_val = int(candidate)
                        if 1000 <= candidate_val <= 50000:
                            logger.warning(f"🔧 FOOTNOTE CONTAMINATION FIXED: {original_value} → {candidate} (removed leading footnote digits)")
                            return candidate
                
                # Common valid large lots (don't "fix" these)
                elif 50000 <= num_val <= 200000:  # Large but reasonable lots
                    return cleaned
            
            return cleaned
            
        except (ValueError, TypeError):
            # If not a clean number, return as-is
            if cleaned != original_value:
                logger.info(f"Cleaned footnotes: '{original_value}' → '{cleaned}'")
            return cleaned
    
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
    
    def _extract_zone_name(self, zone_data: dict) -> str:
        """Extract zone name with flexible key matching and footnote cleaning"""
        possible_zone_keys = ['zone_name', 'zone', 'district', 'zoning_district', 'name']
        for key in possible_zone_keys:
            value = zone_data.get(key)
            if value and str(value).strip():
                zone_name = str(value).strip()
                # Clean footnote exponents that cause parsing issues
                zone_name = self._clean_zone_name_footnotes(zone_name)
                return zone_name
        return 'Unknown_Zone'
    
    def _clean_zone_name_footnotes(self, zone_name: str) -> str:
        """Remove footnote exponents from zone names (R-1¹ → R-1)"""
        import re
        # Remove superscript numbers and symbols that indicate footnotes
        # Pattern matches: ¹ ² ³ ⁴ ⁵ and regular superscripts
        cleaned = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]+', '', zone_name)
        cleaned = re.sub(r'\^[0-9]+', '', cleaned)  # Remove ^1, ^2 style footnotes
        cleaned = re.sub(r'\([0-9]+\)', '', cleaned)  # Remove (1), (2) style footnotes
        cleaned = cleaned.strip()
        
        if cleaned != zone_name:
            logger.info(f"Cleaned zone name: '{zone_name}' → '{cleaned}'")
        
        return cleaned
    
    def _get_frontage_with_fallback(self, interior: dict, zone_data: dict) -> float:
        """Get frontage with enhanced field matching"""
        return self._safe_numeric(
            self._extract_field_value([interior, zone_data], 
            ['min_lot_frontage_ft', 'interior_min_lot_frontage_ft', 'frontage', 'frontage_ft', 'street_frontage'])
        )
    
    def _get_width_with_frontage_fallback(self, interior: dict, zone_data: dict) -> float:
        """Get width, fallback to frontage if width missing"""
        width = self._safe_numeric(
            self._extract_field_value([interior, zone_data], 
            ['min_lot_width_ft', 'interior_min_lot_width_ft', 'width', 'width_ft', 'lot_width'])
        )
        
        # If width is missing, use frontage as fallback
        if width is None:
            frontage = self._get_frontage_with_fallback(interior, zone_data)
            if frontage is not None:
                logger.info(f"Using frontage {frontage} as width fallback")
                return frontage
        
        return width
    
    def _get_depth_with_fallback(self, interior: dict, zone_data: dict) -> float:
        """Get depth with width fallback if missing"""
        depth = self._safe_numeric(
            self._extract_field_value([interior, zone_data], 
            ['min_lot_depth_ft', 'interior_min_lot_depth_ft', 'depth', 'depth_ft', 'lot_depth'])
        )
        
        # If depth is missing, try to use width as fallback
        if depth is None:
            width = self._get_width_with_frontage_fallback(interior, zone_data)
            if width is not None:
                logger.info(f"Using width {width} as depth fallback")
                return width
        
        return depth
    
    def _get_accessory_setback_with_fallback(self, accessory_yards: dict, zone_data: dict, setback_type: str, field_keys: list) -> float:
        """Get accessory setback with fallback to principal setback if missing"""
        # First try to find specific accessory setback
        accessory_value = self._safe_numeric(
            self._extract_field_value([accessory_yards, zone_data], field_keys)
        )
        
        if accessory_value is not None:
            return accessory_value
        
        # Fallback: Use principal building setback (often accessory = principal)
        principal_field = f'principal_min_{setback_type}_yard_ft'
        principal_keys = [principal_field, f'{setback_type}_yard_ft', f'{setback_type}_setback']
        
        principal_value = self._safe_numeric(
            self._extract_field_value([zone_data], principal_keys)
        )
        
        if principal_value is not None:
            logger.info(f"Using principal {setback_type} setback {principal_value} as accessory fallback")
            return principal_value
        
        return None
    
    def _fix_contaminated_lot_area(self, lot_area_value: Any, zone_name: str) -> Optional[float]:
        """Fix lot area values contaminated with zone footnote exponents - AGGRESSIVE VERSION"""
        if lot_area_value is None:
            return None
        
        try:
            # First apply standard numeric cleaning
            cleaned_area = self._safe_numeric(lot_area_value)
            
            if cleaned_area is None:
                return None
            
            # AGGRESSIVE CONTAMINATION DETECTION
            # Common patterns: 15000→5000, 28000→8000, 312000→12000
            area_str = str(int(cleaned_area))
            
            # Pattern 1: Check if it's exactly 15000, 28000, 312000 etc (common contaminations)
            contamination_patterns = {
                15000: 5000,   # R-1¹ + 5000
                28000: 8000,   # R-2² + 8000
                312000: 12000, # R-3³ + 12000
                110000: 10000, # R-1¹ + 10000
                115000: 15000, # R-1¹ + 15000 (but keep as 15000)
                27500: 7500,   # R-2² + 7500
                36000: 6000,   # R-3³ + 6000
            }
            
            if cleaned_area in contamination_patterns:
                fixed_value = contamination_patterns[cleaned_area]
                logger.warning(f"🔧 KNOWN CONTAMINATION FIXED: {cleaned_area} → {fixed_value} (common pattern for zone {zone_name})")
                return float(fixed_value)
            
            # Pattern 2: If starts with 1,2,3 and is 5 digits, likely contaminated
            if len(area_str) == 5 and area_str[0] in '123':
                candidate = int(area_str[1:])
                if 3000 <= candidate <= 20000:  # Common residential lot sizes
                    logger.warning(f"🔧 PATTERN CONTAMINATION FIXED: {cleaned_area} → {candidate} (removed leading {area_str[0]} from zone {zone_name})")
                    return float(candidate)
            
            # Pattern 3: Check zone name for footnotes
            import re
            zone_clean = self._clean_zone_name_footnotes(zone_name)
            
            # Extract potential footnote number from zone name
            footnote_match = re.search(r'[¹²³⁴⁵⁶⁷⁸⁹]', zone_name)
            if not footnote_match:
                # Also check for R-1, R-2, R-3 patterns
                if 'R-1' in zone_name or 'R1' in zone_name:
                    footnote_digit = '1'
                elif 'R-2' in zone_name or 'R2' in zone_name:
                    footnote_digit = '2'
                elif 'R-3' in zone_name or 'R3' in zone_name:
                    footnote_digit = '3'
                else:
                    footnote_digit = None
            else:
                superscript_map = {'¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', 
                                 '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'}
                footnote_digit = superscript_map.get(footnote_match.group(0))
            
            if footnote_digit and area_str.startswith(footnote_digit):
                candidate_area_str = area_str[len(footnote_digit):]
                if candidate_area_str:
                    candidate_area = int(candidate_area_str)
                    if 1000 <= candidate_area <= 50000:
                        logger.warning(f"🔧 ZONE FOOTNOTE FIXED: {cleaned_area} → {candidate_area} (removed {footnote_digit} from zone {zone_name})")
                        return float(candidate_area)
            
            # Pattern 4: General heuristic - if unreasonably large, try removing first digit
            if cleaned_area > 100000:
                if len(area_str) > 4:
                    candidate = int(area_str[1:])
                    if 1000 <= candidate <= 50000:
                        logger.warning(f"🔧 HEURISTIC FIXED: {cleaned_area} → {candidate} (too large, removed first digit)")
                        return float(candidate)
            
            return cleaned_area
            
        except Exception as e:
            logger.error(f"Error fixing contaminated lot area: {e}")
            return self._safe_numeric(lot_area_value)
