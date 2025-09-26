# 🔴 LIVE Tableau Connection Setup

## 🎯 Goal: Real-Time Data Flow
```
PDF Upload → Supabase → Tableau Dashboard (Auto-Updates)
```

No manual scripts, no CSV downloads - just live streaming data!

---

## 🔧 Step 1: Create Live Views in Supabase

**Run this SQL in Supabase SQL Editor:**
```sql
-- Copy and execute: tableau/live_views_for_tableau.sql
```

This creates 5 optimized views:
- `tableau_requirements_live` - Real-time requirements data
- `tableau_processing_performance` - Processing metrics by day
- `tableau_zone_analysis` - Zone extraction analysis 
- `tableau_geographic_summary` - Location-based summaries
- `tableau_daily_stats` - Daily processing statistics

---

## 🔗 Step 2: Connect Tableau to Supabase PostgreSQL

### **Connection Details:**
```
Server: db.xympjhgrdvcrpdvftgyu.supabase.co
Port: 5432
Database: postgres
Username: postgres
Password: [Your Supabase DB Password]
```

### **In Tableau Desktop:**
1. **Open Tableau Desktop**
2. **Connect** → **To a Server** → **PostgreSQL**
3. **Enter connection details** above
4. **Test Connection** (should show "Successfully connected")
5. **Sign In**

---

## 📊 Step 3: Set Up Live Data Sources

### **Data Source 1: Requirements Live Feed**
- **Table**: `tableau_requirements_live`
- **Refresh**: **Live Connection** (no extract)
- **Use**: Main dashboard for requirements visualization

### **Data Source 2: Processing Performance**
- **Table**: `tableau_processing_performance` 
- **Refresh**: **Live Connection**
- **Use**: System performance monitoring

### **Data Source 3: Geographic Analysis**
- **Table**: `tableau_geographic_summary`
- **Refresh**: **Live Connection**
- **Use**: Geographic distribution maps

### **Data Source 4: Daily Statistics**
- **Table**: `tableau_daily_stats`
- **Refresh**: **Live Connection**
- **Use**: Time-series analysis and trends

---

## 🎨 Step 4: Create Live Dashboards

### **Dashboard 1: Real-Time Requirements Monitor**

#### **Sheet 1: Live Geographic Map**
- **Mark Type**: Map
- **Location**: Town, County, State (drag to Detail)
- **Color**: Total Requirements (continuous)
- **Size**: Avg Extraction Confidence
- **Tooltip**: Zone count, latest extraction
- **Auto-Refresh**: Every 5 minutes

#### **Sheet 2: Zone Type Distribution (Live)**
- **Chart**: Horizontal Bar
- **Rows**: Zone Category
- **Columns**: Count of Requirements
- **Color**: Confidence Level
- **Filter**: Last 7 days (relative date)

#### **Sheet 3: Processing Volume Timeline**
- **Chart**: Line Chart
- **X-Axis**: Extraction Date (continuous)
- **Y-Axis**: Requirements Extracted
- **Color**: Zone Category
- **Trend Line**: Yes (exponential)

### **Dashboard 2: Quality Monitoring**

#### **Sheet 1: Extraction Confidence Heatmap**
- **Chart**: Heat Map
- **Rows**: Town
- **Columns**: Zone Category  
- **Color**: Average Confidence
- **Text**: Count of Requirements

#### **Sheet 2: Data Completeness Gauges**
- **Chart**: Bullet Chart
- **Metrics**: Lot Area %, Setback %, FAR %
- **Target**: 80% completion
- **Actual**: Current completion rates

#### **Sheet 3: Live Processing Status**
- **Chart**: Donut Chart
- **Angle**: Count of Jobs
- **Color**: Processing Status
- **Label**: Percentage

---

## ⚡ Step 5: Configure Auto-Refresh

### **Live Connection Settings:**
1. **Data Source** → **Extract** → **Live**
2. **Connection** → **Automatically Update**
3. **Refresh Every**: 5 minutes
4. **Incremental Refresh**: Yes (new records only)

### **Dashboard Auto-Refresh:**
1. **Server** → **Publish Workbook**
2. **Data Source** → **Schedule Refresh**
3. **Frequency**: Every 5-10 minutes
4. **Incremental**: Yes

### **For Tableau Desktop (Local):**
```
Dashboard → Actions → URL Actions → Refresh Data
Trigger: Timer (5 minutes)
URL: [Self-refresh command]
```

---

## 🧪 Step 6: Test Live Data Flow

### **Test Scenario:**
1. **Upload a PDF** via document uploader
2. **Wait 30 seconds** for processing
3. **Check Tableau dashboard** - should show:
   - New requirement record(s)
   - Updated geographic distribution
   - Increased daily extraction count
   - Real-time processing metrics

### **Verification Commands:**
```bash
# Upload test document
curl -X POST -F "file=@test.pdf" -F "municipality=TestTown" -F "county=TestCounty" -F "state=NJ" http://localhost:5001/upload

# Check if data appears in Tableau views (via API)
curl "http://localhost:8000/api/tableau/export/requirements-data?format=json&limit=5"
```

---

## 🎛️ Real-Time Dashboard Features

### **Auto-Refresh Indicators:**
- **Green Dot**: Data updated within 5 minutes
- **Yellow Dot**: Data 5-15 minutes old
- **Red Dot**: Data >15 minutes old (connection issue)

### **Live KPI Cards:**
- **Documents Processed Today**: Real-time count
- **Average Confidence**: Live calculation
- **Success Rate**: Updated every processing completion
- **Zones Extracted**: Live zone discovery count

### **Real-Time Filters:**
- **Last Hour** / **Last Day** / **Last Week**
- **High Confidence Only** (>80%)
- **Specific Towns/Counties**
- **Zone Types** (Residential/Commercial/Industrial)

---

## 🔄 Maintenance & Monitoring

### **Connection Health Check:**
```sql
-- Run in Supabase to verify views are working
SELECT COUNT(*) FROM tableau_requirements_live;
SELECT MAX(extraction_date) FROM tableau_daily_stats;
```

### **Performance Optimization:**
- Views are indexed for fast Tableau queries
- Filters on date ranges for better performance
- Aggregated views reduce data transfer

### **Troubleshooting:**
- **Slow updates**: Check Supabase connection
- **Missing data**: Verify uploader → backend flow
- **Old data**: Check auto-refresh settings in Tableau

**Your Tableau dashboard will now update automatically as new PDFs are processed!** 🎯📊✨
