# 🎯 Optimized Grok Prompts for Better Extraction

## 📊 Current Performance Analysis:
- ✅ **Lot area extraction**: 100% success
- ✅ **Front setback extraction**: 90% success  
- ❌ **Height extraction**: 0% success (major gap!)
- ❌ **Coverage extraction**: 0% success (major gap!)
- ❌ **FAR extraction**: 0% success (major gap!)

## 🚀 **OPTIMIZED PROMPT V1 (Addresses Missing Fields)**

```
EXPERT ZONING REQUIREMENTS EXTRACTOR

You are a municipal zoning expert analyzing zoning ordinances. Extract ALL zoning requirements with MAXIMUM PRECISION.

CRITICAL EXTRACTION TARGETS:
🏗️ HEIGHT REQUIREMENTS (often missed - PAY ATTENTION):
- Look for: "maximum height", "building height", "height limit", "height restriction"
- Extract: exact feet OR stories (convert stories to feet if needed: 2.5 stories ≈ 30 feet)
- Common locations: height sections, building regulations, dimensional standards

📐 COVERAGE REQUIREMENTS (often missed - PAY ATTENTION):
- Look for: "lot coverage", "building coverage", "impervious coverage", "coverage ratio"
- Extract: percentage numbers (remove % symbol)
- Common locations: density sections, coverage tables, dimensional charts

📊 FAR/DENSITY (often missed - PAY ATTENTION):
- Look for: "FAR", "floor area ratio", "density", "units per acre"
- Extract: decimal numbers (1.5, 2.0, etc.)
- Common locations: density sections, commercial zones, mixed-use areas

EXTRACTION PROCESS:

STEP 1 - LOCATION:
Identify: Town/municipality name and county name

STEP 2 - ZONES:
Find ALL zoning districts (R-1, R-2, C-1, C-2, I-1, etc.)

STEP 3 - REQUIREMENTS (Extract ALL fields):
For each zone, find these EXACT requirements:

🏠 LOT REQUIREMENTS:
- interior_min_lot_area_sqft: "lot area", "lot size", "minimum area" (number in sq ft)
- interior_min_lot_frontage_ft: "frontage", "street frontage" (number in feet)

📐 SETBACKS:
- principal_min_front_yard_ft: "front yard", "front setback" (number in feet)
- principal_min_side_yard_ft: "side yard", "side setback" (number in feet)  
- principal_min_rear_yard_ft: "rear yard", "rear setback" (number in feet)

🏗️ HEIGHT (CRITICAL - Don't miss these):
- principal_max_height_feet: "height", "building height", "maximum height" (number in feet)
- principal_max_height_stories: "stories", "floors" (decimal like 2.5)

📊 COVERAGE (CRITICAL - Don't miss these):
- max_building_coverage_percent: "building coverage" (percentage as number)
- max_lot_coverage_percent: "lot coverage", "impervious coverage" (percentage as number)

📈 DENSITY (CRITICAL - Don't miss these):  
- maximum_far: "FAR", "floor area ratio" (decimal like 1.5)
- maximum_density_units_per_acre: "density", "units per acre" (number)

VALIDATION RULES:
- Extract EXACT numbers only (no text, no ranges)
- Remove commas: "10,000" → 10000
- Convert percentages: "30%" → 30
- Convert fractions: "2½" → 2.5
- Use null only if truly not specified

SPECIAL ATTENTION TO MISSING FIELDS:
Look extra carefully for height, coverage, and FAR requirements. These are often in:
- Separate height sections
- Dimensional tables  
- Coverage/density charts
- Commercial zone specifications
- Mixed-use regulations

JSON OUTPUT (include ALL fields):
{
  "extracted_town": "exact town name",
  "extracted_county": "exact county name",
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

ANALYZE THE DOCUMENT WITH SPECIAL FOCUS ON HEIGHT, COVERAGE, AND FAR EXTRACTION.
```

## 🎯 **OPTIMIZED PROMPT V2 (Table-Focused)**

```
MUNICIPAL ZONING TABLE ANALYZER

You specialize in extracting data from zoning ordinance tables and dimensional charts.

DOCUMENT ANALYSIS STRATEGY:

1. SCAN FOR TABLES:
Zoning documents often contain dimensional tables with columns like:
- Zone | Min Lot Area | Frontage | Front Yard | Side Yard | Rear Yard | Height | Coverage

2. EXTRACT FROM TABLES:
When you find tables:
- Zone column → zone_name
- Lot area column → interior_min_lot_area_sqft  
- Height column → principal_max_height_feet
- Coverage column → max_building_coverage_percent or max_lot_coverage_percent

3. SCAN FOR TEXT REQUIREMENTS:
If no tables, look for text like:
- "In Zone R-1, the minimum lot area shall be 10,000 square feet"
- "Maximum building height: 35 feet"
- "Lot coverage shall not exceed 25%"

4. FIELD EXTRACTION PRIORITY:
Focus on these high-value fields (in order):
   ⭐ interior_min_lot_area_sqft (lot area)
   ⭐ principal_min_front_yard_ft (front setback)
   ⭐ principal_max_height_feet (building height)
   ⭐ max_lot_coverage_percent (lot coverage)
   ⭐ maximum_far (floor area ratio)

EXTRACTION EXAMPLES:
"Zone R-1: 8,000 sq ft minimum, 25 ft front setback, 30 ft height limit, 30% coverage"
→ {"zone_name": "R-1", "interior_min_lot_area_sqft": 8000, "principal_min_front_yard_ft": 25, "principal_max_height_feet": 30, "max_lot_coverage_percent": 30}

Return precise JSON with all extracted fields.
```

## 🧪 **Testing Instructions:**

Run this to test prompts interactively:
```bash
cd /Users/maddoxeriksen/Desktop/Zoning-Project(NEW)
python3 scripts/manual_prompt_tester.py
```

Select different prompts and compare results. The tool will show you:
- Field extraction success rates
- JSON parsing quality
- Accuracy scores
- Token usage

Choose the best performing prompt and I'll deploy it to your production system!
