# Tableau Analytics for Zoning A/B Testing

## 📊 Tableau Dashboard Setup Guide

### **Data Sources for Tableau**

Your API provides 5 key data sources optimized for Tableau visualization:

#### **1. Prompt Performance Overview**
- **URL**: `http://localhost:8000/api/tableau/export/prompt-performance?format=csv`
- **Purpose**: Compare different prompt experiments
- **Key Fields**: `prompt_name`, `prompt_version`, `average_accuracy_score`, `success_rate`, `total_tests`
- **Tableau Visualizations**:
  - Bar chart: Prompts ranked by accuracy
  - Scatter plot: Accuracy vs Success Rate
  - Heat map: Performance across different models

#### **2. Test Results Detail**
- **URL**: `http://localhost:8000/api/tableau/export/test-results?format=csv&days=30`
- **Purpose**: Detailed test results for analysis
- **Key Fields**: `test_date`, `overall_accuracy_score`, `zone_identification_accuracy`, `field_extraction_accuracy`
- **Tableau Visualizations**:
  - Time series: Accuracy over time
  - Box plots: Accuracy distribution by prompt
  - Correlation matrix: Accuracy vs processing time

#### **3. Accuracy Trends Timeline**
- **URL**: `http://localhost:8000/api/tableau/export/accuracy-improvement-timeline?format=csv`
- **Purpose**: Track improvement over time
- **Key Fields**: `test_date`, `daily_accuracy`, `improvement_over_baseline`, `trend_direction`
- **Tableau Visualizations**:
  - Line chart: Daily accuracy trends
  - Area chart: Improvement over baseline
  - Bullet chart: Performance vs targets

#### **4. Zone Extraction Difficulty**
- **URL**: `http://localhost:8000/api/tableau/export/zone-extraction-analysis?format=csv`
- **Purpose**: Identify which zones are hardest to extract
- **Key Fields**: `zone`, `avg_zone_accuracy`, `extraction_difficulty`, `document_complexity`
- **Tableau Visualizations**:
  - Heat map: Zone difficulty by location
  - Bar chart: Hardest/easiest zones
  - Geographic map: Accuracy by town/county

#### **5. Field-Level Accuracy Heatmap**
- **URL**: `http://localhost:8000/api/tableau/export/field-accuracy-heatmap?format=csv`
- **Purpose**: Field-by-field accuracy analysis
- **Key Fields**: `lot_area_accuracy`, `front_yard_accuracy`, `height_accuracy`, `far_accuracy`
- **Tableau Visualizations**:
  - Heat map: Field accuracy by prompt
  - Radar chart: Field performance profile
  - Stacked bar: Field accuracy breakdown

---

## 🎯 Recommended Tableau Dashboards

### **Dashboard 1: Prompt Performance Comparison**
```
📊 Visualizations:
- Bar Chart: Prompts ranked by overall accuracy
- Scatter Plot: Accuracy vs Success Rate (bubbles sized by total tests)
- Table: Top 10 performing prompts with details
- KPI Cards: Best accuracy, improvement over baseline

📋 Filters:
- LLM Model (grok-4-fast-reasoning, etc.)
- Date Range
- Minimum number of tests
- Include/exclude baseline
```

### **Dashboard 2: Accuracy Trends & Improvement**
```
📈 Visualizations:
- Line Chart: Daily accuracy trends by prompt
- Area Chart: Improvement over baseline over time
- Forecast: Projected accuracy improvements
- Dual Axis: Accuracy vs Number of Tests

📋 Filters:
- Time period (last 7/30/90 days)
- Prompt name/version
- Show trend lines
```

### **Dashboard 3: Zone & Field Analysis**
```
🗺️ Visualizations:
- Heat Map: Zone extraction difficulty
- Geographic Map: Accuracy by town/county (if locations available)
- Horizontal Bar: Field accuracy rankings
- Tree Map: Zones sized by test frequency, colored by accuracy

📋 Filters:
- Document complexity (simple/medium/complex)
- Zone type
- Geographic location
```

---

## 🔧 Tableau Connection Setup

### **Method 1: CSV Data Source (Recommended)**
1. **Download CSV files** from the API endpoints above
2. **Connect to CSV** in Tableau Desktop
3. **Join multiple CSV** files on common fields (prompt_name, test_date)
4. **Refresh data** by re-downloading CSVs

### **Method 2: PostgreSQL Direct Connection**
1. **Database Connection**: 
   - Server: `db.xympjhgrdvcrpdvftgyu.supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - Username: `postgres`
   - Password: `[Your Supabase password]`

2. **Custom SQL Queries** (use the queries from `tableau_analytics.py`)

### **Method 3: Tableau Online/Server (Future)**
- Set up automated data refresh using Tableau Bridge
- Connect directly to Supabase using PostgreSQL connector
- Schedule automatic dashboard updates

---

## 📈 Key Metrics to Track

### **Primary KPIs**
- **Overall Accuracy**: Target >90%
- **Zone Identification Rate**: Target >95%
- **Field Extraction Accuracy**: Target >85%
- **Success Rate**: Target >98%

### **Trend Indicators**
- **Week-over-week improvement**
- **Accuracy by document complexity**
- **Performance by zone type**
- **Model comparison (Grok vs others)**

### **Actionable Insights**
- **Which prompts perform best?**
- **Which zones need prompt optimization?** 
- **What document types are problematic?**
- **How much improvement over baseline?**

---

## 🚀 Quick Start

1. **Start your backend**: `docker-compose up -d backend`
2. **Download CSV data**: Visit the endpoints above with `?format=csv`
3. **Open Tableau Desktop**: Connect to CSV files
4. **Build visualizations**: Use the suggested chart types above
5. **Create dashboard**: Combine visualizations with filters

Your Tableau dashboard will provide real-time insights into prompt performance and help optimize zoning extraction accuracy systematically!
