"""
Hybrid Stroke Decision Engine for SwimAnalyzer AI.
Combines outputs from:
1. Video / Pose Detector
2. Quality / Visibility Gate
3. Existing Rule-Based Classifier (StrokeHeuristicClassifier)
4. AI Stroke Classifier (AIStrokeAgent)

Outputs the unified 6-part decision structure for the Coach UI:
- Stroke Type
- Confidence
- Evidence
- Rule Contributions
- AI Contributions
- Uncertainty
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np

from models.data_models import StrokeType, StrokeDetectionResult
from analysis.classification.visibility_gate import VisibilityGateResult
from core.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class HybridStrokeDecision:
    """Structured decision output produced by the Hybrid Decision Engine."""
    stroke_type: StrokeType
    confidence: float
    evidence: Dict[str, Any]
    rule_contributions: Dict[str, float]
    ai_contributions: Dict[str, float]
    uncertainty: float
    raw_detection_result: StrokeDetectionResult

class HybridStrokeDecisionEngine:
    """
    Fuses Evidence from Rule-Based Heuristics and AI Stroke Classifier
    to produce a unified, explainable decision for the Coach UI.
    """

    def __init__(self, rule_weight: float = 0.50, ai_weight: float = 0.50):
        self.rule_weight = rule_weight
        self.ai_weight = ai_weight

    def evaluate_hybrid_decision(
        self,
        rule_result: StrokeDetectionResult,
        ai_result: StrokeDetectionResult,
        visibility_result: VisibilityGateResult,
        selected_stroke_input: StrokeType = StrokeType.AUTO_DETECT
    ) -> HybridStrokeDecision:
        """
        Fuses predictions and feature evidence into a single HybridStrokeDecision object.
        """
        # Collect stroke type predictions
        strokes = [StrokeType.FREESTYLE, StrokeType.BACKSTROKE, StrokeType.BREASTSTROKE, StrokeType.BUTTERFLY]
        
        rule_preds = rule_result.predictions or {s.value: 0.25 for s in strokes}
        ai_preds = ai_result.predictions or {s.value: 0.25 for s in strokes}

        # Weight adjustment based on visibility quality
        w_rule = self.rule_weight
        w_ai = self.ai_weight

        # Fused Probabilities
        fused_probs: Dict[str, float] = {}
        for s in strokes:
            s_val = s.value
            p_rule = rule_preds.get(s_val, 0.25)
            p_ai = ai_preds.get(s_val, 0.25)
            fused_probs[s_val] = round(w_rule * p_rule + w_ai * p_ai, 4)

        # Normalize fused probabilities
        total_p = sum(fused_probs.values()) or 1.0
        for s_val in fused_probs:
            fused_probs[s_val] = round(fused_probs[s_val] / total_p, 4)

        # Identify Top Stroke Candidate
        top_stroke_str = max(fused_probs, key=fused_probs.get)
        top_confidence = fused_probs[top_stroke_str]
        chosen_stroke = StrokeType(top_stroke_str)

        # Calculate Uncertainty: 1.0 - Margin between top 1 and top 2 candidate probabilities
        sorted_probs = sorted(fused_probs.values(), reverse=True)
        top1 = sorted_probs[0]
        top2 = sorted_probs[1] if len(sorted_probs) > 1 else 0.0
        margin = top1 - top2
        uncertainty = round(max(0.0, min(1.0, 1.0 - margin)), 4)

        # Rule contributions dictionary
        rule_contribs = rule_result.feature_contributions or {"heuristic_arm_phase": 0.5, "roll_amplitude": 0.5}

        # AI contributions dictionary
        ai_contribs = ai_result.feature_contributions or {"ai_agent_ensemble": top_confidence}
        if ai_result.feature_values:
            for fk, fv in ai_result.feature_values.items():
                if fv is not None and isinstance(fv, (int, float)):
                    ai_contribs[fk] = round(float(fv), 4)

        # Evidence dictionary
        evidence = {
            "visibility_gate_status": "Passed" if visibility_result.is_sufficient else "Warning",
            "visibility_ratio": f"{visibility_result.visibility_ratio*100:.1f}%",
            "wrist_visibility": round(visibility_result.wrist_visibility, 2),
            "shoulder_visibility": round(visibility_result.shoulder_visibility, 2),
            "rule_top_candidate": rule_result.predicted_stroke.value,
            "rule_confidence": f"{rule_result.confidence*100:.1f}%",
            "ai_top_candidate": ai_result.predicted_stroke.value,
            "ai_confidence": f"{ai_result.confidence*100:.1f}%",
            "reasoning_summary": ai_result.classification_reason or rule_result.classification_reason
        }

        # Create unified StrokeDetectionResult for downstream consumption
        unified_detection_result = StrokeDetectionResult(
            predicted_stroke=chosen_stroke,
            confidence=top_confidence,
            predictions=fused_probs,
            selected_stroke=selected_stroke_input,
            manual_override=False,
            is_inconsistent=False,
            classification_status="ACCEPTED" if top_confidence >= 0.40 else "MODERATE_CONFIDENCE",
            classification_reason=f"Hybrid Decision Engine fused Rule-based ({rule_result.predicted_stroke.value}) + AI Agent ({ai_result.predicted_stroke.value}). Uncertainty: {uncertainty*100:.1f}%.",
            feature_values=ai_result.feature_values or {},
            feature_contributions=rule_contribs,
            classifier_version="2.0.0-Hybrid-Engine",
            threshold_version="HYBRID_DECISION_v2.0"
        )

        return HybridStrokeDecision(
            stroke_type=chosen_stroke,
            confidence=top_confidence,
            evidence=evidence,
            rule_contributions=rule_contribs,
            ai_contributions=ai_contribs,
            uncertainty=uncertainty,
            raw_detection_result=unified_detection_result
        )
