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

    def process_zoning_document(self, text_content: str, municipality: str = None, county: str = None, state: str = "NJ") -> Dict[str, Any]:
        """
        Process zoning document text using Grok AI

        Args:
            text_content: Extracted text from the document
            municipality: Municipality name if available (fallback to AI extraction)
            county: County name if available (fallback to AI extraction)
            state: State code (default: NJ)

        Returns:
            Dict containing processed zoning information
        """
        try:
            # If no municipality or county provided, we'll ask Grok to extract them
            location_info = ""
            if municipality:
                location_info += f" for {municipality}"
            if county:
                location_info += f", {county}"
            location_info += f", {state}"

            prompt = f"""
You are an expert zoning and land use analyst. Analyze the following zoning document text{location_info} and extract key information.

Document Text:
{text_content[:10000]}  # Limit text length for API

IMPORTANT: First, identify the town/municipality and county from the document text. Look for phrases like "Town of [Name]", "City of [Name]", "Zoning Ordinance for [Place]", "[County] County", etc. If the location is not explicitly stated, infer from context (e.g., addresses, jurisdiction mentions).

Then, provide a structured analysis including the following zoning requirements for EACH zoning district found. If a value is not explicitly stated, use null. Ensure all 40 fields are present for each zone.

Extracted Location (include even if provided externally):
- extracted_town: The municipality/town name found in the document (e.g., "Hoboken")
- extracted_county: The county name found in the document (e.g., "Hudson County")

For each zone, extract:
- **Zone Name**: e.g., "R-1", "Commercial", "Industrial"
- **Minimum Lot Size (Interior Lots)**:
    - Area (square feet)
    - Frontage (feet)
    - Width (feet)
    - Depth (feet)
- **Minimum Lot Size (Corner Lots)**:
    - Area (square feet)
    - Frontage (feet)
    - Width (feet)
    - Depth (feet)
- **Additional Lot Requirements**:
    - Min. Circle Diameter (feet)
    - Buildable Lot Area (square feet)
- **Minimum Required Yard Areas (feet) - Principal Building**:
    - Front
    - Side
    - Street Side
    - Rear
    - Street Rear
- **Minimum Required Yard Areas (feet) - Accessory Building**:
    - Front
    - Side
    - Street Side
    - Rear
    - Street Rear
- **Coverage and Density Requirements**:
    - Max. Building Coverage (%)
    - Max. Lot Coverage (%)
- **Height Restrictions - Principal Building**:
    - Stories
    - Feet (Total)
- **Floor Area Requirements**:
    - Total Minimum Gross Floor Area - First Floor (square feet)
    - Total Minimum Gross Floor Area - Multistory (square feet)
    - Max Gross Floor Area (all structures, square feet)
- **Development Intensity**:
    - Maximum FAR (Floor Area Ratio)
    - Maximum Density (units per acre)

Format your response as a JSON object with:
- "extracted_town": string (municipality found in document)
- "extracted_county": string (county found in document) 
- "zoning_requirements": array of zone objects, each containing all 40 extracted fields

Example:
{{
    "extracted_town": "Hoboken",
    "extracted_county": "Hudson County",
    "zoning_requirements": [
        {{
            "zone_name": "R-1",
            "interior_min_lot_area_sqft": 10000,
            "interior_min_lot_frontage_ft": 100,
            // ... all 40 fields
        }}
    ]
}}
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