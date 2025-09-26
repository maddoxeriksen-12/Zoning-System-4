# 📊 Tableau Setup Guide for Zoning A/B Testing Analytics

## 🚀 Quick Start (5 minutes)

### **Step 1: Download Data**
```bash
cd /Users/maddoxeriksen/Desktop/Zoning-Project\(NEW\)
python3 scripts/download_tableau_data.py
```

### **Step 2: Open Tableau**
1. **Launch Tableau Desktop**
2. **Connect to Text File (CSV)**
3. **Browse to**: `tableau_data/` folder
4. **Select files**: `requirements_data.csv`, `prompt_performance.csv`, `jobs_data.csv`

### **Step 3: Create Visualizations**

---

## 📈 Recommended Tableau Dashboards

### **Dashboard 1: Zoning Requirements Overview**

#### **Data Source**: `requirements_data.csv`

**🗺️ Visualization 1: Geographic Distribution**
- **Chart Type**: Map
- **Dimensions**: Town, County, State  
- **Measures**: Count of Requirements
- **Color**: Extraction Confidence
- **Size**: Interior Min Lot Area
- **Purpose**: See where zoning data has been extracted

**📊 Visualization 2: Zone Type Analysis**
- **Chart Type**: Bar Chart
- **Rows**: Zone (R-1, R-2, C-1, etc.)
- **Columns**: Count of Records
- **Color**: Average Extraction Confidence
- **Purpose**: Most common zone types extracted

**🏗️ Visualization 3: Zoning Requirements Scatter**
- **Chart Type**: Scatter Plot
- **X-Axis**: Interior Min Lot Area (sqft)
- **Y-Axis**: Principal Front Yard (ft)  
- **Color**: Zone Type
- **Size**: Maximum FAR
- **Purpose**: Relationships between zoning requirements

---

### **Dashboard 2: A/B Testing Performance**

#### **Data Source**: `prompt_performance.csv`

**🎯 Visualization 1: Prompt Accuracy Ranking**
- **Chart Type**: Horizontal Bar Chart
- **Rows**: Prompt Name + Version
- **Columns**: Average Accuracy Score
- **Color**: Is Baseline (Orange for baseline, Blue for experiments)
- **Size**: Total Tests
- **Purpose**: Compare prompt performance

**📊 Visualization 2: Accuracy Breakdown**  
- **Chart Type**: Bullet Chart
- **Rows**: Prompt Name
- **Columns**: Average Accuracy Score, Average Field Accuracy, Average Zone Accuracy
- **Purpose**: Multi-dimensional accuracy comparison

**🔄 Visualization 3: Success Rate vs Accuracy**
- **Chart Type**: Scatter Plot
- **X-Axis**: Success Rate
- **Y-Axis**: Average Accuracy Score
- **Color**: LLM Model
- **Size**: Total Tests
- **Purpose**: Find optimal balance of reliability and accuracy

---

### **Dashboard 3: Processing Performance**

#### **Data Source**: `jobs_data.csv`

**⏱️ Visualization 1: Processing Timeline**
- **Chart Type**: Line Chart
- **X-Axis**: Created At (by day)
- **Y-Axis**: Count of Jobs
- **Color**: Processing Status
- **Purpose**: Monitor processing volume and success rates

**🌍 Visualization 2: Geographic Processing Map**
- **Chart Type**: Map
- **Location**: Town, County, State
- **Color**: Processing Status
- **Size**: Count of Documents
- **Purpose**: See geographic distribution of processed documents

**📈 Visualization 3: Processing Efficiency**
- **Chart Type**: Dual-Axis Chart
- **X-Axis**: Processing Date
- **Y-Axis 1**: Processing Time (if available)
- **Y-Axis 2**: Success Rate
- **Purpose**: Track system efficiency over time

---

## 🎨 Tableau Color Schemes

### **Accuracy Performance**
- **🟢 Excellent (90-100%)**: Green
- **🟡 Good (70-89%)**: Yellow/Orange  
- **🔴 Needs Improvement (<70%)**: Red

### **Zone Types**
- **🏠 Residential (R-*)**: Blue shades
- **🏢 Commercial (C-*)**: Orange shades
- **🏭 Industrial (I-*)**: Purple shades
- **🌳 Mixed/Other**: Green shades

### **Processing Status**
- **✅ Completed**: Green
- **⏳ Processing**: Blue
- **❌ Failed**: Red
- **📋 Pending**: Gray

---

## 🔧 Advanced Tableau Features

### **Calculated Fields to Create**

#### **1. Accuracy Category**
```
IF [Average Accuracy Score] >= 0.9 THEN "Excellent"
ELSEIF [Average Accuracy Score] >= 0.7 THEN "Good"  
ELSE "Needs Improvement"
END
```

#### **2. Zone Type Category**
```
IF LEFT([Zone], 1) = "R" THEN "Residential"
ELSEIF LEFT([Zone], 1) = "C" THEN "Commercial"
ELSEIF LEFT([Zone], 1) = "I" THEN "Industrial"
ELSE "Other"
END
```

#### **3. Lot Size Category**
```
IF [Interior Min Lot Area Sqft] >= 20000 THEN "Large (20k+ sqft)"
ELSEIF [Interior Min Lot Area Sqft] >= 10000 THEN "Medium (10k-20k sqft)"
ELSEIF [Interior Min Lot Area Sqft] >= 5000 THEN "Small (5k-10k sqft)"
ELSE "Very Small (<5k sqft)"
END
```

### **Parameters to Create**

#### **1. Date Range Filter**
- **Type**: Date Range
- **Purpose**: Filter data by processing date
- **Default**: Last 30 days

#### **2. Minimum Tests Filter**
- **Type**: Integer
- **Purpose**: Filter prompts by minimum number of tests
- **Default**: 5

#### **3. Accuracy Threshold**
- **Type**: Float
- **Purpose**: Highlight prompts above/below threshold
- **Default**: 0.8

---

## 📱 Mobile-Friendly Dashboards

### **Executive Summary Dashboard**
- **KPI Cards**: Overall accuracy, total tests, best prompt
- **Trend Line**: Accuracy improvement over time
- **Status Indicators**: System health metrics

### **Zone Analysis Dashboard**
- **Heat Map**: Zone difficulty by location
- **Bar Chart**: Most/least accurate zones
- **Geographic View**: Requirements coverage map

---

## 🔄 Data Refresh Strategy

### **Manual Refresh**
```bash
# Download latest data
python3 scripts/download_tableau_data.py

# In Tableau: Data → Refresh All Extracts
```

### **Automated Refresh** (Future)
- Set up Tableau Bridge for live connection
- Schedule automatic data downloads
- Use Tableau Server/Online for automatic refresh

---

## 🎯 Key Metrics to Monitor

### **A/B Testing KPIs**
- **Overall Accuracy**: Target >90%
- **Zone Detection Rate**: Target >95%
- **Field Accuracy**: Target >85%
- **Improvement Rate**: Target >5% month-over-month

### **Production System KPIs**  
- **Processing Success Rate**: Target >98%
- **Documents Processed**: Volume tracking
- **Geographic Coverage**: Expand to new locations
- **Zone Type Coverage**: Comprehensive zone extraction

### **Quality Metrics**
- **False Positive Rate**: Minimize incorrect extractions
- **False Negative Rate**: Minimize missed requirements
- **Confidence Scores**: Track extraction confidence
- **Human Verification**: Compare against ground truth

Your Tableau analytics system is now ready to provide comprehensive insights into zoning extraction performance! 📊✨
