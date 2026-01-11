"""
Analysis service
Handles cycle comparison, deviation detection, and root cause analysis
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from scipy import signal, stats
from sklearn.metrics.pairwise import cosine_similarity

from app.models.models import Cycle, Deviation, Dataset
from app.services.cycle_service import CycleService
from app.schemas.analysis import (
    ComparisonResponse,
    DeviationDetail,
    DeviationType,
    DeviationAnalysisResponse,
    AnomalyDetectionResponse,
    RootCauseAnalysisResponse,
    RootCauseContributor
)


class AnalysisService:
    """Service for cycle analysis and deviation detection"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cycle_service = CycleService(db)
    
    def compare_cycles(
        self,
        cycle_id: int,
        reference_cycle_id: int,
        sensors: Optional[List[str]] = None
    ) -> ComparisonResponse:
        """Compare two cycles and identify deviations"""
        
        cycle = self.cycle_service.get_cycle(cycle_id)
        ref_cycle = self.cycle_service.get_cycle(reference_cycle_id)
        
        if not cycle or not ref_cycle:
            raise ValueError("Cycle not found")
        
        if cycle.dataset_id != ref_cycle.dataset_id:
            raise ValueError("Cycles must be from the same dataset")
        
        # Load cycle data
        cycle_data = self._load_cycle_sensor_data(cycle)
        ref_data = self._load_cycle_sensor_data(ref_cycle)
        
        # Compare sensors
        sensors_to_compare = sensors or list(cycle_data.keys())
        deviations = []
        similarity_scores = []
        
        for sensor_name in sensors_to_compare:
            if sensor_name not in cycle_data or sensor_name not in ref_data:
                continue
            
            sensor_deviations, similarity = self._compare_sensor_data(
                cycle_data[sensor_name],
                ref_data[sensor_name],
                sensor_name,
                "reference"
            )
            
            deviations.extend(sensor_deviations)
            similarity_scores.append(similarity)
        
        overall_similarity = np.mean(similarity_scores) if similarity_scores else 0.0
        
        # Generate summary
        summary = self._generate_comparison_summary(deviations, overall_similarity)
        
        # Store deviations in database
        self._store_deviations(cycle_id, deviations, reference_cycle_id)
        
        return ComparisonResponse(
            cycle_id=cycle_id,
            reference_cycle_id=reference_cycle_id,
            similarity_score=overall_similarity,
            deviations=deviations,
            summary=summary
        )
    
    def analyze_deviations(
        self,
        cycle_id: int,
        compare_to_reference: bool = True,
        compare_to_previous: bool = True
    ) -> Optional[DeviationAnalysisResponse]:
        """Analyze deviations for a cycle"""
        
        cycle = self.cycle_service.get_cycle(cycle_id)
        if not cycle:
            return None
        
        deviations_from_reference = []
        deviations_from_previous = []
        
        # Compare to reference cycle
        if compare_to_reference:
            ref_cycle = self.cycle_service.get_reference_cycle(cycle.dataset_id)
            if ref_cycle and ref_cycle.id != cycle_id:
                comparison = self.compare_cycles(cycle_id, ref_cycle.id)
                deviations_from_reference = comparison.deviations
        
        # Compare to previous cycle
        if compare_to_previous:
            prev_cycle = self.cycle_service.get_previous_cycle(cycle_id)
            if prev_cycle:
                comparison = self.compare_cycles(cycle_id, prev_cycle.id)
                deviations_from_previous = comparison.deviations
        
        # Calculate overall health score
        all_deviations = deviations_from_reference + deviations_from_previous
        health_score = self._calculate_health_score(all_deviations)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            deviations_from_reference,
            deviations_from_previous
        )
        
        # Update cycle anomaly status
        is_anomalous = health_score < 0.7
        cycle.is_anomalous = is_anomalous
        cycle.anomaly_score = 1.0 - health_score
        self.db.commit()
        
        return DeviationAnalysisResponse(
            cycle_id=cycle_id,
            has_deviations=len(all_deviations) > 0,
            deviations_from_reference=deviations_from_reference,
            deviations_from_previous=deviations_from_previous,
            overall_health_score=health_score,
            recommendations=recommendations
        )
    
    def detect_anomalies(
        self,
        dataset_id: int,
        threshold: float = 0.8
    ) -> List[AnomalyDetectionResponse]:
        """Detect anomalous cycles in a dataset"""
        
        cycles = self.cycle_service.list_cycles_by_dataset(dataset_id, limit=10000)
        
        anomalies = []
        for cycle in cycles:
            if cycle.anomaly_score and cycle.anomaly_score > (1.0 - threshold):
                # Get top contributing sensors
                top_sensors = self._get_top_contributing_sensors(cycle.id)
                
                description = f"Cycle {cycle.cycle_number} shows anomalous behavior"
                if top_sensors:
                    description += f" in sensors: {', '.join(top_sensors[:3])}"
                
                anomalies.append(AnomalyDetectionResponse(
                    cycle_id=cycle.id,
                    cycle_number=cycle.cycle_number,
                    anomaly_score=cycle.anomaly_score,
                    is_anomalous=cycle.is_anomalous,
                    top_contributing_sensors=top_sensors,
                    description=description
                ))
        
        return anomalies
    
    def analyze_root_cause(
        self,
        cycle_id: int,
        time_window_seconds: Optional[float] = None
    ) -> Optional[RootCauseAnalysisResponse]:
        """Analyze root cause for abnormal cycle termination"""
        
        cycle = self.cycle_service.get_cycle(cycle_id)
        if not cycle or cycle.is_complete:
            return None
        
        # Determine analysis window
        stop_time = cycle.end_time
        if time_window_seconds:
            window_start = max(cycle.start_time, stop_time - time_window_seconds)
        else:
            # Default to last 10% of cycle duration
            window_duration = cycle.duration * 0.1
            window_start = stop_time - window_duration
        
        # Load cycle data
        cycle_data = self._load_cycle_sensor_data(cycle)
        
        # Load reference cycle data
        ref_cycle = self.cycle_service.get_reference_cycle(cycle.dataset_id)
        if not ref_cycle:
            return None
        
        ref_data = self._load_cycle_sensor_data(ref_cycle)
        
        # Analyze each sensor in the window
        contributors = []
        for sensor_name in cycle_data.keys():
            if sensor_name not in ref_data:
                continue
            
            # Extract window data
            sensor_series = cycle_data[sensor_name]
            window_data = sensor_series[
                (sensor_series['time'] >= window_start) &
                (sensor_series['time'] <= stop_time)
            ]
            
            if len(window_data) == 0:
                continue
            
            # Calculate deviation score
            deviation_score, deviation_type, deviation_time = self._calculate_window_deviation(
                window_data,
                ref_data[sensor_name],
                window_start,
                stop_time
            )
            
            if deviation_score > 0.3:  # Threshold for significance
                description = self._describe_deviation(
                    sensor_name,
                    deviation_type,
                    deviation_score
                )
                
                contributors.append(RootCauseContributor(
                    sensor_name=sensor_name,
                    contribution_score=deviation_score,
                    deviation_type=deviation_type,
                    time_of_deviation=deviation_time,
                    description=description
                ))
        
        # Sort by contribution score
        contributors.sort(key=lambda x: x.contribution_score, reverse=True)
        
        # Determine most likely cause
        if contributors:
            top_contributor = contributors[0]
            most_likely_cause = f"Abnormal behavior in {top_contributor.sensor_name}"
            confidence = min(top_contributor.contribution_score, 0.95)
        else:
            most_likely_cause = "No clear deviation detected in available sensors"
            confidence = 0.1
        
        return RootCauseAnalysisResponse(
            cycle_id=cycle_id,
            stop_time=stop_time,
            analysis_window_start=window_start,
            analysis_window_end=stop_time,
            ranked_contributors=contributors,
            most_likely_cause=most_likely_cause,
            confidence=confidence
        )
    
    def _load_cycle_sensor_data(self, cycle: Cycle) -> Dict[str, pd.DataFrame]:
        """Load sensor data for a cycle as dict of DataFrames"""
        cycle_detail = self.cycle_service.get_cycle_detail(cycle.id, include_data=True)
        
        sensor_data_dict = {}
        for sensor_data in cycle_detail.sensor_data:
            df = pd.DataFrame({
                'time': sensor_data.timestamps,
                'value': sensor_data.values
            })
            sensor_data_dict[sensor_data.sensor_name] = df
        
        return sensor_data_dict
    
    def _compare_sensor_data(
        self,
        sensor_data: pd.DataFrame,
        ref_data: pd.DataFrame,
        sensor_name: str,
        compared_to: str
    ) -> Tuple[List[DeviationDetail], float]:
        """Compare sensor data between two cycles"""
        
        deviations = []
        
        # Resample or interpolate to same length if needed
        if len(sensor_data) != len(ref_data):
            sensor_values = self._resample_series(sensor_data['value'].values, len(ref_data))
            ref_values = ref_data['value'].values
        else:
            sensor_values = sensor_data['value'].values
            ref_values = ref_data['value'].values
        
        # Calculate similarity
        similarity = self._calculate_similarity(sensor_values, ref_values)
        
        # Detect different types of deviations
        
        # 1. Amplitude deviation
        amplitude_dev = self._detect_amplitude_deviation(sensor_values, ref_values)
        if amplitude_dev > 0.2:
            deviations.append(DeviationDetail(
                sensor_name=sensor_name,
                deviation_type=DeviationType.AMPLITUDE,
                severity=amplitude_dev,
                compared_to=compared_to,
                details={"description": "Significant amplitude difference detected"}
            ))
        
        # 2. Shape deviation (using correlation)
        shape_dev = self._detect_shape_deviation(sensor_values, ref_values)
        if shape_dev > 0.2:
            deviations.append(DeviationDetail(
                sensor_name=sensor_name,
                deviation_type=DeviationType.SHAPE,
                severity=shape_dev,
                compared_to=compared_to,
                details={"description": "Signal shape differs from reference"}
            ))
        
        # 3. Timing deviation (using cross-correlation for phase shift)
        timing_dev = self._detect_timing_deviation(sensor_values, ref_values)
        if timing_dev > 0.2:
            deviations.append(DeviationDetail(
                sensor_name=sensor_name,
                deviation_type=DeviationType.TIMING,
                severity=timing_dev,
                compared_to=compared_to,
                details={"description": "Timing offset detected"}
            ))
        
        return deviations, similarity
    
    def _calculate_similarity(self, series1: np.ndarray, series2: np.ndarray) -> float:
        """Calculate similarity between two time series (0-1 scale)"""
        # Normalize series
        s1_norm = (series1 - np.mean(series1)) / (np.std(series1) + 1e-10)
        s2_norm = (series2 - np.mean(series2)) / (np.std(series2) + 1e-10)
        
        # Calculate correlation
        correlation = np.corrcoef(s1_norm, s2_norm)[0, 1]
        
        # Convert to similarity (0-1 scale)
        similarity = (correlation + 1) / 2
        
        return float(np.clip(similarity, 0, 1))
    
    def _detect_amplitude_deviation(self, series1: np.ndarray, series2: np.ndarray) -> float:
        """Detect amplitude deviation"""
        mean1 = np.mean(series1)
        mean2 = np.mean(series2)
        std1 = np.std(series1)
        std2 = np.std(series2)
        
        # Normalized difference
        mean_diff = abs(mean1 - mean2) / (abs(mean2) + 1e-10)
        std_diff = abs(std1 - std2) / (abs(std2) + 1e-10)
        
        severity = min((mean_diff + std_diff) / 2, 1.0)
        return float(severity)
    
    def _detect_shape_deviation(self, series1: np.ndarray, series2: np.ndarray) -> float:
        """Detect shape deviation using correlation"""
        correlation = np.corrcoef(series1, series2)[0, 1]
        severity = max(0, 1 - abs(correlation))
        return float(severity)
    
    def _detect_timing_deviation(self, series1: np.ndarray, series2: np.ndarray) -> float:
        """Detect timing/phase deviation"""
        # Use cross-correlation to find phase shift
        correlation = signal.correlate(series1, series2, mode='same')
        lag = np.argmax(correlation) - len(series1) // 2
        
        # Normalize lag to severity score
        max_lag = len(series1) * 0.1  # 10% of signal length
        severity = min(abs(lag) / max_lag, 1.0)
        
        return float(severity)
    
    def _resample_series(self, series: np.ndarray, target_length: int) -> np.ndarray:
        """Resample a series to target length using interpolation"""
        x_old = np.linspace(0, 1, len(series))
        x_new = np.linspace(0, 1, target_length)
        return np.interp(x_new, x_old, series)
    
    def _calculate_health_score(self, deviations: List[DeviationDetail]) -> float:
        """Calculate overall health score from deviations"""
        if not deviations:
            return 1.0
        
        # Weight different deviation types
        weights = {
            DeviationType.AMPLITUDE: 0.8,
            DeviationType.SHAPE: 1.0,
            DeviationType.TIMING: 0.6,
            DeviationType.OVERALL: 1.0
        }
        
        weighted_sum = sum(
            dev.severity * weights.get(dev.deviation_type, 1.0)
            for dev in deviations
        )
        
        total_weight = sum(weights.get(dev.deviation_type, 1.0) for dev in deviations)
        
        avg_deviation = weighted_sum / total_weight if total_weight > 0 else 0
        health_score = max(0, 1.0 - avg_deviation)
        
        return float(health_score)
    
    def _generate_comparison_summary(
        self,
        deviations: List[DeviationDetail],
        similarity: float
    ) -> str:
        """Generate human-readable comparison summary"""
        if similarity > 0.9:
            return "Cycles are highly similar with minimal deviations."
        elif similarity > 0.7:
            return f"Cycles show moderate similarity with {len(deviations)} deviation(s) detected."
        else:
            return f"Cycles differ significantly. {len(deviations)} deviation(s) detected across multiple sensors."
    
    def _generate_recommendations(
        self,
        ref_deviations: List[DeviationDetail],
        prev_deviations: List[DeviationDetail]
    ) -> List[str]:
        """Generate recommendations based on deviations"""
        recommendations = []
        
        if not ref_deviations and not prev_deviations:
            recommendations.append("Cycle operating normally")
            return recommendations
        
        # Group by sensor
        sensor_deviations = {}
        for dev in ref_deviations + prev_deviations:
            if dev.sensor_name not in sensor_deviations:
                sensor_deviations[dev.sensor_name] = []
            sensor_deviations[dev.sensor_name].append(dev)
        
        # Generate recommendations per sensor
        for sensor, devs in sensor_deviations.items():
            avg_severity = np.mean([d.severity for d in devs])
            if avg_severity > 0.7:
                recommendations.append(f"Inspect {sensor} - high severity deviation detected")
            elif avg_severity > 0.4:
                recommendations.append(f"Monitor {sensor} - moderate deviation detected")
        
        if len(recommendations) == 0:
            recommendations.append("Minor deviations detected - continue monitoring")
        
        return recommendations[:5]  # Limit to top 5
    
    def _store_deviations(
        self,
        cycle_id: int,
        deviations: List[DeviationDetail],
        reference_cycle_id: Optional[int] = None
    ):
        """Store deviations in database"""
        for dev in deviations:
            deviation = Deviation(
                cycle_id=cycle_id,
                sensor_name=dev.sensor_name,
                deviation_type=dev.deviation_type.value,
                severity=dev.severity,
                compared_to=dev.compared_to,
                reference_cycle_id=reference_cycle_id,
                time_start=dev.time_start,
                time_end=dev.time_end,
                details=dev.details
            )
            self.db.add(deviation)
        
        self.db.commit()
    
    def _get_top_contributing_sensors(self, cycle_id: int, limit: int = 5) -> List[str]:
        """Get sensors with highest deviation severity"""
        deviations = (
            self.db.query(Deviation)
            .filter(Deviation.cycle_id == cycle_id)
            .order_by(Deviation.severity.desc())
            .limit(limit)
            .all()
        )
        
        return [dev.sensor_name for dev in deviations]
    
    def _calculate_window_deviation(
        self,
        window_data: pd.DataFrame,
        ref_data: pd.DataFrame,
        window_start: float,
        window_end: float
    ) -> Tuple[float, DeviationType, float]:
        """Calculate deviation score for a time window"""
        
        if len(window_data) == 0:
            return 0.0, DeviationType.OVERALL, window_start
        
        # Simple approach: compare statistics in window
        window_mean = window_data['value'].mean()
        window_std = window_data['value'].std()
        
        ref_mean = ref_data['value'].mean()
        ref_std = ref_data['value'].std()
        
        # Calculate normalized deviations
        mean_dev = abs(window_mean - ref_mean) / (abs(ref_mean) + 1e-10)
        std_dev = abs(window_std - ref_std) / (abs(ref_std) + 1e-10)
        
        overall_deviation = min((mean_dev + std_dev) / 2, 1.0)
        
        # Determine deviation type
        if mean_dev > std_dev:
            dev_type = DeviationType.AMPLITUDE
        else:
            dev_type = DeviationType.SHAPE
        
        # Find time of maximum deviation
        if len(window_data) > 0:
            deviation_time = window_data.iloc[-1]['time']  # Use last time point
        else:
            deviation_time = window_start
        
        return float(overall_deviation), dev_type, float(deviation_time)
    
    def _describe_deviation(
        self,
        sensor_name: str,
        deviation_type: DeviationType,
        score: float
    ) -> str:
        """Generate human-readable deviation description"""
        severity_text = "high" if score > 0.7 else "moderate" if score > 0.4 else "low"
        
        type_descriptions = {
            DeviationType.AMPLITUDE: "amplitude anomaly",
            DeviationType.SHAPE: "pattern change",
            DeviationType.TIMING: "timing shift",
            DeviationType.OVERALL: "abnormal behavior"
        }
        
        return f"{sensor_name} shows {severity_text} {type_descriptions[deviation_type]}"
