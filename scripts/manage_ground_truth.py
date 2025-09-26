#!/usr/bin/env python3
"""
Ground Truth Management CLI Tool
Easily add ground truth documents and requirements for A/B testing
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.ab_testing_service import ABTestingService, GroundTruthDocument, GroundTruthRequirement

def main():
    print("🧪 Ground Truth Management Tool")
    print("=" * 50)
    
    service = ABTestingService()
    
    while True:
        print("\nOptions:")
        print("1. Add Ground Truth Document")
        print("2. Add Ground Truth Requirement")
        print("3. List Ground Truth Documents")
        print("4. View Document Requirements")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            add_ground_truth_document(service)
        elif choice == "2":
            add_ground_truth_requirement(service)
        elif choice == "3":
            list_ground_truth_documents(service)
        elif choice == "4":
            view_document_requirements(service)
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def add_ground_truth_document(service: ABTestingService):
    """Add a new ground truth document"""
    print("\n📄 Add Ground Truth Document")
    print("-" * 30)
    
    try:
        document_name = input("Document name: ").strip()
        original_filename = input("Original filename: ").strip()
        town = input("Town: ").strip()
        county = input("County (optional): ").strip() or None
        state = input("State [NJ]: ").strip() or "NJ"
        verified_by = input("Verified by (your name): ").strip()
        number_of_zones = int(input("Number of zones: ").strip())
        
        print("\nComplexity options: simple, medium, complex")
        complexity = input("Document complexity [medium]: ").strip() or "medium"
        
        verification_notes = input("Verification notes (optional): ").strip() or None
        
        doc = GroundTruthDocument(
            id=None,
            document_name=document_name,
            original_filename=original_filename,
            town=town,
            county=county,
            state=state,
            verified_by=verified_by,
            number_of_zones=number_of_zones,
            complexity=complexity
        )
        
        doc_id = service.create_ground_truth_document(doc)
        print(f"✅ Created ground truth document: {doc_id}")
        print(f"📝 Document: {document_name} ({town}, {county}, {state})")
        print(f"🏗️  Expected zones: {number_of_zones}")
        print("\n💡 Next: Use option 2 to add zoning requirements for each zone")
        
    except Exception as e:
        print(f"❌ Error creating document: {e}")

def add_ground_truth_requirement(service: ABTestingService):
    """Add a ground truth requirement"""
    print("\n🏗️  Add Ground Truth Requirement")
    print("-" * 35)
    
    try:
        # First, show available documents
        docs = service.client.table('ground_truth_documents').select('id, document_name, town, number_of_zones').execute()
        
        if not docs.data:
            print("❌ No ground truth documents found. Create one first (option 1).")
            return
        
        print("\nAvailable documents:")
        for i, doc in enumerate(docs.data):
            print(f"{i+1}. {doc['document_name']} ({doc['town']}) - {doc['number_of_zones']} zones")
        
        doc_choice = int(input(f"\nSelect document (1-{len(docs.data)}): ")) - 1
        selected_doc = docs.data[doc_choice]
        
        print(f"\n📄 Adding requirement for: {selected_doc['document_name']}")
        
        zone = input("Zone name (e.g., R-1, C-1): ").strip()
        zone_description = input("Zone description (optional): ").strip() or None
        
        print("\nEnter zoning requirements (press Enter to skip any field):")
        
        # Collect common zoning fields
        fields = {}
        
        area_sqft = input("Min lot area (sq ft): ").strip()
        if area_sqft:
            fields['interior_min_lot_area_sqft'] = float(area_sqft)
        
        frontage_ft = input("Min lot frontage (ft): ").strip()
        if frontage_ft:
            fields['interior_min_lot_frontage_ft'] = float(frontage_ft)
        
        front_yard = input("Front yard setback (ft): ").strip()
        if front_yard:
            fields['principal_front_yard_ft'] = float(front_yard)
        
        side_yard = input("Side yard setback (ft): ").strip()
        if side_yard:
            fields['principal_side_yard_ft'] = float(side_yard)
        
        rear_yard = input("Rear yard setback (ft): ").strip()
        if rear_yard:
            fields['principal_rear_yard_ft'] = float(rear_yard)
        
        building_coverage = input("Max building coverage (%): ").strip()
        if building_coverage:
            fields['max_building_coverage_percent'] = float(building_coverage)
        
        lot_coverage = input("Max lot coverage (%): ").strip()
        if lot_coverage:
            fields['max_lot_coverage_percent'] = float(lot_coverage)
        
        height_stories = input("Max height (stories): ").strip()
        if height_stories:
            fields['max_height_stories'] = int(height_stories)
        
        height_feet = input("Max height (feet): ").strip()
        if height_feet:
            fields['max_height_feet_total'] = float(height_feet)
        
        far = input("Maximum FAR: ").strip()
        if far:
            fields['maximum_far'] = float(far)
        
        requirement = GroundTruthRequirement(
            id=None,
            ground_truth_doc_id=selected_doc['id'],
            zone=zone,
            zone_description=zone_description,
            **fields
        )
        
        req_id = service.add_ground_truth_requirement(requirement)
        print(f"✅ Created requirement: {req_id}")
        print(f"🏗️  Zone: {zone}")
        print(f"📊 Fields added: {len(fields)}")
        
    except Exception as e:
        print(f"❌ Error creating requirement: {e}")

def list_ground_truth_documents(service: ABTestingService):
    """List all ground truth documents"""
    print("\n📋 Ground Truth Documents")
    print("-" * 30)
    
    try:
        result = service.client.from_('ground_truth_overview').select('*').execute()
        
        if not result.data:
            print("📭 No ground truth documents found.")
            return
        
        for doc in result.data:
            print(f"\n📄 {doc['document_name']}")
            print(f"   📍 Location: {doc['town']}, {doc['county']}, {doc['state']}")
            print(f"   🏗️  Zones: {doc['number_of_zones']} (verified: {doc['verified_zones']})")
            print(f"   📊 Complexity: {doc['document_complexity']}")
            print(f"   ✅ Verified by: {doc['verified_by']}")
            print(f"   📅 Date: {doc['verification_date']}")
        
    except Exception as e:
        print(f"❌ Error listing documents: {e}")

def view_document_requirements(service: ABTestingService):
    """View requirements for a specific document"""
    print("\n🔍 View Document Requirements")
    print("-" * 35)
    
    try:
        docs = service.client.table('ground_truth_documents').select('id, document_name, town').execute()
        
        if not docs.data:
            print("❌ No ground truth documents found.")
            return
        
        print("\nAvailable documents:")
        for i, doc in enumerate(docs.data):
            print(f"{i+1}. {doc['document_name']} ({doc['town']})")
        
        doc_choice = int(input(f"\nSelect document (1-{len(docs.data)}): ")) - 1
        selected_doc = docs.data[doc_choice]
        
        reqs = service.client.table('ground_truth_requirements').select('*').eq('ground_truth_doc_id', selected_doc['id']).execute()
        
        print(f"\n📄 Requirements for: {selected_doc['document_name']}")
        
        if not reqs.data:
            print("📭 No requirements found for this document.")
            return
        
        for req in reqs.data:
            print(f"\n🏗️  Zone: {req['zone']}")
            if req['zone_description']:
                print(f"   📝 Description: {req['zone_description']}")
            
            # Show non-null fields
            fields = []
            if req['interior_min_lot_area_sqft']:
                fields.append(f"Lot area: {req['interior_min_lot_area_sqft']} sq ft")
            if req['principal_front_yard_ft']:
                fields.append(f"Front setback: {req['principal_front_yard_ft']} ft")
            if req['principal_side_yard_ft']:
                fields.append(f"Side setback: {req['principal_side_yard_ft']} ft")
            if req['max_height_feet_total']:
                fields.append(f"Max height: {req['max_height_feet_total']} ft")
            if req['maximum_far']:
                fields.append(f"FAR: {req['maximum_far']}")
            
            if fields:
                print("   📊 Requirements: " + ", ".join(fields))
            else:
                print("   📊 No specific requirements recorded")
        
    except Exception as e:
        print(f"❌ Error viewing requirements: {e}")

if __name__ == "__main__":
    main()
