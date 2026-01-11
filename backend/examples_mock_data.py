#!/usr/bin/env python
"""
Example script demonstrating mock data usage
Run this to see how to use mock_data.py for testing and development
"""

import json
from mock_data import (
    MOCK_DATASETS,
    get_mock_dataset,
    get_mock_cycle_with_data,
    generate_mock_sensor_data,
    MOCK_DEVIATIONS,
    MOCK_ANALYSIS_RESULTS,
)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def example_1_available_datasets():
    """Example 1: List available datasets"""
    print_section("Example 1: Available Datasets")
    
    for dataset_key, dataset_info in MOCK_DATASETS.items():
        print(f"📊 {dataset_key}")
        print(f"   Name: {dataset_info['name']}")
        print(f"   Format: {dataset_info['file_format']}")
        print(f"   Cycles: {dataset_info['total_cycles']}")
        print(f"   Size: {dataset_info['file_size'] / 1024:.1f} KB")
        print(f"   Sensors: {', '.join(dataset_info['sensors'][:3])}...")
        print()


def example_2_get_complete_dataset():
    """Example 2: Get a complete dataset with all cycles"""
    print_section("Example 2: Get Complete Dataset")
    
    dataset = get_mock_dataset("test_dataset_1")
    
    print(f"Dataset: {dataset['dataset']['name']}")
    print(f"ID: {dataset['dataset']['id']}")
    print(f"Description: {dataset['dataset']['description']}")
    print(f"\nCycles in dataset: {len(dataset['cycles'])}")
    
    for cycle in dataset["cycles"][:2]:
        status = "📍 REFERENCE" if cycle["is_reference"] else ""
        anomaly = "⚠️ ANOMALOUS" if cycle["is_anomalous"] else ""
        print(f"\n  Cycle {cycle['cycle_number']}: {cycle['duration']:.1f}s {status} {anomaly}")
        print(f"    - Time: {cycle['start_time']} to {cycle['end_time']} seconds")
        print(f"    - Operator: {cycle['cycle_metadata']['operator']}")


def example_3_cycle_with_sensor_data():
    """Example 3: Get a cycle with sensor time-series data"""
    print_section("Example 3: Cycle with Sensor Data")
    
    cycle_data = get_mock_cycle_with_data(
        cycle_number=1,
        is_anomalous=False,
        sensors=["motor_speed", "temperature"]
    )
    
    print(f"Cycle {cycle_data['cycle']['cycle_number']}")
    print(f"Duration: {cycle_data['cycle']['duration']:.1f} seconds")
    print(f"Anomalous: {cycle_data['cycle']['is_anomalous']}\n")
    
    for sensor_name, data_points in cycle_data["sensor_data"].items():
        print(f"📈 {sensor_name.upper()}")
        print(f"   Total points: {len(data_points)}")
        print(f"   Unit: {data_points[0]['unit']}")
        print(f"\n   Sample data (first 3 points):")
        
        for point in data_points[:3]:
            print(f"     {point['timestamp']:7.3f}s: {point['value']:8.2f} {point['unit']}")
        
        print(f"   ... ({len(data_points) - 3} more points)")
        print()


def example_4_sensor_data_generation():
    """Example 4: Generate custom sensor data"""
    print_section("Example 4: Generate Custom Sensor Data")
    
    print("Generating high-resolution temperature data with anomaly...\n")
    
    data = generate_mock_sensor_data(
        cycle_start=0.0,
        cycle_end=118.5,
        sensor_name="temperature",
        num_points=500,
        is_anomalous=True
    )
    
    print(f"Generated {len(data)} data points")
    print(f"Time range: {data[0]['timestamp']:.3f}s to {data[-1]['timestamp']:.3f}s")
    
    # Calculate statistics
    values = [p["value"] for p in data]
    print(f"\nTemperature Statistics:")
    print(f"  Min:    {min(values):.2f} °C")
    print(f"  Max:    {max(values):.2f} °C")
    print(f"  Mean:   {sum(values)/len(values):.2f} °C")
    print(f"  Range:  {max(values) - min(values):.2f} °C")


def example_5_anomalous_vs_normal():
    """Example 5: Compare normal vs anomalous cycles"""
    print_section("Example 5: Normal vs Anomalous Cycles")
    
    normal = get_mock_cycle_with_data(cycle_number=1, is_anomalous=False)
    anomalous = get_mock_cycle_with_data(cycle_number=3, is_anomalous=True)
    
    print("📊 NORMAL CYCLE (Cycle 1)")
    print(f"   Anomalous: {normal['cycle']['is_anomalous']}")
    temps_normal = [p["value"] for p in normal["sensor_data"]["temperature"]]
    print(f"   Temperature range: {min(temps_normal):.1f} - {max(temps_normal):.1f} °C")
    
    print("\n⚠️  ANOMALOUS CYCLE (Cycle 3)")
    print(f"   Anomalous: {anomalous['cycle']['is_anomalous']}")
    temps_anomalous = [p["value"] for p in anomalous["sensor_data"]["temperature"]]
    print(f"   Temperature range: {min(temps_anomalous):.1f} - {max(temps_anomalous):.1f} °C")
    
    # Analyze anomaly location (should be in last third)
    if len(temps_normal) >= 100:
        normal_last_third = temps_normal[len(temps_normal)//3:]
        anomalous_last_third = temps_anomalous[len(temps_anomalous)//3:]
        
        if normal_last_third and anomalous_last_third:
            normal_variation = max(normal_last_third) - min(normal_last_third)
            anomalous_variation = max(anomalous_last_third) - min(anomalous_last_third)
            
            print(f"\n   Last third temperature variation:")
            print(f"   Normal cycle:     {normal_variation:.2f} °C")
            print(f"   Anomalous cycle:  {anomalous_variation:.2f} °C")
            print(f"   Increase: {((anomalous_variation/normal_variation - 1) * 100):.1f}%")


def example_6_deviations():
    """Example 6: Mock deviation data"""
    print_section("Example 6: Deviation Detection Results")
    
    for deviation_key, deviation in MOCK_DEVIATIONS.items():
        print(f"🔴 {deviation['sensor_name'].upper()} - {deviation['deviation_type'].upper()}")
        print(f"   Severity: {deviation['severity']:.2f} (0-1 scale)")
        print(f"   Compared to: {deviation['compared_to']}")
        
        if "time_start" in deviation and deviation["time_start"]:
            duration = deviation.get("time_end", 0) - deviation.get("time_start", 0)
            print(f"   Time window: {deviation['time_start']:.1f}s - {deviation['time_end']:.1f}s ({duration:.1f}s)")
        
        print(f"   Details: {deviation['details']['description']}")
        print()


def example_7_analysis_results():
    """Example 7: Analysis and root cause analysis"""
    print_section("Example 7: Analysis Results")
    
    analysis = MOCK_ANALYSIS_RESULTS["cycle_comparison"]
    
    print(f"Cycle Comparison Analysis")
    print(f"Reference Cycle: {analysis['reference_cycle_id']}")
    print(f"Compared Cycle: {analysis['compared_cycle_id']}")
    
    print(f"\n📊 Comparison Metrics:")
    metrics = analysis['comparison_metrics']
    print(f"   Overall similarity: {metrics['overall_similarity']:.1%}")
    print(f"   Sensors analyzed: {metrics['sensors_analyzed']}")
    print(f"   Deviations found: {metrics['deviations_found']}")
    print(f"   Anomaly detected: {metrics['anomaly_detected']}")
    
    print(f"\n📋 Deviations Found:")
    for i, dev in enumerate(analysis['deviations'], 1):
        print(f"   {i}. {dev['sensor']} ({dev['type']})")
        print(f"      Severity: {dev['severity']:.2f}")
        print(f"      {dev['details']}")
    
    print(f"\n🔍 Root Cause Analysis:")
    rca = analysis['root_cause_analysis']
    print(f"   Most likely cause: {rca['most_likely_cause']}")
    print(f"   Confidence: {rca['confidence']:.1%}")
    print(f"   Contributing factors:")
    for factor in rca['contributing_factors']:
        print(f"     - {factor}")
    print(f"   Recommendations:")
    for rec in rca['recommendations']:
        print(f"     - {rec}")


def example_8_json_export():
    """Example 8: Export mock data as JSON"""
    print_section("Example 8: Export as JSON")
    
    dataset = get_mock_dataset("test_dataset_2")
    
    # Prepare data for JSON serialization
    json_data = {
        "dataset": dataset["dataset"],
        "cycles": dataset["cycles"][:1],  # Just first cycle
    }
    
    # Convert datetime objects to strings for JSON
    import datetime
    for key in ["upload_date"]:
        if key in json_data["dataset"]:
            json_data["dataset"][key] = json_data["dataset"][key].isoformat()
    
    print("Sample JSON output (formatted):")
    print(json.dumps(json_data, indent=2, default=str)[:500] + "...\n")


def main():
    """Run all examples"""
    print("\n" + "🎯 " * 20)
    print("\nVerTac Mock Data Examples")
    print("\n" + "🎯 " * 20)
    
    try:
        example_1_available_datasets()
        example_2_get_complete_dataset()
        example_3_cycle_with_sensor_data()
        example_4_sensor_data_generation()
        example_5_anomalous_vs_normal()
        example_6_deviations()
        example_7_analysis_results()
        example_8_json_export()
        
        print_section("Summary")
        print("""✅ Mock data provides:
  • 3 pre-built datasets with realistic scenarios
  • Configurable cycle generation (1-10 cycles per dataset)
  • Time-series sensor data generation (200-1000+ points)
  • Realistic anomaly patterns
  • Complete deviation detection results
  • Root cause analysis data
  
✅ All data is:
  • Fully compatible with VerTac models and schemas
  • Realistic and representative
  • Configurable and reproducible
  • Perfect for testing and development
  
Use cases:
  • Unit testing (test individual components)
  • Integration testing (test API endpoints)
  • Development (UI/UX with real data)
  • Demonstrations (show system capabilities)
  • Performance testing (various dataset sizes)
""")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
