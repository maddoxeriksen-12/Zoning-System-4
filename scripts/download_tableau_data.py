#!/usr/bin/env python3
"""
Download CSV data for Tableau Analytics
Automatically downloads all datasets needed for Tableau visualizations
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
OUTPUT_DIR = Path("tableau_data")
OUTPUT_DIR.mkdir(exist_ok=True)

def download_csv(endpoint, filename, description):
    """Download CSV data from API endpoint"""
    try:
        print(f"📥 Downloading {description}...")
        
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            output_path = OUTPUT_DIR / filename
            with open(output_path, 'w') as f:
                f.write(response.text)
            
            # Count rows
            row_count = len(response.text.strip().split('\n')) - 1  # Subtract header
            print(f"   ✅ Saved {filename} ({row_count} records)")
            return True
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error downloading {filename}: {e}")
        return False

def download_all_tableau_data():
    """Download all data sources for Tableau"""
    
    print("🎯 Zoning Analytics - Tableau Data Download")
    print("=" * 50)
    print(f"📂 Output directory: {OUTPUT_DIR.absolute()}")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Data sources to download
    downloads = [
        {
            "endpoint": "/api/tableau/export/prompt-performance?format=csv",
            "filename": "prompt_performance.csv",
            "description": "Prompt Performance Metrics"
        },
        {
            "endpoint": "/api/tableau/export/test-results?format=csv&days=30",
            "filename": "test_results_30days.csv", 
            "description": "Test Results (Last 30 Days)"
        },
        {
            "endpoint": "/api/tableau/export/requirements-data?format=csv&limit=1000",
            "filename": "requirements_data.csv",
            "description": "Current Requirements Data"
        },
        {
            "endpoint": "/api/tableau/export/jobs-data?format=csv&limit=1000",
            "filename": "jobs_data.csv",
            "description": "Processing Jobs Data"
        }
    ]
    
    success_count = 0
    
    for download in downloads:
        if download_csv(download["endpoint"], download["filename"], download["description"]):
            success_count += 1
    
    print()
    print(f"📊 Download Summary: {success_count}/{len(downloads)} successful")
    
    if success_count == len(downloads):
        print("🎉 All data downloaded successfully!")
        print()
        print("🔗 Next Steps for Tableau:")
        print(f"1. Open Tableau Desktop")
        print(f"2. Connect to Text File → Browse to {OUTPUT_DIR.absolute()}")
        print(f"3. Select CSV files to create data sources")
        print(f"4. Use the Tableau workbook template: tableau/ZoningAnalytics.twb")
        print()
        print("📈 Recommended Visualizations:")
        print("- Bar Chart: Prompt accuracy rankings")
        print("- Time Series: Accuracy trends over time")
        print("- Geographic Map: Requirements by town/county")
        print("- Heatmap: Field-level accuracy comparison")
        print("- Scatter Plot: Accuracy vs Processing Time")
    else:
        print("⚠️  Some downloads failed. Check your backend is running:")
        print(f"   Backend URL: {BACKEND_URL}")
        print(f"   Health check: {BACKEND_URL}/health")
    
    # Create a manifest file for easy reference
    manifest = {
        "download_timestamp": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "files_downloaded": success_count,
        "total_files": len(downloads),
        "data_sources": downloads
    }
    
    with open(OUTPUT_DIR / "download_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📄 Manifest saved: {OUTPUT_DIR}/download_manifest.json")

if __name__ == "__main__":
    download_all_tableau_data()
