"""
Mock Data for VerTac Testing
This file contains sample data structures that are compatible with the VerTac system.
Used for unit tests, integration tests, and development.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# ============================================================================
# MOCK DATASET DATA
# ============================================================================

MOCK_DATASETS = {
    "test_dataset_1": {
        "name": "Motor Speed Test Run 001",
        "description": "High-speed motor operation test with normal operating conditions",
        "file_format": "csv",
        "file_size": 1024000,  # bytes
        "upload_date": datetime.now() - timedelta(days=5),
        "sensors": ["motor_speed", "voltage", "current", "temperature", "vibration"],
        "total_cycles": 5,
    },
    "test_dataset_2": {
        "name": "Pump Cycle Analysis",
        "description": "Water pump operating cycles during peak load conditions",
        "file_format": "xlsx",
        "file_size": 2048000,
        "upload_date": datetime.now() - timedelta(days=3),
        "sensors": ["flow_rate", "pressure", "temperature", "power_consumption"],
        "total_cycles": 8,
    },
    "test_dataset_3": {
        "name": "Production Line Quality Check",
        "description": "Manufacturing quality control measurements across 10 production cycles",
        "file_format": "csv",
        "file_size": 512000,
        "upload_date": datetime.now() - timedelta(days=1),
        "sensors": ["force", "displacement", "acceleration", "surface_temp"],
        "total_cycles": 10,
    },
}

# ============================================================================
# MOCK CYCLE DATA
# ============================================================================

def generate_mock_cycles(dataset_id: int, dataset_name: str, num_cycles: int = 5) -> List[Dict[str, Any]]:
    """Generate mock cycle data for a dataset"""
    cycles = []
    
    for cycle_num in range(1, num_cycles + 1):
        start_time = (cycle_num - 1) * 120.0  # Each cycle is ~2 minutes apart
        end_time = start_time + 118.5  # Cycle duration 118.5 seconds
        duration = end_time - start_time
        
        cycle = {
            "dataset_id": dataset_id,
            "cycle_number": cycle_num,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "is_complete": True,
            "is_reference": cycle_num == 1,  # First cycle is typically reference
            "is_anomalous": cycle_num in [3, 5],  # Simulate anomalies in cycles 3 and 5
            "anomaly_score": 0.72 if cycle_num == 3 else (0.85 if cycle_num == 5 else None),
            "cycle_metadata": {
                "operator": "John Doe",
                "ambient_temperature": 22.5 + (cycle_num * 0.1),
                "humidity": 45.2,
                "machine_mode": "normal" if cycle_num != 3 else "degraded",
                "notes": f"Cycle {cycle_num} execution normal" if cycle_num not in [3, 5] else f"Cycle {cycle_num} shows anomalies",
            },
        }
        cycles.append(cycle)
    
    return cycles

# ============================================================================
# MOCK SENSOR DATA (Time Series)
# ============================================================================

def generate_mock_sensor_data(
    cycle_start: float,
    cycle_end: float,
    sensor_name: str,
    num_points: int = 200,
    is_anomalous: bool = False,
) -> List[Dict[str, float]]:
    """
    Generate realistic time-series sensor data for a cycle
    
    Args:
        cycle_start: Start time of cycle
        cycle_end: End time of cycle
        sensor_name: Name of the sensor
        num_points: Number of data points
        is_anomalous: Whether to add anomalous patterns
    
    Returns:
        List of sensor data points with timestamp and value
    """
    import math
    
    data = []
    time_step = (cycle_end - cycle_start) / num_points
    
    # Base patterns for different sensors
    sensor_patterns = {
        "motor_speed": {
            "baseline": 1500,
            "amplitude": 100,
            "frequency": 0.5,
            "unit": "RPM",
        },
        "voltage": {
            "baseline": 230,
            "amplitude": 15,
            "frequency": 0.3,
            "unit": "V",
        },
        "current": {
            "baseline": 50,
            "amplitude": 8,
            "frequency": 0.4,
            "unit": "A",
        },
        "temperature": {
            "baseline": 65,
            "amplitude": 5,
            "frequency": 0.2,
            "unit": "C",
        },
        "vibration": {
            "baseline": 2.1,
            "amplitude": 0.5,
            "frequency": 0.6,
            "unit": "mm/s",
        },
        "flow_rate": {
            "baseline": 75,
            "amplitude": 10,
            "frequency": 0.3,
            "unit": "L/min",
        },
        "pressure": {
            "baseline": 4.2,
            "amplitude": 0.3,
            "frequency": 0.4,
            "unit": "bar",
        },
        "power_consumption": {
            "baseline": 2500,
            "amplitude": 200,
            "frequency": 0.5,
            "unit": "W",
        },
        "force": {
            "baseline": 500,
            "amplitude": 50,
            "frequency": 0.7,
            "unit": "N",
        },
        "displacement": {
            "baseline": 10,
            "amplitude": 2,
            "frequency": 0.4,
            "unit": "mm",
        },
        "acceleration": {
            "baseline": 9.81,
            "amplitude": 1.5,
            "frequency": 0.5,
            "unit": "m/s²",
        },
        "surface_temp": {
            "baseline": 45,
            "amplitude": 8,
            "frequency": 0.3,
            "unit": "C",
        },
    }
    
    pattern = sensor_patterns.get(sensor_name, {
        "baseline": 100,
        "amplitude": 10,
        "frequency": 0.5,
        "unit": "unit",
    })
    
    for i in range(num_points):
        timestamp = cycle_start + (i * time_step)
        
        # Normal sine wave pattern
        normalized_time = (i / num_points) * 2 * math.pi
        value = (
            pattern["baseline"] +
            pattern["amplitude"] * math.sin(normalized_time * pattern["frequency"])
        )
        
        # Add noise
        import random
        noise = random.gauss(0, pattern["amplitude"] * 0.05)
        value += noise
        
        # Add anomaly if flagged
        if is_anomalous:
            # Spike in last third of cycle
            if i > num_points * 0.65:
                anomaly_spike = pattern["amplitude"] * 0.8 * math.sin(
                    (i - num_points * 0.65) / (num_points * 0.35) * math.pi
                )
                value += anomaly_spike
        
        data.append({
            "timestamp": round(timestamp, 3),
            "value": round(value, 2),
            "unit": pattern["unit"],
        })
    
    return data

# ============================================================================
# MOCK DEVIATIONS DATA
# ============================================================================

MOCK_DEVIATIONS = {
    "amplitude_deviation": {
        "sensor_name": "motor_speed",
        "deviation_type": "amplitude",
        "severity": 0.72,
        "compared_to": "reference",
        "time_start": 85.2,
        "time_end": 110.5,
        "details": {
            "reference_value": 1500,
            "actual_value": 1620,
            "deviation_percent": 8.0,
            "description": "Motor speed exceeded nominal value by 8%",
        },
    },
    "shape_deviation": {
        "sensor_name": "voltage",
        "deviation_type": "shape",
        "severity": 0.45,
        "compared_to": "reference",
        "time_start": 30.1,
        "time_end": 95.8,
        "details": {
            "correlation_coefficient": 0.82,
            "description": "Voltage waveform shape differs significantly from reference",
            "euclidean_distance": 45.3,
        },
    },
    "timing_deviation": {
        "sensor_name": "temperature",
        "deviation_type": "timing",
        "severity": 0.38,
        "compared_to": "previous",
        "time_start": 40.0,
        "time_end": 80.0,
        "details": {
            "reference_peak_time": 60.5,
            "actual_peak_time": 52.3,
            "time_shift_seconds": -8.2,
            "description": "Temperature peak occurred 8.2 seconds earlier than reference",
        },
    },
    "overall_deviation": {
        "sensor_name": "current",
        "deviation_type": "overall",
        "severity": 0.65,
        "compared_to": "reference",
        "details": {
            "rms_difference": 12.5,
            "max_delta": 24.3,
            "description": "Current profile shows significant overall deviation",
        },
    },
}

# ============================================================================
# MOCK ANALYSIS RESULTS
# ============================================================================

MOCK_ANALYSIS_RESULTS = {
    "cycle_comparison": {
        "reference_cycle_id": 1,
        "compared_cycle_id": 3,
        "dataset_id": 1,
        "comparison_metrics": {
            "overall_similarity": 0.78,
            "sensors_analyzed": 5,
            "deviations_found": 3,
            "anomaly_detected": True,
        },
        "deviations": [
            {
                "sensor": "motor_speed",
                "type": "amplitude",
                "severity": 0.72,
                "details": "Motor running 8% faster than reference",
            },
            {
                "sensor": "voltage",
                "type": "shape",
                "severity": 0.45,
                "details": "Voltage waveform shape irregular",
            },
            {
                "sensor": "temperature",
                "type": "overall",
                "severity": 0.55,
                "details": "Temperature excursions beyond expected range",
            },
        ],
        "root_cause_analysis": {
            "most_likely_cause": "Motor bearing degradation",
            "confidence": 0.68,
            "contributing_factors": [
                "Elevated current consumption",
                "Increased vibration",
                "Temperature rise",
            ],
            "recommendations": [
                "Inspect motor bearings",
                "Check motor alignment",
                "Monitor temperature closely",
            ],
        },
    },
    "anomaly_detection": {
        "cycle_id": 5,
        "dataset_id": 1,
        "anomaly_detected": True,
        "anomaly_score": 0.85,
        "anomaly_type": "outlier",
        "severity": "high",
        "affected_sensors": ["current", "temperature", "vibration"],
        "anomaly_window": {
            "start_time": 80.0,
            "end_time": 110.0,
            "duration": 30.0,
        },
        "health_metrics": {
            "current_health_score": 0.42,
            "baseline_health_score": 0.92,
            "degradation_rate": 0.08,
            "estimated_remaining_life_hours": 240,
        },
    },
}

# ============================================================================
# HELPER FUNCTIONS FOR TEST DATA
# ============================================================================

def get_mock_dataset(dataset_key: str = "test_dataset_1") -> Dict[str, Any]:
    """Get a complete mock dataset with all related data"""
    if dataset_key not in MOCK_DATASETS:
        raise ValueError(f"Unknown dataset key: {dataset_key}")
    
    dataset_info = MOCK_DATASETS[dataset_key]
    dataset_id = list(MOCK_DATASETS.keys()).index(dataset_key) + 1
    
    return {
        "dataset": {
            "id": dataset_id,
            **dataset_info,
        },
        "cycles": generate_mock_cycles(
            dataset_id,
            dataset_key,
            dataset_info["total_cycles"],
        ),
    }

def get_mock_cycle_with_data(
    cycle_number: int = 1,
    is_anomalous: bool = False,
    sensors: List[str] = None,
) -> Dict[str, Any]:
    """Get a complete mock cycle with sensor data"""
    if sensors is None:
        sensors = ["motor_speed", "voltage", "current", "temperature"]
    
    start_time = (cycle_number - 1) * 120.0
    end_time = start_time + 118.5
    
    sensor_data = {}
    for sensor in sensors:
        sensor_data[sensor] = generate_mock_sensor_data(
            start_time,
            end_time,
            sensor,
            num_points=200,
            is_anomalous=is_anomalous,
        )
    
    return {
        "cycle": {
            "cycle_number": cycle_number,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "is_anomalous": is_anomalous,
        },
        "sensor_data": sensor_data,
    }

def get_all_mock_data() -> Dict[str, Any]:
    """Get all mock data structured together"""
    return {
        "datasets": MOCK_DATASETS,
        "cycles_generator": generate_mock_cycles,
        "sensor_data_generator": generate_mock_sensor_data,
        "deviations": MOCK_DEVIATIONS,
        "analysis_results": MOCK_ANALYSIS_RESULTS,
    }

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Get complete dataset
    dataset = get_mock_dataset("test_dataset_1")
    print("Dataset:")
    print(json.dumps(dataset["dataset"], indent=2, default=str))
    
    # Example: Get cycle with sensor data
    cycle_data = get_mock_cycle_with_data(cycle_number=1, is_anomalous=False)
    print("\n\nCycle with Sensor Data:")
    print(json.dumps(cycle_data, indent=2))
    
    # Example: Get deviations
    print("\n\nMock Deviations:")
    print(json.dumps(MOCK_DEVIATIONS, indent=2))
    
    # Example: Get analysis results
    print("\n\nMock Analysis Results:")
    print(json.dumps(MOCK_ANALYSIS_RESULTS, indent=2, default=str))
