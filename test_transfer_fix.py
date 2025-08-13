#!/usr/bin/env python3
"""
Test script to verify storage transfer direction fix
"""

import requests
import json

# Test data for storage transfer from Cu Chi to BRENNTAG
test_orders = [
    {
        "CustomerID": "TRANSFER",
        "cataName": "Test Product",
        "weight": 20.0,
        "quantity": 1,
        "StorageID": "S00001",  # Cu Chi (source)
        "toStorage": "S00002",  # BRENNTAG (destination)
        "offRoute": False
    }
]

def test_transfer_direction():
    """Test that storage transfers go from source to destination correctly"""
    
    try:
        # Send request to the backend
        response = requests.post(
            "http://localhost:5000/assign_trucks",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"orders": test_orders})
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Transfer test successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check the route to verify direction
            if data.get("assigned_vehicles"):
                for vehicle in data["assigned_vehicles"]:
                    print(f"\n🚚 Vehicle {vehicle.get('truckId')}:")
                    print(f"   Type: {vehicle.get('type')}")
                    print(f"   Load: {vehicle.get('currentLoad')}kg")
                    
                    # Check assigned customers for transfer
                    for customer in vehicle.get("assignedCustomers", []):
                        if "Relocate" in customer.get("customerName", ""):
                            print(f"   Transfer: {customer['customerName']}")
                    
                    # Check route
                    print("   Route:")
                    for step in vehicle.get("route", []):
                        if len(step) >= 2:
                            step_type, step_id = step[0], step[1]
                            if step_type == "storage":
                                print(f"     🏭 Pickup at storage {step_id}")
                            elif step_type == "customer":
                                print(f"     📦 Delivery to {step_id}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing storage transfer direction fix...")
    test_transfer_direction()
