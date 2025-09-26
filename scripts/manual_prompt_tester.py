#!/usr/bin/env python3
"""
Manual Prompt Tester - Interactive tool for optimizing Grok prompts
"""

import sys
import os
import json
import requests
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings

def test_prompt_with_grok(prompt_text, document_text):
    """Test a custom prompt with Grok API"""
    
    print("🤖 Testing prompt with Grok...")
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        full_prompt = f"{prompt_text}\n\nDOCUMENT TO ANALYZE:\n{document_text}"
        
        payload = {
            "model": settings.GROK_MODEL,
            "messages": [{"role": "user", "content": full_prompt}],
            "max_tokens": settings.GROK_MAX_TOKENS,
            "temperature": settings.GROK_TEMPERATURE
        }
        
        response = requests.post(
            f"{settings.GROK_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            
            return {
                "success": True,
                "response": content,
                "tokens_used": tokens_used
            }
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def analyze_response(response_text):
    """Analyze Grok's response for quality"""
    
    print("\n📊 Response Analysis:")
    print("-" * 30)
    
    try:
        # Try to parse as JSON
        parsed = json.loads(response_text)
        
        print("✅ Valid JSON structure")
        
        # Check required fields
        has_town = parsed.get('extracted_town') is not None
        has_county = parsed.get('extracted_county') is not None
        has_zones = len(parsed.get('zoning_requirements', [])) > 0
        
        print(f"🏘️ Location extraction: {'✅' if has_town else '❌'} Town, {'✅' if has_county else '❌'} County")
        print(f"🏗️ Zones found: {len(parsed.get('zoning_requirements', []))}")
        
        if has_zones:
            zones = parsed['zoning_requirements']
            for i, zone in enumerate(zones):
                zone_name = zone.get('zone_name', 'Unknown')
                non_null_fields = sum(1 for v in zone.values() if v is not None)
                print(f"   Zone {i+1}: {zone_name} ({non_null_fields} fields extracted)")
        
        return parsed
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON - needs improvement")
        print(f"📝 Response preview: {response_text[:200]}...")
        return None

def interactive_prompt_testing():
    """Interactive prompt testing session"""
    
    print("🎯 Manual Prompt Optimizer for Zoning Extraction")
    print("=" * 60)
    
    # Sample document for testing
    test_document = """
Town of Springfield Zoning Ordinance
County: Union County, New Jersey

ZONE R-1 SINGLE FAMILY RESIDENTIAL
- Minimum lot area: 8,000 square feet
- Minimum lot frontage: 75 feet  
- Front yard setback: 25 feet
- Side yard setback: 10 feet
- Rear yard setback: 30 feet
- Maximum height: 30 feet (2.5 stories)
- Maximum lot coverage: 30%

ZONE C-1 COMMERCIAL DISTRICT
- Minimum lot area: 10,000 square feet
- Maximum FAR: 1.5
- Maximum height: 40 feet
- Front setback: 0 feet (build to street line)
- Side setback: None required
"""
    
    print("📄 Test Document Preview:")
    print(test_document[:300] + "...")
    
    # Prompt variants to test
    prompts = {
        "1": {
            "name": "Current Production",
            "text": """
Extract zoning requirements from this document. Return JSON with:
- extracted_town: municipality name
- extracted_county: county name  
- zoning_requirements: array of zones with fields like zone_name, interior_min_lot_area_sqft, principal_min_front_yard_ft, etc.

Be precise with numbers. Use null if not specified.
"""
        },
        "2": {
            "name": "Structured Field Mapping",
            "text": """
ZONING EXTRACTION EXPERT - Extract with surgical precision.

STEP 1: Identify location (town/municipality and county)
STEP 2: Find all zoning districts (R-1, C-1, I-1, etc.)  
STEP 3: Extract exact numeric requirements for each zone

FIELD MAPPING:
- "lot area" → interior_min_lot_area_sqft (number only)
- "frontage" → interior_min_lot_frontage_ft (number only)
- "front setback" → principal_min_front_yard_ft (number only)
- "side setback" → principal_min_side_yard_ft (number only)
- "rear setback" → principal_min_rear_yard_ft (number only)
- "height" → principal_max_height_feet (number only)
- "stories" → principal_max_height_stories (decimal like 2.5)
- "lot coverage" → max_lot_coverage_percent (number only)
- "FAR" → maximum_far (decimal like 1.5)

Extract EXACT numbers. Remove commas. Convert "8,000" to 8000.

Return clean JSON:
{
  "extracted_town": "town name",
  "extracted_county": "county name",
  "zoning_requirements": [
    {
      "zone_name": "R-1",
      "interior_min_lot_area_sqft": 8000,
      "principal_min_front_yard_ft": 25,
      // ... exact numbers only
    }
  ]
}
"""
        },
        "3": {
            "name": "Examples-Based",
            "text": """
You are a zoning expert. Extract requirements following these EXACT examples:

EXAMPLE 1:
Input: "Zone R-1: lot area 10,000 sq ft, front setback 25 feet"
Output: {"zone_name": "R-1", "interior_min_lot_area_sqft": 10000, "principal_min_front_yard_ft": 25}

EXAMPLE 2:  
Input: "Commercial C-1: FAR 2.0, height 45 feet"
Output: {"zone_name": "C-1", "maximum_far": 2.0, "principal_max_height_feet": 45}

RULES:
- Extract EXACT zone codes (R-1, C-1, not descriptions)
- Extract EXACT numbers (remove commas: "8,000" → 8000)
- Use precise field names as shown in examples
- Use null if not specified

Analyze the document and return JSON with extracted_town, extracted_county, and zoning_requirements array.
"""
        },
        "4": {
            "name": "Custom Prompt",
            "text": ""  # User will enter custom prompt
        }
    }
    
    while True:
        print("\n" + "=" * 60)
        print("🧪 Prompt Testing Options:")
        print("1. Test Current Production Prompt")
        print("2. Test Structured Field Mapping Prompt")  
        print("3. Test Examples-Based Prompt")
        print("4. Test Custom Prompt (enter your own)")
        print("5. Compare All Prompts")
        print("6. Deploy Best Prompt to Production")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice in ["1", "2", "3"]:
            prompt_info = prompts[choice]
            print(f"\n🧪 Testing: {prompt_info['name']}")
            
            result = test_prompt_with_grok(prompt_info['text'], test_document)
            
            if result['success']:
                print(f"\n📊 Tokens used: {result['tokens_used']}")
                print(f"📝 Raw response length: {len(result['response'])} characters")
                
                parsed = analyze_response(result['response'])
                
                if parsed:
                    print(f"\n🎯 Quick Quality Check:")
                    zones = parsed.get('zoning_requirements', [])
                    for zone in zones:
                        zone_name = zone.get('zone_name', 'Unknown')
                        lot_area = zone.get('interior_min_lot_area_sqft')
                        front_yard = zone.get('principal_min_front_yard_ft')
                        print(f"   {zone_name}: {lot_area} sqft lot, {front_yard}ft setback")
            else:
                print(f"❌ Test failed: {result['error']}")
        
        elif choice == "4":
            print("\n✏️ Enter your custom prompt:")
            print("(Type your prompt, then press Enter twice when done)")
            
            lines = []
            while True:
                line = input()
                if line == "" and lines:
                    break
                lines.append(line)
            
            custom_prompt = "\n".join(lines)
            print(f"\n🧪 Testing custom prompt ({len(custom_prompt)} characters)")
            
            result = test_prompt_with_grok(custom_prompt, test_document)
            
            if result['success']:
                parsed = analyze_response(result['response'])
                
                if parsed and input("\n💾 Save this prompt? (y/n): ").lower() == 'y':
                    prompt_name = input("Prompt name: ").strip()
                    prompts[str(len(prompts) + 1)] = {
                        "name": prompt_name,
                        "text": custom_prompt
                    }
                    print(f"✅ Saved prompt: {prompt_name}")
        
        elif choice == "5":
            print("\n🏁 Comparing All Prompts:")
            results = {}
            
            for key, prompt_info in prompts.items():
                if prompt_info['text']:  # Skip empty custom prompt
                    result = test_prompt_with_grok(prompt_info['text'], test_document)
                    if result['success']:
                        parsed = analyze_response(result['response'])
                        accuracy = calculate_simple_accuracy(parsed) if parsed else 0.0
                        results[prompt_info['name']] = {
                            'accuracy': accuracy,
                            'tokens': result['tokens_used'],
                            'zones_found': len(parsed.get('zoning_requirements', [])) if parsed else 0
                        }
            
            print("\n📊 COMPARISON RESULTS:")
            for name, metrics in sorted(results.items(), key=lambda x: x[1]['accuracy'], reverse=True):
                print(f"🏆 {name}: {metrics['accuracy']:.1%} accuracy, {metrics['zones_found']} zones, {metrics['tokens']} tokens")
        
        elif choice == "6":
            print("\n🚀 Deploy to Production:")
            print("1. Choose your best prompt from tests above")
            print("2. I'll help you update the grok_service.py file")
            print("3. Rebuild and test the Docker container")
            
            print("\nWhich prompt performed best?")
            best_prompt = input("Enter prompt name: ").strip()
            print(f"✅ Ready to deploy '{best_prompt}' - let me know and I'll update the code!")
        
        elif choice == "7":
            print("👋 Optimization session complete!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

def calculate_simple_accuracy(parsed_data):
    """Simple accuracy calculation based on field completeness"""
    if not parsed_data or not parsed_data.get('zoning_requirements'):
        return 0.0
    
    total_possible_fields = len(parsed_data['zoning_requirements']) * 10  # 10 key fields per zone
    extracted_fields = 0
    
    for zone in parsed_data['zoning_requirements']:
        key_fields = [
            'zone_name', 'interior_min_lot_area_sqft', 'interior_min_lot_frontage_ft',
            'principal_min_front_yard_ft', 'principal_min_side_yard_ft', 'principal_min_rear_yard_ft',
            'principal_max_height_feet', 'max_lot_coverage_percent', 'maximum_far'
        ]
        
        for field in key_fields:
            if zone.get(field) is not None:
                extracted_fields += 1
    
    return extracted_fields / total_possible_fields if total_possible_fields > 0 else 0.0

if __name__ == "__main__":
    interactive_prompt_testing()
