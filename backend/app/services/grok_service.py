"""
Grok AI Service for document processing
"""

import logging
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)


class GrokService:
    """Service for interacting with Grok AI API"""

    def __init__(self):
        self.api_key = settings.GROK_API_KEY
        self.base_url = settings.GROK_BASE_URL
        self.model = settings.GROK_MODEL
        self.max_tokens = settings.GROK_MAX_TOKENS
        self.temperature = settings.GROK_TEMPERATURE

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def process_zoning_document(self, text_content: str, municipality: str = None, state: str = "NJ", county: str = None) -> Dict[str, Any]:
        """
        Process zoning document text using Grok AI

        Args:
            text_content: Extracted text from the document
            municipality: Municipality name if available
            state: State code (default: NJ)
            county: County name if available

        Returns:
            Dict containing processed zoning information
        """
        try:
            location_info = ""
            if municipality and county:
                location_info = f" for {municipality}, {county}, {state}"
            elif municipality:
                location_info = f" for {municipality}, {state}"
            else:
                location_info = f" for {state}"

            prompt = f"""
            You are an expert zoning and land use analyst. Analyze the following zoning document text{location_info} and extract SPECIFIC zoning requirements data.

            Document Text:
            {text_content[:10000]}  # Limit text length for API

            Please extract and provide the following information for EACH ZONING DISTRICT found in the document. 
            Return your response as a JSON object with the following structure:

            {{
                "zones": [
                    {{
                        "zone": "Zone name/code (e.g., R-1, C-2, etc.)",
                        
                        "interior_lots": {{
                            "min_lot_area_sqft": numeric or null,
                            "min_lot_frontage_ft": numeric or null,
                            "min_lot_width_ft": numeric or null,
                            "min_lot_depth_ft": numeric or null
                        }},
                        
                        "corner_lots": {{
                            "min_lot_area_sqft": numeric or null,
                            "min_lot_frontage_ft": numeric or null,
                            "min_lot_width_ft": numeric or null,
                            "min_lot_depth_ft": numeric or null
                        }},
                        
                        "lot_requirements": {{
                            "min_circle_diameter_ft": numeric or null,
                            "buildable_lot_area_sqft": numeric or null
                        }},
                        
                        "principal_building_yards": {{
                            "front_yard_ft": numeric or null,
                            "side_yard_ft": numeric or null,
                            "street_side_yard_ft": numeric or null,
                            "rear_yard_ft": numeric or null,
                            "street_rear_yard_ft": numeric or null
                        }},
                        
                        "accessory_building_yards": {{
                            "front_yard_ft": numeric or null,
                            "side_yard_ft": numeric or null,
                            "street_side_yard_ft": numeric or null,
                            "rear_yard_ft": numeric or null,
                            "street_rear_yard_ft": numeric or null
                        }},
                        
                        "coverage_and_height": {{
                            "max_building_coverage_percent": numeric or null,
                            "max_lot_coverage_percent": numeric or null,
                            "max_height_stories": numeric or null,
                            "max_height_feet": numeric or null
                        }},
                        
                        "floor_area": {{
                            "min_gross_floor_area_first_floor_sqft": numeric or null,
                            "min_gross_floor_area_multistory_sqft": numeric or null,
                            "max_gross_floor_area_all_structures_sqft": numeric or null
                        }},
                        
                        "development_intensity": {{
                            "maximum_far": numeric or null,
                            "maximum_density_units_per_acre": numeric or null
                        }},
                        
                        "permitted_uses": ["list of permitted uses"],
                        "special_provisions": "any special provisions or notes"
                    }}
                ],
                "summary": "Brief summary of the zoning ordinance",
                "extraction_confidence": 0.0 to 1.0 (your confidence in the extraction accuracy)
            }}

            IMPORTANT EXTRACTION RULES:
            1. Extract NUMERIC values only - convert all measurements to the requested units
            2. If a value is not found or not applicable, use null
            3. Convert percentages to decimal form (e.g., 35% becomes 35)
            4. If frontage and width are both mentioned, include both
            5. Look for tables, schedules, or charts that contain these requirements
            6. Extract data for ALL zones mentioned in the document
            7. Be precise with zone names/codes as they appear in the document

            Return ONLY valid JSON, no additional text or explanation.
            """

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=settings.AI_PROCESSING_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Try to parse the content as JSON
                try:
                    parsed_content = json.loads(content)
                except json.JSONDecodeError:
                    # If not valid JSON, wrap it in a structure
                    parsed_content = {
                        "raw_response": content,
                        "zones": [],
                        "extraction_confidence": 0.5
                    }

                logger.info(f"Successfully processed document with Grok AI")
                return {
                    "success": True,
                    "processed_at": datetime.utcnow().isoformat(),
                    "grok_response": json.dumps(parsed_content) if isinstance(parsed_content, dict) else content,
                    "parsed_data": parsed_content,
                    "model": self.model,
                    "tokens_used": result.get("usage", {}).get("total_tokens")
                }
            else:
                error_msg = f"Grok API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "processed_at": datetime.utcnow().isoformat()
                }

        except requests.exceptions.Timeout:
            error_msg = "Grok API request timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "processed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Error processing document with Grok: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "processed_at": datetime.utcnow().isoformat()
            }

    def extract_text_from_document(self, file_path: str) -> Optional[str]:
        """
        Extract text content from various document formats
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            import os
            from pathlib import Path
            
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
            elif file_extension == '.pdf':
                try:
                    import PyPDF2
                    text = ""
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page_num in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_num]
                            text += page.extract_text()
                    return text
                except ImportError:
                    logger.warning("PyPDF2 not installed, trying alternative method")
                    # Fallback to pdfplumber if available
                    try:
                        import pdfplumber
                        text = ""
                        with pdfplumber.open(file_path) as pdf:
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text
                        return text
                    except ImportError:
                        logger.error("No PDF processing library available")
                        return None
                        
            elif file_extension in ['.doc', '.docx']:
                try:
                    import python_docx
                    doc = python_docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    logger.error("python-docx not installed for Word document processing")
                    return None
                    
            else:
                # Try to read as plain text for other formats
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Error extracting text from document: {str(e)}")
            return None