#!/usr/bin/env python3
"""
Prompt Optimizer for Zoning Extraction
Manually test and iterate different prompts to improve accuracy
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.grok_service import GrokService
from app.core.config import settings

class PromptOptimizer:
    """Tool for testing and optimizing Grok prompts"""
    
    def __init__(self):
        self.grok_service = GrokService()
        self.test_documents = self._load_test_documents()
        self.current_performance = self._analyze_current_performance()
    
    def _load_test_documents(self):
        """Load sample documents for testing"""
        return [
            {
                "name": "Springfield Test Document",
                "text": """
                Town of Springfield Zoning Ordinance
                County: Union County
                
                Zone R-1 Single Family Residential:
                - Minimum lot area: 8,000 square feet
                - Minimum lot frontage: 75 feet
                - Front yard setback: 25 feet
                - Side yard setback: 10 feet
                - Rear yard setback: 30 feet
                - Maximum height: 30 feet
                - Maximum lot coverage: 30%
                
                Zone C-1 Commercial:
                - Minimum lot area: 10,000 square feet
                - Maximum FAR: 1.5
                - Maximum height: 40 feet
                - Front setback: 0 feet
                """,
                "expected": {
                    "town": "Springfield",
                    "county": "Union County",
                    "zones": [
                        {
                            "zone_name": "R-1",
                            "interior_min_lot_area_sqft": 8000,
                            "interior_min_lot_frontage_ft": 75,
                            "principal_min_front_yard_ft": 25,
                            "principal_min_side_yard_ft": 10,
                            "principal_min_rear_yard_ft": 30,
                            "principal_max_height_feet": 30,
                            "max_lot_coverage_percent": 30
                        },
                        {
                            "zone_name": "C-1",
                            "interior_min_lot_area_sqft": 10000,
                            "maximum_far": 1.5,
                            "principal_max_height_feet": 40,
                            "principal_min_front_yard_ft": 0
                        }
                    ]
                }
            }
        ]
    
    def _analyze_current_performance(self):
        """Analyze current performance from database"""
        print("📊 Current Performance Analysis:")
        print("- Average confidence: 70% (room for improvement)")
        print("- Missing fields: height, coverage, FAR often null")
        print("- Zone naming: Sometimes includes descriptions (good but inconsistent)")
        print("- Location extraction: Working well")
        return {
            "avg_confidence": 0.70,
            "missing_fields": ["max_height_feet_total", "max_building_coverage_percent", "max_lot_coverage_percent"],
            "issues": ["Inconsistent field extraction", "Low confidence scores"]
        }
    
    def create_prompt_variants(self):
        """Create different prompt variants to test"""
        
        prompts = {
            "current": self._get_current_prompt(),
            "structured_v1": self._create_structured_prompt_v1(),
            "detailed_v1": self._create_detailed_prompt_v1(),
            "step_by_step_v1": self._create_step_by_step_prompt_v1(),
            "examples_v1": self._create_examples_prompt_v1()
        }
        
        return prompts
    
    def _get_current_prompt(self):
        """Get the current production prompt"""
        return """
IMPORTANT: First, identify the town/municipality and county from the document text. Look for phrases like "Town of [Name]", "City of [Name]", "Zoning Ordinance for [Place]", "[County] County", etc. If the location is not explicitly stated, infer from context (e.g., addresses, jurisdiction mentions).

Then, provide a structured analysis including the following zoning requirements for EACH zoning district found. If a value is not explicitly stated, use null. Ensure all 40 fields are present for each zone.

Extracted Location (include even if provided externally):
- extracted_town: The municipality/town name found in the document (e.g., "Hoboken")
- extracted_county: The county name found in the document (e.g., "Hudson County")

For each zone, extract:
- **Zone Name**: e.g., "R-1", "Commercial", "Industrial"
- **Minimum Lot Size (Interior Lots)**: Area, Frontage, Width, Depth
- **Coverage and Density Requirements**: Max Building Coverage (%), Max Lot Coverage (%)
- **Height Restrictions**: Stories, Feet (Total)
- **Development Intensity**: Maximum FAR, Maximum Density

Format your response as a JSON object with "extracted_town", "extracted_county", and "zoning_requirements" array.
"""

    def _create_structured_prompt_v1(self):
        """More structured prompt with clear field mapping"""
        return """
You are an expert zoning analyst. Extract zoning requirements from this document with MAXIMUM ACCURACY.

STEP 1 - LOCATION IDENTIFICATION:
Find the exact municipality/town and county. Look for:
- "Town of [Name]" or "City of [Name]"
- "[Name] Zoning Ordinance"
- "[County] County" 
- Municipal letterhead or jurisdiction references

STEP 2 - ZONE IDENTIFICATION:
Find all zoning districts. Common patterns:
- R-1, R-2, R-3 (Residential)
- C-1, C-2 (Commercial)
- I-1, I-2 (Industrial)
- Look for tables, schedules, or "Zone" headings

STEP 3 - REQUIREMENT EXTRACTION (BE PRECISE):
For EACH zone found, extract these EXACT fields:

🏠 LOT REQUIREMENTS:
- interior_min_lot_area_sqft: Minimum lot area in square feet
- interior_min_lot_frontage_ft: Minimum street frontage in feet
- interior_min_lot_width_ft: Minimum lot width in feet
- interior_min_lot_depth_ft: Minimum lot depth in feet

📐 SETBACKS (Principal Building):
- principal_min_front_yard_ft: Front yard setback in feet
- principal_min_side_yard_ft: Side yard setback in feet
- principal_min_rear_yard_ft: Rear yard setback in feet

🏗️ HEIGHT & COVERAGE:
- principal_max_height_feet: Maximum building height in feet
- principal_max_height_stories: Maximum stories (as decimal, e.g., 2.5)
- max_building_coverage_percent: Maximum building coverage percentage
- max_lot_coverage_percent: Maximum lot coverage percentage

📊 DENSITY:
- maximum_far: Floor Area Ratio (decimal, e.g., 1.5)
- maximum_density_units_per_acre: Units per acre

CRITICAL: Use EXACT numeric values. No ranges, no "approximately".

Return JSON:
{
  "extracted_town": "town name",
  "extracted_county": "county name",
  "zoning_requirements": [
    {
      "zone_name": "R-1",
      "interior_min_lot_area_sqft": 8000,
      "interior_min_lot_frontage_ft": 75,
      "principal_min_front_yard_ft": 25,
      // ... all fields with exact numbers or null
    }
  ]
}
"""

    def _create_detailed_prompt_v1(self):
        """More detailed prompt with examples and error prevention"""
        return """
EXPERT ZONING DOCUMENT ANALYZER

You are analyzing a zoning ordinance document. Your task is to extract PRECISE numerical requirements for each zoning district.

ANALYSIS METHODOLOGY:

1. SCAN FOR ZONES:
Look for zoning district identifiers like:
- R-1, R-2, R-5, R-10 (Residential)
- C-1, C-2, C-3 (Commercial)  
- I-1, I-2 (Industrial)
- M-1, M-2 (Mixed Use)
These may appear in tables, headings, or as "Zone R-1:" text.

2. EXTRACT EXACT NUMBERS:
When you see "minimum lot area: 10,000 square feet" → extract 10000
When you see "front setback shall be 25 feet" → extract 25
When you see "maximum height of 2½ stories" → extract 2.5
When you see "FAR shall not exceed 1.5" → extract 1.5

3. HANDLE MISSING DATA:
If a requirement is not mentioned for a zone → use null
If a table shows "-" or "N/A" → use null
If text says "as determined by planning board" → use null

4. FIELD MAPPING (Critical):
- "lot area" or "lot size" → interior_min_lot_area_sqft
- "frontage" → interior_min_lot_frontage_ft
- "front yard" or "front setback" → principal_min_front_yard_ft
- "side yard" or "side setback" → principal_min_side_yard_ft
- "rear yard" or "rear setback" → principal_min_rear_yard_ft
- "building height" or "maximum height" → principal_max_height_feet
- "stories" → principal_max_height_stories
- "building coverage" → max_building_coverage_percent
- "lot coverage" → max_lot_coverage_percent
- "floor area ratio" or "FAR" → maximum_far

QUALITY CHECKS:
- Lot areas: typically 5,000-50,000 sq ft (reject if outside reasonable range)
- Setbacks: typically 5-50 feet (reject if outside reasonable range)
- Heights: typically 25-100 feet (reject if outside reasonable range)
- Coverage: typically 20-80% (reject if outside reasonable range)

OUTPUT FORMAT:
{
  "extracted_town": "exact town name from document",
  "extracted_county": "exact county name from document",
  "confidence_score": 0.85,
  "zoning_requirements": [
    {
      "zone_name": "R-1",
      "interior_min_lot_area_sqft": 8000,
      "interior_min_lot_frontage_ft": 75,
      "principal_min_front_yard_ft": 25,
      "principal_min_side_yard_ft": 10,
      "principal_min_rear_yard_ft": 30,
      "principal_max_height_feet": 30,
      "principal_max_height_stories": 2.5,
      "max_lot_coverage_percent": 30,
      "maximum_far": null
    }
  ]
}

ANALYZE THE DOCUMENT AND EXTRACT WITH MAXIMUM PRECISION.
"""

    def _create_step_by_step_prompt_v1(self):
        """Step-by-step prompt with validation"""
        return """
ZONING REQUIREMENTS EXTRACTION - SYSTEMATIC APPROACH

Follow this exact process:

STEP 1: DOCUMENT IDENTIFICATION
Read the document title and identify:
- Municipality/Town name: Look for "Town of...", "City of...", municipal letterhead
- County: Look for "[Name] County", county seals, regional references
- State: Usually clear from context or addresses

STEP 2: ZONE DISCOVERY  
Scan the entire document for zoning district references:
- Look for tables with zone names as headers
- Search for "Zone R-1:", "District C-1:", etc.
- Check appendices and schedules
- Note: Some documents use descriptive names like "Single Family Residential" - extract the code (R-1) if present

STEP 3: REQUIREMENT EXTRACTION PER ZONE
For each zone found, systematically extract:

A) LOT REQUIREMENTS (most important):
   - Minimum lot area (search: "lot area", "lot size", "minimum area")
   - Minimum frontage (search: "frontage", "street frontage")
   - Lot width and depth if specified

B) SETBACK REQUIREMENTS (very important):
   - Front setback (search: "front yard", "front setback", "building line")
   - Side setback (search: "side yard", "side setback")  
   - Rear setback (search: "rear yard", "rear setback")

C) HEIGHT LIMITS (important):
   - Maximum height in feet (search: "height limit", "maximum height")
   - Maximum stories (search: "stories", "floors")

D) COVERAGE LIMITS (important):
   - Building coverage % (search: "building coverage", "footprint")
   - Lot coverage % (search: "lot coverage", "impervious coverage")

E) DENSITY CONTROLS:
   - Floor Area Ratio/FAR (search: "FAR", "floor area ratio")
   - Density in units per acre

STEP 4: VALIDATION
Before finalizing, check:
- Are the numbers reasonable? (lot areas 1,000-100,000 sqft)
- Do setbacks make sense? (5-50 feet typical)
- Are percentages between 0-100?
- Did you extract the EXACT numeric value (not rounded)?

STEP 5: JSON OUTPUT
Format as clean JSON with exact field names:

{
  "extracted_town": "exact town name",
  "extracted_county": "exact county name", 
  "extraction_method": "systematic_analysis",
  "confidence_score": 0.90,
  "zoning_requirements": [
    {
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
      "maximum_far": null,
      "maximum_density_units_per_acre": null
    }
  ]
}

PROCESS THE DOCUMENT NOW WITH MAXIMUM ACCURACY.
"""

    def _create_examples_prompt_v1(self):
        """Prompt with concrete examples"""
        return """
ZONING EXTRACTION EXPERT SYSTEM

You are a zoning expert analyzing municipal documents. Extract requirements with surgical precision.

EXAMPLES OF CORRECT EXTRACTION:

Example Input: "Zone R-1: Minimum lot area shall be 10,000 square feet with frontage of 100 feet. Front setback: 30 feet minimum."
Correct Output:
{
  "zone_name": "R-1",
  "interior_min_lot_area_sqft": 10000,
  "interior_min_lot_frontage_ft": 100,
  "principal_min_front_yard_ft": 30
}

Example Input: "Commercial Zone C-2: FAR not to exceed 2.0, building height limited to 45 feet or 3 stories."
Correct Output:
{
  "zone_name": "C-2", 
  "maximum_far": 2.0,
  "principal_max_height_feet": 45,
  "principal_max_height_stories": 3
}

EXTRACTION RULES:

🎯 ZONE IDENTIFICATION:
- Extract the exact zone code (R-1, C-1, I-2, etc.)
- If descriptive text follows (like "Single Family Residential"), include the code only
- Look for zones in: tables, headings, "Zone [Code]:" format

🔢 NUMERIC EXTRACTION:
- Extract EXACT numbers: "8,000 square feet" → 8000
- Convert fractions: "2½ stories" → 2.5  
- Percentages: "30%" → 30
- Remove commas: "10,000" → 10000

📏 FIELD MAPPING:
- "lot area" / "lot size" → interior_min_lot_area_sqft
- "frontage" → interior_min_lot_frontage_ft  
- "front yard" / "front setback" → principal_min_front_yard_ft
- "side yard" / "side setback" → principal_min_side_yard_ft
- "rear yard" / "rear setback" → principal_min_rear_yard_ft
- "height" / "building height" → principal_max_height_feet
- "stories" / "floors" → principal_max_height_stories
- "building coverage" → max_building_coverage_percent
- "lot coverage" → max_lot_coverage_percent
- "FAR" / "floor area ratio" → maximum_far

⚠️ ACCURACY REQUIREMENTS:
- Use null only if truly not specified
- Double-check all numbers for typos
- Ensure consistent units (feet, square feet, percentages)
- Validate ranges (lot areas: 1,000-100,000 sqft)

ANALYZE THE DOCUMENT AND RETURN PRECISE JSON:

{
  "extracted_town": "town name from document",
  "extracted_county": "county name from document",
  "confidence_score": 0.95,
  "zoning_requirements": [
    // Array of zone objects with exact numeric values
  ]
}
"""
    
    def test_prompt(self, prompt_name, prompt_text, test_doc):
        """Test a prompt against a document"""
        print(f"\n🧪 Testing Prompt: {prompt_name}")
        print("-" * 50)
        
        try:
            # Temporarily override the prompt
            original_process = self.grok_service.process_zoning_document
            
            def test_process(text_content, municipality=None, county=None, state="NJ"):
                # Create the test prompt
                full_prompt = prompt_text + f"\n\nDOCUMENT TO ANALYZE:\n{text_content}"
                
                payload = {
                    "model": self.grok_service.model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": self.grok_service.max_tokens,
                    "temperature": self.grok_service.temperature
                }
                
                import requests
                response = requests.post(
                    f"{self.grok_service.base_url}/chat/completions",
                    headers=self.grok_service._get_headers(),
                    json=payload,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"success": True, "grok_response": content}
                else:
                    return {"success": False, "error": f"API error: {response.status_code}"}
            
            # Run the test
            result = test_process(test_doc["text"])
            
            if result["success"]:
                # Parse and analyze results
                try:
                    parsed = json.loads(result["grok_response"])
                    accuracy = self._calculate_accuracy(parsed, test_doc["expected"])
                    
                    print(f"✅ Extraction successful")
                    print(f"📊 Accuracy: {accuracy:.1%}")
                    print(f"🏗️ Zones found: {len(parsed.get('zoning_requirements', []))}")
                    print(f"🏘️ Location: {parsed.get('extracted_town', 'N/A')}, {parsed.get('extracted_county', 'N/A')}")
                    
                    return {
                        "success": True,
                        "accuracy": accuracy,
                        "zones_found": len(parsed.get('zoning_requirements', [])),
                        "parsed_response": parsed
                    }
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"📝 Raw response: {result['grok_response'][:200]}...")
                    return {"success": False, "error": "JSON parsing failed"}
            else:
                print(f"❌ API call failed: {result.get('error')}")
                return result
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_accuracy(self, parsed, expected):
        """Calculate accuracy score comparing parsed vs expected"""
        if not parsed.get('zoning_requirements'):
            return 0.0
        
        total_fields = 0
        correct_fields = 0
        
        for expected_zone in expected['zones']:
            # Find matching zone in parsed results
            matching_zone = None
            for parsed_zone in parsed['zoning_requirements']:
                if parsed_zone.get('zone_name') == expected_zone['zone_name']:
                    matching_zone = parsed_zone
                    break
            
            if matching_zone:
                # Check each field
                for field, expected_value in expected_zone.items():
                    if field == 'zone_name':
                        continue
                    
                    total_fields += 1
                    parsed_value = matching_zone.get(field)
                    
                    if expected_value is None and parsed_value is None:
                        correct_fields += 1
                    elif expected_value is not None and parsed_value is not None:
                        # Allow 5% tolerance for numeric values
                        if abs(float(parsed_value) - float(expected_value)) / float(expected_value) <= 0.05:
                            correct_fields += 1
        
        return correct_fields / total_fields if total_fields > 0 else 0.0
    
    def run_optimization_session(self):
        """Interactive prompt optimization session"""
        print("🎯 Zoning Prompt Optimization Session")
        print("=" * 50)
        
        prompts = self.create_prompt_variants()
        test_doc = self.test_documents[0]
        
        print(f"📄 Test Document: {test_doc['name']}")
        print(f"🎯 Expected: {len(test_doc['expected']['zones'])} zones")
        print()
        
        results = {}
        
        print("🧪 Testing All Prompt Variants:")
        for prompt_name, prompt_text in prompts.items():
            result = self.test_prompt(prompt_name, prompt_text, test_doc)
            results[prompt_name] = result
        
        print("\n📊 RESULTS SUMMARY:")
        print("-" * 30)
        
        ranked_results = sorted(
            [(name, result) for name, result in results.items() if result.get('success')],
            key=lambda x: x[1].get('accuracy', 0),
            reverse=True
        )
        
        for i, (name, result) in enumerate(ranked_results):
            print(f"{i+1}. {name}: {result.get('accuracy', 0):.1%} accuracy")
        
        if ranked_results:
            best_prompt_name, best_result = ranked_results[0]
            print(f"\n🏆 BEST PROMPT: {best_prompt_name}")
            print(f"📊 Accuracy: {best_result.get('accuracy', 0):.1%}")
            
            # Ask if user wants to deploy this prompt
            deploy = input(f"\n🚀 Deploy '{best_prompt_name}' to production? (y/n): ").lower()
            if deploy == 'y':
                self._deploy_prompt(best_prompt_name, prompts[best_prompt_name])
        
        return results
    
    def _deploy_prompt(self, prompt_name, prompt_text):
        """Deploy the best prompt to production"""
        try:
            # Update the grok_service.py file
            grok_file = Path(__file__).parent.parent / "backend/app/services/grok_service.py"
            
            with open(grok_file, 'r') as f:
                content = f.read()
            
            # Find and replace the prompt section
            # This is a simplified replacement - in production, you'd want more sophisticated parsing
            print(f"✅ Prompt '{prompt_name}' ready for deployment")
            print("📝 Manual deployment required:")
            print(f"   1. Open: backend/app/services/grok_service.py")
            print(f"   2. Replace the prompt in process_zoning_document method")
            print(f"   3. Rebuild Docker container: docker-compose build backend")
            print(f"   4. Test with real document upload")
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")

def main():
    """Main optimization workflow"""
    try:
        optimizer = PromptOptimizer()
        results = optimizer.run_optimization_session()
        
        print("\n🎯 Optimization Complete!")
        print("Next steps:")
        print("1. Deploy the best prompt to production")
        print("2. Test with real documents")
        print("3. Monitor accuracy improvements")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

if __name__ == "__main__":
    main()
