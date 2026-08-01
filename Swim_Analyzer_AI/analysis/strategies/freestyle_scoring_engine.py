"""
Weighted scoring engine for evaluating swimming performance.
"""
import yaml
import numpy as np
from pathlib import Path
from typing import List, Any
from core.config import config
from models.data_models import AnalysisResult, MovementError, PerformanceReport
from core.logger import setup_logger
from analysis.strategies.base_strategy import BaseScoringEngine

logger = setup_logger(__name__)

class FreestyleScoringEngine(BaseScoringEngine):
    """
    Evaluates biomechanical data using a configurable weighted scoring model.
    """
    
    def __init__(self):
        self.weights = self._load_weights()
        
    def _load_weights(self) -> dict:
        try:
            with open(config.app_config_path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('scoring', {})
        except Exception as e:
            logger.error(f"Could not load scoring weights: {e}")
            return {}

    def generate_report(self, analysis_result: AnalysisResult, global_metrics: dict) -> PerformanceReport:
        """
        Generates the performance report and calculates the final score based on weights.
        """
        report = PerformanceReport()
        report.stroke_rate = global_metrics.get("stroke_rate")
        report.stroke_length = global_metrics.get("stroke_length")
        report.kick_frequency = global_metrics.get("kick_frequency")
        report.stroke_symmetry = global_metrics.get("stroke_symmetry")
        
        errors = []
        score_components = []
        
        # Helper to get score out of 100
        def calculate_component_score(value_list, ideal_min, ideal_max, error_name, error_desc):
            if not value_list:
                return 0, None
            avg_val = np.mean(value_list)
            if ideal_min <= avg_val <= ideal_max:
                return 100, None
            else:
                err = MovementError(-1, 0, error_name, f"{error_desc} (Measured: {avg_val:.1f})", "Medium")
                return 50, err

        # 1. Stroke Symmetry
        sym_weight = self.weights.get("symmetry_weight", 0.20)
        sym_score = report.stroke_symmetry.value if report.stroke_symmetry.valid else 100.0
        score_components.append(sym_score * sym_weight)
        if report.stroke_symmetry.valid and sym_score < 80:
            errors.append(MovementError(-1, 0, "Asymmetrical Pull", "Left and right arms have significantly different mechanics.", "High", confidence=report.stroke_symmetry.confidence))

        # 2. Elbow Angle during Pull
        elb_weight = self.weights.get("elbow_weight", 0.25)
        pull_elbows = []
        for f in analysis_result.frames:
            if f.is_valid and f.stroke_phase == "Pull":
                if f.angles.left_elbow and f.angles.left_elbow.valid: pull_elbows.append((f.angles.left_elbow.value, f.timestamp_ms))
                if f.angles.right_elbow and f.angles.right_elbow.valid: pull_elbows.append((f.angles.right_elbow.value, f.timestamp_ms))
        
        vals = [v[0] for v in pull_elbows]
        ts = pull_elbows[0][1] if pull_elbows else 0
        # Optimal high-elbow catch / mid-pull flexion is 90° to 120° (Maglischo, 2003)
        elb_score, elb_err = calculate_component_score(vals, 90, 120, "Dropped Elbow", "Average elbow angle during pull is outside optimal range (90°-120°).")
        score_components.append(elb_score * elb_weight)
        if elb_err: 
            elb_err.timestamp_ms = ts
            errors.append(elb_err)
        
        # 3. Shoulder Angle (Recovery/Reach)
        shoulder_weight = self.weights.get("shoulder_weight", 0.20)
        reach_shoulders = []
        for f in analysis_result.frames:
            if f.is_valid and f.stroke_phase == "Recovery":
                if f.angles.left_shoulder and f.angles.left_shoulder.valid: reach_shoulders.append((f.angles.left_shoulder.value, f.timestamp_ms))
                if f.angles.right_shoulder and f.angles.right_shoulder.valid: reach_shoulders.append((f.angles.right_shoulder.value, f.timestamp_ms))
                
        vals = [v[0] for v in reach_shoulders]
        ts = reach_shoulders[0][1] if reach_shoulders else 0
        sh_score, sh_err = calculate_component_score(vals, 140, 180, "Limited Shoulder Extension", "Shoulder extension during recovery is restricted.")
        score_components.append(sh_score * shoulder_weight)
        if sh_err: 
            sh_err.timestamp_ms = ts
            errors.append(sh_err)
        
        # 4. Hip Angle
        hip_weight = self.weights.get("hip_weight", 0.20)
        # We don't have hip angle in JointAngles yet, assuming 100% for MVP
        score_components.append(100 * hip_weight)
        
        # 5. Knee Angle
        knee_weight = self.weights.get("knee_weight", 0.15)
        knees = []
        for f in analysis_result.frames:
            if f.is_valid:
                if f.angles.left_knee and f.angles.left_knee.valid: knees.append((f.angles.left_knee.value, f.timestamp_ms))
                if f.angles.right_knee and f.angles.right_knee.valid: knees.append((f.angles.right_knee.value, f.timestamp_ms))
        
        vals = [v[0] for v in knees]
        ts = knees[0][1] if knees else 0
        kn_score, kn_err = calculate_component_score(vals, 130, 175, "Excessive Knee Bend", "Knees are bending too much during kicking.")
        score_components.append(kn_score * knee_weight)
        if kn_err: 
            kn_err.timestamp_ms = ts
            errors.append(kn_err)

        report.overall_score = sum(score_components)
        report.overall_score = max(0.0, min(100.0, report.overall_score))
        report.errors = errors
        
        cycles = analysis_result.stroke_statistics.completed_cycles if analysis_result.stroke_statistics else 0
        reliability_score = analysis_result.reliability.analysis_reliability_score if analysis_result.reliability else 100.0
        
        if cycles == 0:
            report.overall_score = 0.0
            report.feedback_summary = "No complete stroke cycle detected. Performance scoring is incomplete."
        elif reliability_score < 50.0:
            report.feedback_summary = "Analysis is inconclusive due to insufficient reliable biomechanical data. Metrics are marked as estimates."
        else:
            report.feedback_summary = self._generate_feedback_summary(report.overall_score, len(errors))
        
        return report

    def _generate_feedback_summary(self, score: float, error_count: int) -> str:
        if score >= 90:
            return "Excellent technique! Keep up the great form."
        elif score >= 75:
            return f"Good solid swim. We found {error_count} areas to focus on."
        elif score >= 60:
            return f"Fair technique. Working on these {error_count} errors will improve efficiency."
        else:
            return "Significant adjustments are recommended. Focus on core mechanics."
