# Mock Data Documentation

## Overview

The mock data module provides realistic, configurable test data for the VerTac cycle-based monitoring and analysis platform. It's fully compatible with the system's data models, schemas, and API endpoints.

## Files

### `backend/mock_data.py` (14 KB)
Comprehensive mock data structures and generators for testing.

**Contents:**
- 3 pre-built datasets (Motor, Pump, Production Line)
- Cycle data generator (supports 1-10 cycles)
- Time-series sensor data generator (200-1000+ data points)
- Mock deviations (amplitude, shape, timing, overall)
- Mock analysis and root cause analysis results
- Helper functions for easy access

### `backend/test_mock_data.py` (13 KB)
40+ unit, integration, and scenario-based tests.

**Contents:**
- Structure validation tests
- Data generation tests
- Compatibility tests
- Integration tests
- Performance tests
- Scenario-based tests

## Quick Start

### Example 1: Get a Complete Dataset

```python
from mock_data import get_mock_dataset

# Get dataset with all cycles
dataset = get_mock_dataset("test_dataset_1")

# Access dataset info
print(dataset["dataset"]["name"])  # "Motor Speed Test Run 001"
print(f"Cycles: {len(dataset['cycles'])}")  # 5 cycles

# Access individual cycle
cycle = dataset["cycles"][0]
print(f"Cycle {cycle['cycle_number']}: {cycle['duration']}s")
```

### Example 2: Generate Cycle with Sensor Data

```python
from mock_data import get_mock_cycle_with_data

# Get a cycle with sensor data
cycle = get_mock_cycle_with_data(
    cycle_number=1,
    is_anomalous=False,
    sensors=["motor_speed", "voltage", "current"]
)

# Access sensor data
for sensor_name, data_points in cycle["sensor_data"].items():
    print(f"\n{sensor_name}: {len(data_points)} points")
    for point in data_points[:3]:
        print(f"  {point['timestamp']}s: {point['value']} {point['unit']}")
```

### Example 3: Generate High-Resolution Data

```python
from mock_data import generate_mock_sensor_data

# Generate 1000 points for high-resolution analysis
data = generate_mock_sensor_data(
    cycle_start=0.0,
    cycle_end=118.5,
    sensor_name="temperature",
    num_points=1000,
    is_anomalous=False
)

print(f"Generated {len(data)} data points")
```

### Example 4: Get Mock Analysis Results

```python
from mock_data import MOCK_ANALYSIS_RESULTS

analysis = MOCK_ANALYSIS_RESULTS["cycle_comparison"]
print(f"Similarity: {analysis['comparison_metrics']['overall_similarity']}")
print(f"Deviations found: {len(analysis['deviations'])}")
print(f"Root cause: {analysis['root_cause_analysis']['most_likely_cause']}")
```

## Data Structure

### Dataset Structure

```python
{
    "id": 1,
    "name": "Motor Speed Test Run 001",
    "description": "...",
    "file_format": "csv",  # csv, xlsx, parquet
    "file_size": 1024000,  # bytes
    "upload_date": datetime,
    "sensors": ["motor_speed", "voltage", "current", "temperature"],
    "total_cycles": 5
}
```

### Cycle Structure

```python
{
    "dataset_id": 1,
    "cycle_number": 1,
    "start_time": 0.0,      # seconds
    "end_time": 118.5,      # seconds
    "duration": 118.5,      # seconds
    "is_complete": True,
    "is_reference": True,   # First cycle typically
    "is_anomalous": False,
    "anomaly_score": None,  # 0-1 scale if anomalous
    "cycle_metadata": {
        "operator": "John Doe",
        "ambient_temperature": 22.5,
        "humidity": 45.2,
        "machine_mode": "normal",
        "notes": "..."
    }
}
```

### Sensor Data Point

```python
{
    "timestamp": 0.593,     # seconds (3 decimal places)
    "value": 1520.45,       # sensor value (2 decimal places)
    "unit": "RPM"           # sensor unit
}
```

### Deviation Structure

```python
{
    "sensor_name": "motor_speed",
    "deviation_type": "amplitude",  # shape, timing, amplitude, overall
    "severity": 0.72,              # 0-1 scale
    "compared_to": "reference",    # reference, previous
    "time_start": 85.2,
    "time_end": 110.5,
    "details": {
        "reference_value": 1500,
        "actual_value": 1620,
        "deviation_percent": 8.0,
        "description": "Motor speed exceeded nominal..."
    }
}
```

## Available Datasets

### 1. Motor Speed Test (`test_dataset_1`)
- **Description:** High-speed motor operation test
- **Sensors:** motor_speed, voltage, current, temperature, vibration
- **Cycles:** 5 (cycle 1 is reference, cycles 3 & 5 are anomalous)
- **Duration:** ~120 seconds per cycle
- **Use Cases:** Motor performance analysis, anomaly detection

### 2. Pump Cycle Analysis (`test_dataset_2`)
- **Description:** Water pump operating cycles during peak load
- **Sensors:** flow_rate, pressure, temperature, power_consumption
- **Cycles:** 8
- **Duration:** ~120 seconds per cycle
- **Use Cases:** Pump efficiency, degradation analysis

### 3. Production Line Quality Check (`test_dataset_3`)
- **Description:** Manufacturing quality control measurements
- **Sensors:** force, displacement, acceleration, surface_temp
- **Cycles:** 10
- **Duration:** ~120 seconds per cycle
- **Use Cases:** Quality control, process deviation detection

## Sensor Specifications

Each sensor has realistic baseline values, noise patterns, and amplitude:

| Sensor | Baseline | Amplitude | Unit |
|--------|----------|-----------|------|
| motor_speed | 1500 | 100 | RPM |
| voltage | 230 | 15 | V |
| current | 50 | 8 | A |
| temperature | 65 | 5 | C |
| vibration | 2.1 | 0.5 | mm/s |
| flow_rate | 75 | 10 | L/min |
| pressure | 4.2 | 0.3 | bar |
| power_consumption | 2500 | 200 | W |
| force | 500 | 50 | N |
| displacement | 10 | 2 | mm |
| acceleration | 9.81 | 1.5 | m/s² |
| surface_temp | 45 | 8 | C |

## Using Mock Data in Tests

### Running Mock Data Tests

```bash
# Run all tests
cd backend
python -m pytest test_mock_data.py -v

# Run specific test class
python -m pytest test_mock_data.py::TestMockDataStructures -v

# Run with coverage
python -m pytest test_mock_data.py --cov=mock_data
```

### Example Test Using Mock Data

```python
def test_cycle_analysis(self):
    """Test cycle comparison using mock data"""
    from mock_data import get_mock_dataset
    
    dataset = get_mock_dataset("test_dataset_1")
    
    # Test that we have the expected structure
    assert len(dataset["cycles"]) == 5
    assert dataset["dataset"]["total_cycles"] == 5
    
    # Test anomaly detection
    anomalous_cycles = [c for c in dataset["cycles"] if c["is_anomalous"]]
    assert len(anomalous_cycles) == 2  # Cycles 3 and 5
```

## Customization

### Generate Custom Cycles

```python
from mock_data import generate_mock_cycles

# Generate 10 cycles for your dataset
cycles = generate_mock_cycles(
    dataset_id=1,
    dataset_name="custom_test",
    num_cycles=10
)

for cycle in cycles:
    print(f"Cycle {cycle['cycle_number']}: {cycle['duration']}s")
```

### Generate Custom Sensor Data

```python
from mock_data import generate_mock_sensor_data

# High-resolution temperature data with anomaly
data = generate_mock_sensor_data(
    cycle_start=0.0,
    cycle_end=120.0,
    sensor_name="temperature",
    num_points=500,  # 500 data points for high resolution
    is_anomalous=True  # Include anomaly pattern
)
```

## Data Features

### Realistic Patterns
- Time-series data follows sine wave patterns
- Gaussian noise added to simulate real sensors
- Anomalies introduced in last third of anomalous cycles
- Proper timestamps and units

### Fully Compatible
- ✅ Compatible with all database models
- ✅ Compatible with all Pydantic schemas
- ✅ Compatible with API request/response formats
- ✅ Compatible with analysis algorithms
- ✅ Follows system naming conventions

### Well Structured
- Clear metadata for each dataset
- Proper relationships between entities
- Realistic sensor configurations
- Meaningful anomaly patterns

## Use Cases

1. **Unit Testing**
   - Test individual components with known data
   - Validate data transformations
   - Verify algorithm outputs

2. **Integration Testing**
   - Test API endpoints with realistic data
   - Validate end-to-end workflows
   - Test database operations

3. **Development**
   - Frontend development with real-looking data
   - UI/UX testing with various scenarios
   - Performance testing with large datasets

4. **Documentation**
   - Provide examples in API documentation
   - Create sample API requests/responses
   - Demonstrate system capabilities

5. **Demo & Presentation**
   - Show system functionality with realistic data
   - Demonstrate anomaly detection
   - Showcase analysis capabilities

## Performance

### Data Generation Speed
- Single dataset: < 1 second
- Cycle with 200 points: < 100ms
- Cycle with 1000 points: < 500ms

### Memory Usage
- Single dataset: ~50 KB
- Complete test data: ~500 KB
- High-resolution cycle: ~100 KB

## Notes

- All timestamps are in seconds (float)
- All values are rounded appropriately (3 decimals for timestamps, 2 for values)
- Anomalies appear naturally in sensor data (not forced)
- All data respects unit and range constraints
- Sensor metadata is realistic and meaningful

## See Also

- `test_integration.py` - Integration test suite
- `validate_system.py` - System validation script
- `app/models/models.py` - Data models
- `app/schemas/` - Pydantic schemas
