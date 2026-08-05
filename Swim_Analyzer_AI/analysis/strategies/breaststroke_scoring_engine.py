from typing import Any
from analysis.strategies.base_strategy import BaseScoringEngine
from models.data_models import PerformanceReport, ValidatedMetric

class BreaststrokeScoringEngine(BaseScoringEngine):
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
        glide_ratio = _val("glide_ratio")
        max_knee_bend = _val("max_knee_bend_deg")
        sr_value = _val("stroke_rate")

        # Scoring deductions
        if sr_value > 55:
            score -= 10.0
            feedback_lines.append("Stroke rate too fast — losing glide efficiency. Slow down and hold the extension.")
        elif 0 < sr_value < 25:
            score -= 5.0
            feedback_lines.append("Stroke rate is very slow. Try to maintain a consistent rhythm.")

        if 0 < max_knee_bend < 60:
            score -= 8.0
            feedback_lines.append(f"Insufficient knee bend for whip kick ({max_knee_bend:.1f}°). Drive heels toward glutes.")

        if 0 < glide_ratio < 0.15:
            score -= 15.0
            feedback_lines.append("Missing distinct glide phase. Ensure full arm extension before starting the next outsweep.")

        return PerformanceReport(
            overall_score=max(0.0, min(100.0, score)),
            stroke_rate=global_metrics.get("stroke_rate") or ValidatedMetric(value=sr_value, valid=sr_value > 0),
            stroke_length=stroke_length,
            kick_frequency=global_metrics.get("kick_frequency"),
            stroke_symmetry=global_metrics.get("stroke_symmetry"),
            feedback_summary="\n".join(feedback_lines) if feedback_lines else "Good breaststroke technique.",
            errors=[]
        )
