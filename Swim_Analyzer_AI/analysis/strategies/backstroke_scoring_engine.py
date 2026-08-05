from typing import Any
from analysis.strategies.base_strategy import BaseScoringEngine
from models.data_models import PerformanceReport

class BackstrokeScoringEngine(BaseScoringEngine):
    """Scoring engine for Backstroke analysis."""

    def generate_report(self, analysis_result: Any, global_metrics: dict) -> PerformanceReport:
        score = 100.0
        feedback_lines = []

        def _val(key, default=0.0):
            m = global_metrics.get(key)
            if m is None:
                return default
            return m.value if hasattr(m, "value") else float(m)

        stroke_rate = global_metrics.get("stroke_rate")
        stroke_length = global_metrics.get("stroke_length")
        sr_value = _val("stroke_rate")
        avg_body_roll = _val("average_body_roll")
        symmetry = _val("stroke_symmetry")

        # Stroke rate: backstroke typically 40–60 spm
        if sr_value > 65:
            score -= 8.0
            feedback_lines.append("Stroke rate is too fast. Focus on a longer, controlled pull.")
        elif 0 < sr_value < 30:
            score -= 5.0
            feedback_lines.append("Stroke rate is very slow. Maintain a consistent rhythm.")

        # Body roll: ideal backstroke body roll is 30–50°
        if avg_body_roll < 20 and avg_body_roll > 0:
            score -= 12.0
            feedback_lines.append(
                f"Insufficient body roll ({avg_body_roll:.1f}°). Rotate shoulders 30–50° to generate power.")
        elif avg_body_roll > 60:
            score -= 8.0
            feedback_lines.append(
                f"Excessive body roll ({avg_body_roll:.1f}°). Over-rotation reduces propulsion efficiency.")

        # Symmetry: ideal is close to 100
        if 0 < symmetry < 80:
            score -= 10.0
            feedback_lines.append(
                "Significant asymmetry between left and right arm pull. Aim for equal power on both sides.")

        return PerformanceReport(
            overall_score=max(0.0, min(100.0, score)),
            stroke_rate=stroke_rate,
            stroke_length=stroke_length,
            kick_frequency=global_metrics.get("kick_frequency"),
            stroke_symmetry=global_metrics.get("stroke_symmetry"),
            feedback_summary="\n".join(feedback_lines) if feedback_lines else "Good backstroke technique.",
            errors=[]
        )
