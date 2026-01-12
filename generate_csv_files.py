#!/usr/bin/env python
"""
Generate CSV files from mock data for uploading to VerTac system
"""

import sys
sys.path.insert(0, '/home/interferometer/VerTac/backend')

import pandas as pd
from pathlib import Path
from mock_data import get_mock_dataset, get_mock_cycle_with_data

# Output directory
output_dir = Path('/home/interferometer/VerTac/data')
output_dir.mkdir(exist_ok=True)

print("🔄 Generating CSV files from mock data...\n")

# Generate CSV for each dataset
datasets_info = [
    ("test_dataset_1", ["motor_speed", "voltage", "current", "temperature", "vibration"]),
    ("test_dataset_2", ["flow_rate", "pressure", "temperature", "power_consumption"]),
    ("test_dataset_3", ["force", "displacement", "acceleration", "surface_temp"]),
]

for dataset_key, sensors in datasets_info:
    print(f"📊 Generating {dataset_key}...")
    
    # Get dataset
    dataset_data = get_mock_dataset(dataset_key)
    dataset = dataset_data["dataset"]
    cycles = dataset_data["cycles"]
    
    # Collect all data points
    all_rows = []
    
    for cycle in cycles:
        # Get cycle with sensor data
        cycle_data = get_mock_cycle_with_data(
            cycle_number=cycle["cycle_number"],
            is_anomalous=cycle["is_anomalous"],
            sensors=sensors
        )
        
        # Extract sensor data
        sensor_data = cycle_data["sensor_data"]
        num_points = len(sensor_data[sensors[0]])
        
        # Create rows for this cycle
        for i in range(num_points):
            row = {
                "time": sensor_data[sensors[0]][i]["timestamp"],
                "cycle": cycle["cycle_number"],
            }
            
            # Add sensor values
            for sensor in sensors:
                row[sensor] = sensor_data[sensor][i]["value"]
            
            all_rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    # Save to CSV
    output_file = output_dir / f"{dataset_key}.csv"
    df.to_csv(output_file, index=False)
    
    print(f"   ✅ Created: {output_file}")
    print(f"   📈 Cycles: {len(cycles)}, Sensors: {len(sensors)}, Rows: {len(df)}")
    print()

print("=" * 70)
print("✅ CSV FILES GENERATED SUCCESSFULLY!")
print("=" * 70)
print("\nGenerated files:")
for dataset_key, _ in datasets_info:
    file_path = output_dir / f"{dataset_key}.csv"
    size = file_path.stat().st_size
    print(f"  📄 {file_path}")
    print(f"     Size: {size:,} bytes ({size/1024:.1f} KB)")
print(f"\nYou can now upload these files through the website at http://localhost:3000")
