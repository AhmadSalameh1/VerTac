"""
Real-time deviation analysis pipeline for completed cycles
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from scipy import signal
from scipy.spatial.distance import euclidean
import logging


logger = logging.getLogger(__name__)


@dataclass
class SensorDeviation:
    """Deviation metrics for a single sensor"""
    sensor_id: str
    sensor_name: str
    euclidean_distance: float
    dtw_distance: float
    max_deviation: float
    mean_deviation: float
    peak_deviation_time: Optional[str] = None
    contribution_rank: int = 0
    severity: str = "normal"  # normal, warning, critical


@dataclass
class CycleAnalysisResult:
    """Complete analysis result for a cycle"""
    cycle_id: str
    reference_cycle_id: str
    comparison_type: str  # "reference" or "previous"
    completed_at: str
    
    sensor_deviations: List[SensorDeviation]
    overall_health_score: float  # 0-100
    anomaly_flag: bool
    
    top_3_problematic_sensors: List[Tuple[str, float]]
    alerts: List[Dict]


class DeviationAnalyzer:
    """Analyzes deviations between cycles"""
    
    def __init__(self):
        self.anomaly_threshold = 0.7  # Deviation score threshold for anomaly
        self.warning_threshold = 0.5
    
    def normalize_signal(self, values: np.ndarray) -> np.ndarray:
        """Normalize signal to 0-1 range"""
        if len(values) == 0:
            return values
        
        min_val = np.min(values)
        max_val = np.max(values)
        
        if max_val == min_val:
            return np.zeros_like(values)
        
        return (values - min_val) / (max_val - min_val)
    
    def smooth_signal(self, values: np.ndarray, window_length: int = 11) -> np.ndarray:
        """Apply Savitzky-Golay filter for smoothing"""
        if len(values) < window_length:
            return values
        
        try:
            return signal.savgol_filter(values, window_length, polyorder=3)
        except:
            return values
    
    def euclidean_distance(
        self,
        completed_values: np.ndarray,
        reference_values: np.ndarray
    ) -> float:
        """Calculate Euclidean distance between signals"""
        # Ensure same length
        min_len = min(len(completed_values), len(reference_values))
        completed_values = completed_values[:min_len]
        reference_values = reference_values[:min_len]
        
        # Normalize
        completed_norm = self.normalize_signal(completed_values)
        reference_norm = self.normalize_signal(reference_values)
        
        # Calculate distance
        return float(euclidean(completed_norm, reference_norm))
    
    def dtw_distance(
        self,
        completed_values: np.ndarray,
        reference_values: np.ndarray
    ) -> float:
        """Calculate Dynamic Time Warping distance"""
        # Ensure same length by interpolation
        if len(completed_values) != len(reference_values):
            from scipy.interpolate import interp1d
            
            x_completed = np.linspace(0, 1, len(completed_values))
            x_reference = np.linspace(0, 1, len(reference_values))
            x_common = np.linspace(0, 1, max(len(completed_values), len(reference_values)))
            
            f_completed = interp1d(x_completed, completed_values, kind='linear', fill_value='extrapolate')
            f_reference = interp1d(x_reference, reference_values, kind='linear', fill_value='extrapolate')
            
            completed_values = f_completed(x_common)
            reference_values = f_reference(x_common)
        
        # Normalize
        completed_norm = self.normalize_signal(completed_values)
        reference_norm = self.normalize_signal(reference_values)
        
        # DTW calculation (simplified)
        n, m = len(completed_norm), len(reference_norm)
        dtw_matrix = np.full((n + 1, m + 1), np.inf)
        dtw_matrix[0, 0] = 0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(completed_norm[i-1] - reference_norm[j-1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i-1, j],
                    dtw_matrix[i, j-1],
                    dtw_matrix[i-1, j-1]
                )
        
        return float(dtw_matrix[n, m])
    
    def compute_deviation_metrics(
        self,
        completed_values: np.ndarray,
        reference_values: np.ndarray
    ) -> Dict:
        """Compute all deviation metrics"""
        # Point-wise deviation
        min_len = min(len(completed_values), len(reference_values))
        completed_values = completed_values[:min_len]
        reference_values = reference_values[:min_len]
        
        deviations = np.abs(completed_values - reference_values)
        
        return {
            "max_deviation": float(np.max(deviations)),
            "mean_deviation": float(np.mean(deviations)),
            "std_deviation": float(np.std(deviations)),
            "peak_index": int(np.argmax(deviations)) if len(deviations) > 0 else 0,
        }
    
    def analyze_sensor(
        self,
        sensor_id: str,
        sensor_name: str,
        completed_values: List[float],
        reference_values: List[float]
    ) -> SensorDeviation:
        """Analyze a single sensor's deviation"""
        completed_array = np.array(completed_values)
        reference_array = np.array(reference_values)
        
        # Smooth both signals
        completed_smooth = self.smooth_signal(completed_array)
        reference_smooth = self.smooth_signal(reference_array)
        
        # Compute distances
        euclidean_dist = self.euclidean_distance(completed_smooth, reference_smooth)
        dtw_dist = self.dtw_distance(completed_smooth, reference_smooth)
        
        # Compute metrics
        metrics = self.compute_deviation_metrics(completed_array, reference_array)
        
        # Determine severity
        # Use weighted combination of distances
        combined_score = 0.6 * (euclidean_dist / 10.0) + 0.4 * (dtw_dist / 100.0)
        combined_score = min(1.0, combined_score)
        
        if combined_score > self.anomaly_threshold:
            severity = "critical"
        elif combined_score > self.warning_threshold:
            severity = "warning"
        else:
            severity = "normal"
        
        return SensorDeviation(
            sensor_id=sensor_id,
            sensor_name=sensor_name,
            euclidean_distance=euclidean_dist,
            dtw_distance=dtw_dist,
            max_deviation=metrics["max_deviation"],
            mean_deviation=metrics["mean_deviation"],
            peak_deviation_time=None,  # Would need timestamps
            severity=severity
        )
    
    def analyze_cycle(
        self,
        cycle_id: str,
        completed_samples: Dict[str, List[float]],
        reference_samples: Dict[str, List[float]],
        reference_cycle_id: str,
        comparison_type: str = "reference"
    ) -> CycleAnalysisResult:
        """Analyze a completed cycle against reference"""
        logger.info(f"🔬 Analyzing cycle {cycle_id}...")
        
        sensor_deviations = []
        
        # Analyze each sensor
        for sensor_id, values in completed_samples.items():
            if sensor_id not in reference_samples:
                logger.warning(f"⚠️  Sensor {sensor_id} missing in reference")
                continue
            
            deviation = self.analyze_sensor(
                sensor_id=sensor_id,
                sensor_name=sensor_id,  # Would get from metadata
                completed_values=values,
                reference_values=reference_samples[sensor_id]
            )
            sensor_deviations.append(deviation)
        
        # Rank sensors by contribution
        sensor_deviations.sort(
            key=lambda x: x.euclidean_distance + x.dtw_distance,
            reverse=True
        )
        for i, deviation in enumerate(sensor_deviations, 1):
            deviation.contribution_rank = i
        
        # Calculate overall health score
        if sensor_deviations:
            severity_scores = {
                "critical": 0.0,
                "warning": 0.5,
                "normal": 1.0
            }
            
            avg_severity = np.mean([
                severity_scores.get(d.severity, 0.5)
                for d in sensor_deviations
            ])
            
            overall_health_score = avg_severity * 100.0
        else:
            overall_health_score = 100.0
        
        # Determine anomaly
        anomaly_flag = overall_health_score < 70.0
        
        # Generate alerts
        alerts = []
        for deviation in sensor_deviations:
            if deviation.severity in ["warning", "critical"]:
                alerts.append({
                    "sensor_id": deviation.sensor_id,
                    "sensor_name": deviation.sensor_name,
                    "severity": deviation.severity,
                    "message": f"{deviation.sensor_name} shows {deviation.severity} deviation",
                    "euclidean_distance": round(deviation.euclidean_distance, 4),
                    "dtw_distance": round(deviation.dtw_distance, 4),
                })
        
        # Top 3 problematic sensors
        top_3 = [
            (d.sensor_name, round(d.euclidean_distance + d.dtw_distance, 4))
            for d in sensor_deviations[:3]
        ]
        
        logger.info(f"✅ Analysis complete. Health score: {overall_health_score:.1f}")
        
        return CycleAnalysisResult(
            cycle_id=cycle_id,
            reference_cycle_id=reference_cycle_id,
            comparison_type=comparison_type,
            completed_at="2026-01-11T10:30:00Z",  # Would use actual time
            sensor_deviations=sensor_deviations,
            overall_health_score=overall_health_score,
            anomaly_flag=anomaly_flag,
            top_3_problematic_sensors=top_3,
            alerts=alerts
        )


# Example usage
if __name__ == "__main__":
    analyzer = DeviationAnalyzer()
    
    # Create synthetic data
    import numpy as np
    
    # Reference cycle (normal)
    reference_samples = {
        "motor_speed": list(np.sin(np.linspace(0, 4*np.pi, 100)) * 50 + 100),
        "vibration": list(np.random.normal(5, 1, 100)),
    }
    
    # Completed cycle (with deviation in motor_speed)
    completed_samples = {
        "motor_speed": list(np.sin(np.linspace(0, 4*np.pi, 100)) * 60 + 100),  # Larger amplitude
        "vibration": list(np.random.normal(5, 1, 100)),
    }
    
    result = analyzer.analyze_cycle(
        cycle_id="cycle-1",
        completed_samples=completed_samples,
        reference_samples=reference_samples,
        reference_cycle_id="cycle-0",
        comparison_type="reference"
    )
    
    print(f"\n📊 Analysis Result:")
    print(f"  Health Score: {result.overall_health_score:.1f}")
    print(f"  Anomaly Flag: {result.anomaly_flag}")
    print(f"  Alerts: {len(result.alerts)}")
    for alert in result.alerts:
        print(f"    - {alert['message']}")
