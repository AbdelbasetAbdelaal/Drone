from typing import Any
from analysis.strategies.base_strategy import BaseScoringEngine
from models.data_models import PerformanceReport

class ButterflyScoringEngine(BaseScoringEngine):
    def generate_report(self, analysis_result: Any, global_metrics: dict) -> PerformanceReport:
        score = 100.0
        feedback_lines = []

        # Safely extract values from ValidatedMetric objects
        def _val(key, default=0.0):
            m = global_metrics.get(key)
            if m is None:
                return default
            return m.value if hasattr(m, "value") else float(m)

        stroke_rate = global_metrics.get("stroke_rate")
        stroke_length = global_metrics.get("stroke_length")
        sr_value = _val("stroke_rate")
        undulation = _val("hip_undulation_amplitude")
        asymmetry = _val("avg_wrist_asymmetry")

        # Scoring deductions
        if sr_value > 60:
            score -= 10.0
            feedback_lines.append("Stroke rate too fast — you may be losing the two-beat kick rhythm.")

        if 0 < undulation < 0.1:
            score -= 12.0
            feedback_lines.append("Insufficient hip undulation. Initiate the dolphin kick from your chest and hips, not just your knees.")

        if asymmetry > 0.15:
            score -= 15.0
            feedback_lines.append("Significant arm asymmetry detected. Both arms should clear the water at the same time.")

        return PerformanceReport(
            overall_score=max(0.0, min(100.0, score)),
            stroke_rate=stroke_rate,
            stroke_length=stroke_length,
            kick_frequency=global_metrics.get("kick_frequency"),
            stroke_symmetry=global_metrics.get("stroke_symmetry"),
            feedback_summary="\n".join(feedback_lines) if feedback_lines else "Good butterfly technique.",
            errors=[]
        )
