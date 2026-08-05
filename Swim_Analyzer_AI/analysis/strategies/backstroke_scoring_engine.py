from typing import Any
from analysis.strategies.base_strategy import BaseScoringEngine
from models.data_models import PerformanceReport

class BackstrokeScoringEngine(BaseScoringEngine):
    def generate_report(self, analysis_result: Any, global_metrics: dict) -> PerformanceReport:
        # Placeholder logic for Backstroke scoring.
        return PerformanceReport(
            overall_score=75.0,
            technique_score=80.0,
            consistency_score=70.0,
            stroke_rate_spm=global_metrics.get("average_stroke_rate", 0),
            stroke_length_meters=global_metrics.get("stroke_length_meters", 0),
            turn_time_seconds=0.0,
            breakdown={"body_roll": 40.0, "symmetry": 0.85},
            feedback=["Keep your head steady.", "Rotate shoulders, not hips."],
            warnings=[]
        )
