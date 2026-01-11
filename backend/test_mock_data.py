"""
Test examples using mock data
Demonstrates how to use mock_data.py for testing
"""

import pytest
from datetime import datetime
from mock_data import (
    MOCK_DATASETS,
    MOCK_DEVIATIONS,
    MOCK_ANALYSIS_RESULTS,
    get_mock_dataset,
    get_mock_cycle_with_data,
    generate_mock_sensor_data,
    get_all_mock_data,
)


# ============================================================================
# UNIT TEST EXAMPLES
# ============================================================================

class TestMockDataStructures:
    """Test that mock data has correct structure"""
    
    def test_datasets_have_required_fields(self):
        """Verify mock datasets have all required fields"""
        required_fields = {
            "name",
            "description",
            "file_format",
            "file_size",
            "upload_date",
            "sensors",
            "total_cycles",
        }
        
        for dataset_key, dataset in MOCK_DATASETS.items():
            assert required_fields.issubset(dataset.keys()), \
                f"Dataset {dataset_key} missing required fields"
            
            # Validate field types
            assert isinstance(dataset["name"], str)
            assert isinstance(dataset["file_size"], int)
            assert isinstance(dataset["sensors"], list)
            assert isinstance(dataset["total_cycles"], int)
    
    def test_deviations_have_required_fields(self):
        """Verify mock deviations have correct structure"""
        required_fields = {
            "sensor_name",
            "deviation_type",
            "severity",
            "compared_to",
            "details",
        }
        
        for dev_key, deviation in MOCK_DEVIATIONS.items():
            assert required_fields.issubset(deviation.keys()), \
                f"Deviation {dev_key} missing required fields"
            
            # Validate field types and ranges
            assert isinstance(deviation["severity"], float)
            assert 0 <= deviation["severity"] <= 1, \
                "Severity must be between 0 and 1"
            assert deviation["deviation_type"] in [
                "shape",
                "timing",
                "amplitude",
                "overall",
            ]
    
    def test_analysis_results_structure(self):
        """Verify analysis results have correct structure"""
        analysis = MOCK_ANALYSIS_RESULTS["cycle_comparison"]
        
        assert "comparison_metrics" in analysis
        assert "deviations" in analysis
        assert "root_cause_analysis" in analysis
        
        # Verify metrics
        metrics = analysis["comparison_metrics"]
        assert 0 <= metrics["overall_similarity"] <= 1
        assert isinstance(metrics["anomaly_detected"], bool)


class TestMockDataGeneration:
    """Test mock data generation functions"""
    
    def test_get_mock_dataset(self):
        """Test dataset retrieval"""
        dataset = get_mock_dataset("test_dataset_1")
        
        assert "dataset" in dataset
        assert "cycles" in dataset
        assert len(dataset["cycles"]) == 5
        
        # Verify dataset structure
        ds = dataset["dataset"]
        assert ds["id"] == 1
        assert ds["name"] == "Motor Speed Test Run 001"
    
    def test_get_mock_cycle_with_data(self):
        """Test cycle with sensor data generation"""
        cycle = get_mock_cycle_with_data(cycle_number=1, is_anomalous=False)
        
        assert "cycle" in cycle
        assert "sensor_data" in cycle
        
        # Verify cycle info
        assert cycle["cycle"]["cycle_number"] == 1
        assert cycle["cycle"]["is_anomalous"] is False
        
        # Verify sensor data
        sensors = cycle["sensor_data"]
        assert len(sensors) >= 1
        
        for sensor_name, data_points in sensors.items():
            assert len(data_points) == 200  # 200 data points
            assert "timestamp" in data_points[0]
            assert "value" in data_points[0]
            assert "unit" in data_points[0]
    
    def test_generate_sensor_data(self):
        """Test sensor data generation"""
        data = generate_mock_sensor_data(
            cycle_start=0.0,
            cycle_end=118.5,
            sensor_name="motor_speed",
            num_points=100,
            is_anomalous=False,
        )
        
        assert len(data) == 100
        
        # Verify data point structure
        point = data[0]
        assert "timestamp" in point
        assert "value" in point
        assert "unit" in point
        
        # Verify timestamps are in order
        for i in range(len(data) - 1):
            assert data[i]["timestamp"] < data[i + 1]["timestamp"]
    
    def test_anomalous_data_generation(self):
        """Test that anomalous data is different from normal"""
        normal_data = generate_mock_sensor_data(
            cycle_start=0.0,
            cycle_end=118.5,
            sensor_name="temperature",
            num_points=200,
            is_anomalous=False,
        )
        
        anomalous_data = generate_mock_sensor_data(
            cycle_start=0.0,
            cycle_end=118.5,
            sensor_name="temperature",
            num_points=200,
            is_anomalous=True,
        )
        
        # Last third should be more different in anomalous data
        normal_last_third = [p["value"] for p in normal_data[133:]]
        anomalous_last_third = [p["value"] for p in anomalous_data[133:]]
        
        normal_range = max(normal_last_third) - min(normal_last_third)
        anomalous_range = max(anomalous_last_third) - min(anomalous_last_third)
        
        # Anomalous should have more variation
        assert anomalous_range > normal_range


class TestMockDataCompatibility:
    """Test that mock data is compatible with system requirements"""
    
    def test_sensor_names_consistency(self):
        """Verify all referenced sensors exist in patterns"""
        from mock_data import generate_mock_sensor_data
        
        # Get unique sensor names from datasets
        sensor_names = set()
        for dataset in MOCK_DATASETS.values():
            sensor_names.update(dataset["sensors"])
        
        # Test that each sensor can generate data without error
        for sensor in sensor_names:
            data = generate_mock_sensor_data(
                cycle_start=0.0,
                cycle_end=100.0,
                sensor_name=sensor,
                num_points=50,
                is_anomalous=False,
            )
            assert len(data) > 0, f"Failed to generate data for {sensor}"
    
    def test_timestamp_ranges(self):
        """Verify timestamps are within valid ranges"""
        for dataset in MOCK_DATASETS.values():
            cycles = get_mock_cycle_with_data(
                cycle_number=1,
                sensors=dataset["sensors"][:1],
            )
            
            cycle = cycles["cycle"]
            assert cycle["end_time"] > cycle["start_time"]
            assert cycle["duration"] > 0
    
    def test_data_completeness_for_api(self):
        """Verify mock data has all fields needed for API responses"""
        dataset = get_mock_dataset("test_dataset_1")
        
        # Check dataset response fields
        ds = dataset["dataset"]
        assert "id" in ds
        assert "name" in ds
        assert "file_format" in ds
        assert "sensors" in ds
        assert "total_cycles" in ds
        
        # Check cycle response fields
        cycle = dataset["cycles"][0]
        assert "cycle_number" in cycle
        assert "start_time" in cycle
        assert "end_time" in cycle
        assert "duration" in cycle
        assert "is_complete" in cycle
        assert "is_reference" in cycle
        assert "is_anomalous" in cycle


# ============================================================================
# INTEGRATION TEST EXAMPLES
# ============================================================================

class TestMockDataIntegration:
    """Integration tests using mock data"""
    
    def test_dataset_cycle_relationship(self):
        """Test that cycles properly reference datasets"""
        dataset = get_mock_dataset("test_dataset_1")
        
        for cycle in dataset["cycles"]:
            assert cycle["dataset_id"] == dataset["dataset"]["id"]
    
    def test_deviation_references_valid_cycles(self):
        """Verify deviations reference existing cycles"""
        dataset = get_mock_dataset("test_dataset_1")
        cycle_numbers = [c["cycle_number"] for c in dataset["cycles"]]
        
        # Deviations should reference valid cycles
        for dev_key, deviation in MOCK_DEVIATIONS.items():
            assert "details" in deviation
            assert isinstance(deviation["details"], dict)
    
    def test_analysis_consistency(self):
        """Test analysis results reference valid cycles"""
        dataset = get_mock_dataset("test_dataset_1")
        analysis = MOCK_ANALYSIS_RESULTS["cycle_comparison"]
        
        # Check that referenced cycles exist
        assert "reference_cycle_id" in analysis
        assert "compared_cycle_id" in analysis


# ============================================================================
# EXAMPLE TESTS FOR SPECIFIC SCENARIOS
# ============================================================================

class TestMockDataScenarios:
    """Scenario-based tests using mock data"""
    
    def test_normal_operation_scenario(self):
        """Test scenario: Normal motor operation"""
        cycle = get_mock_cycle_with_data(
            cycle_number=1,
            is_anomalous=False,
            sensors=["motor_speed", "temperature"],
        )
        
        assert cycle["cycle"]["is_anomalous"] is False
        
        # Verify sensor values are within normal ranges
        motor_speed = cycle["sensor_data"]["motor_speed"]
        for point in motor_speed:
            # Motor speed should be around 1500 RPM ±100
            assert 1300 < point["value"] < 1700
    
    def test_degraded_operation_scenario(self):
        """Test scenario: Degraded motor operation (anomalous)"""
        cycle = get_mock_cycle_with_data(
            cycle_number=3,
            is_anomalous=True,
            sensors=["motor_speed", "current", "temperature"],
        )
        
        assert cycle["cycle"]["is_anomalous"] is True
        
        # Verify anomalous pattern exists
        temperature = cycle["sensor_data"]["temperature"]
        last_third = [p["value"] for p in temperature[133:]]
        first_third = [p["value"] for p in temperature[:67]]
        
        # Last third should show more variation (anomaly spike)
        assert max(last_third) > max(first_third) + 2
    
    def test_multiple_sensors_analysis(self):
        """Test scenario: Analyze multiple sensors together"""
        sensors_to_analyze = ["motor_speed", "voltage", "current", "temperature"]
        cycle = get_mock_cycle_with_data(
            cycle_number=1,
            sensors=sensors_to_analyze,
        )
        
        assert len(cycle["sensor_data"]) == len(sensors_to_analyze)
        
        # All sensors should have same number of points (synchronized)
        point_counts = [
            len(data) for data in cycle["sensor_data"].values()
        ]
        assert all(count == point_counts[0] for count in point_counts)


# ============================================================================
# PERFORMANCE/LOAD TESTS
# ============================================================================

class TestMockDataPerformance:
    """Performance tests for mock data generation"""
    
    def test_large_dataset_generation(self):
        """Test generating data for larger datasets"""
        # Generate dataset with many cycles
        dataset = get_mock_dataset("test_dataset_2")
        
        assert len(dataset["cycles"]) == 8
    
    def test_high_resolution_sensor_data(self):
        """Test generating high-resolution sensor data"""
        # Generate 1000 data points per cycle
        data = generate_mock_sensor_data(
            cycle_start=0.0,
            cycle_end=118.5,
            sensor_name="motor_speed",
            num_points=1000,
            is_anomalous=False,
        )
        
        assert len(data) == 1000
        
        # Verify data quality
        for point in data:
            assert isinstance(point["timestamp"], float)
            assert isinstance(point["value"], float)


if __name__ == "__main__":
    # Run with: python -m pytest test_mock_data.py -v
    pytest.main([__file__, "-v"])
