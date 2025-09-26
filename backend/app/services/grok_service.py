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
You are an expert zoning analyst. Extract ALL zoning requirements with MAXIMUM PRECISION.

⚠️⚠️⚠️ CRITICAL BUG TO AVOID ⚠️⚠️⚠️
NEVER COMBINE ZONE FOOTNOTES WITH LOT AREAS!
- Zone "R-1¹" with area "5,000 sq ft" → MUST output 5000 NOT 15000
- Zone "R-2²" with area "8,000 sq ft" → MUST output 8000 NOT 28000
- The superscript ¹²³ is NEVER part of the area number!

Document Text:
{text_content[:10000]}

CRITICAL EXTRACTION TARGETS (Currently missing - FOCUS HERE):
🏗️ HEIGHT: "maximum height", "building height", "height limit", "stories" → EXACT numbers
📐 COVERAGE: "lot coverage", "building coverage", "impervious coverage" → EXACT percentages  
📊 FAR: "FAR", "floor area ratio", "density" → EXACT decimal numbers

STEP 1 - LOCATION:
Find: {municipality if municipality else 'SEARCH_DOCUMENT'}, {county if county else 'SEARCH_DOCUMENT'}, {state}

STEP 2 - ZONES:
Find ALL districts: R-1, R-2, C-1, C-2, I-1, etc. (look in tables, headings, schedules)
⚠️ REMOVE all superscripts/footnotes from zone names: R-1¹ → R-1

STEP 3 - REQUIREMENTS (Extract EXACT numbers):

✅ LOT REQUIREMENTS (CRITICAL: Fix exponent contamination):
- interior_min_lot_area_sqft: "lot area", "minimum area", "required area" → EXACT number ONLY
  🚨 CRITICAL BUG FIX: Zone footnotes (¹²³) are contaminating lot area values
  🚨 "Zone R-1¹: 5,000 sq ft" MUST extract 5000, NOT 15000
  🚨 "Zone R-2²: 8,000 sq ft" MUST extract 8000, NOT 28000  
  🚨 IGNORE ALL SUPERSCRIPT NUMBERS: ¹²³⁴⁵⁶⁷⁸⁹⁰
  🚨 Extract ONLY the actual square footage number, completely ignore zone footnotes
- interior_min_lot_frontage_ft: "frontage", "street frontage", "minimum frontage" → number
- interior_min_lot_width_ft: "width", "lot width" → number (if missing, use frontage value)
- interior_min_lot_depth_ft: "depth", "lot depth" → number (if missing but width exists, use width value)

✅ PRINCIPAL BUILDING SETBACKS (enhanced):
- principal_min_front_yard_ft: "front yard", "front setback", "front building line" → number
- principal_min_side_yard_ft: "side yard", "side setback" → number (use ONE side value, not multiple)
- principal_min_rear_yard_ft: "rear yard", "rear setback", "back yard" → number

🏠 ACCESSORY BUILDING SETBACKS (currently 0% - IMPROVE):
- accessory_min_front_yard_ft: "accessory front", "garage setback", "shed setback" → number
- accessory_min_side_yard_ft: "accessory side", "outbuilding side" → number
- accessory_min_rear_yard_ft: "accessory rear", "outbuilding rear" → number
SEARCH: accessory building sections, outbuilding regulations, garage requirements, shed rules

🏗️ HEIGHT (improved accuracy needed):
- principal_max_height_feet: "height", "maximum height", "building height" → EXACT feet
- principal_max_height_stories: "stories", "floors" → PRECISE decimal (2.5 for "2½", 2.5 for "two and one-half", NOT rounded to 2)
CRITICAL: Convert fractional stories accurately: "2½"→2.5, "2 1/2"→2.5, "two and one-half"→2.5
SEARCH: height sections, building codes, dimensional tables, "H=" in tables

❌ COVERAGE (CRITICAL - LOOK EVERYWHERE):
- max_building_coverage_percent: "building coverage", "structure coverage", "footprint coverage" → number (remove %)
- max_lot_coverage_percent: "lot coverage", "impervious coverage", "total coverage", "site coverage" → number (remove %)
SEARCH LOCATIONS: coverage sections, density rules, environmental regulations, "coverage" tables, building regulations, dimensional charts, development standards
COMMON PHRASES: "coverage shall not exceed", "maximum coverage", "coverage ratio", "coverage percentage", "impervious surface"

❌ FAR/DENSITY (0% success - FIX THIS):
- maximum_far: "FAR", "floor area ratio" → decimal (1.5, 2.0)
- maximum_density_units_per_acre: "density", "units per acre" → number
SEARCH: commercial zones, mixed-use areas, density bonuses, "FAR=" in tables

⚠️ EXTRACTION EXAMPLES - PAY CLOSE ATTENTION TO LOT AREAS:

INPUT: "Zone R-1¹: 5,000 sq ft, 25 ft setback"
✅ CORRECT: {{"zone_name": "R-1", "interior_min_lot_area_sqft": 5000}}
❌ WRONG: {{"zone_name": "R-1", "interior_min_lot_area_sqft": 15000}} ← DO NOT ADD FOOTNOTE TO AREA!

INPUT: "Zone R-2²: minimum area 8,000 square feet" 
✅ CORRECT: {{"zone_name": "R-2", "interior_min_lot_area_sqft": 8000}}
❌ WRONG: {{"zone_name": "R-2", "interior_min_lot_area_sqft": 28000}} ← DO NOT ADD FOOTNOTE TO AREA!

INPUT: "Zone R-3³: 12,000 sf minimum lot"
✅ CORRECT: {{"zone_name": "R-3", "interior_min_lot_area_sqft": 12000}}
❌ WRONG: {{"zone_name": "R-3", "interior_min_lot_area_sqft": 312000}} ← DO NOT ADD FOOTNOTE TO AREA!

🚨 FOOTNOTE CONTAMINATION PREVENTION (CRITICAL):
PROBLEM: Zone footnotes are contaminating lot area values
- "Zone R-1¹: 5,000 sq ft" being extracted as 15000 instead of 5000
- "Zone R-2²: 8,000 sq ft" being extracted as 28000 instead of 8000

SOLUTION: Extract numeric values SEPARATELY from zone names
- Zone name: "R-1¹" → clean to "R-1"  
- Lot area: "5,000 sq ft" → extract 5000 (ignore any zone footnotes)
- DO NOT concatenate zone footnote numbers with area values

EXTRACTION PROCESS:
1. Identify zone: "R-1¹" → record as "R-1"
2. Find area: "5,000 square feet" → extract 5000
3. NEVER combine: zone footnote (1) + area (5000) = 15000 ❌
4. Always separate: zone="R-1", area=5000 ✅

JSON OUTPUT:
{{
  "extracted_town": "{municipality or 'EXTRACT_FROM_DOCUMENT'}",
  "extracted_county": "{county or 'EXTRACT_FROM_DOCUMENT'}",
  "zoning_requirements": [
    {{
      "zone_name": "R-1",
      "interior_min_lot_area_sqft": 8000,
      "interior_min_lot_frontage_ft": 75,
      "principal_min_front_yard_ft": 25,
      "principal_min_side_yard_ft": 10,
      "principal_min_rear_yard_ft": 30,
      "principal_max_height_feet": 30,
      "principal_max_height_stories": 2.5,
      "max_building_coverage_percent": 30,
      "max_lot_coverage_percent": 40,
      "maximum_far": 1.5,
      "maximum_density_units_per_acre": null
    }}
  ]
}}

PAY SPECIAL ATTENTION TO HEIGHT, COVERAGE, AND FAR EXTRACTION.
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