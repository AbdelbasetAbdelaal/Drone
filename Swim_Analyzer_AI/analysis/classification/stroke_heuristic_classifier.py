"""
Explainable Stroke Heuristic Classifier for SwimAnalyzer AI.
Evaluates kinematic feature sets against explicit UNVALIDATED_HEURISTIC thresholds.
"""
from typing import Dict, Any, Tuple, Optional
from models.data_models import StrokeType, StrokeDetectionResult
from analysis.classification.feature_extractor import KinematicFeatureSet, KinematicFeatureExtractor
from core.logger import setup_logger

logger = setup_logger(__name__)

# EXPLICIT UNVALIDATED HEURISTIC THRESHOLD METADATA
CLASSIFIER_VERSION = "1.0.0-unvalidated"
THRESHOLD_VERSION = "UNVALIDATED_HEURISTIC_v1.0"
CONFIDENCE_THRESHOLD = 0.75

class StrokeHeuristicClassifier:
    """
    Explainable Heuristic Classifier for swimming stroke styles.
    Thresholds are strictly tagged as UNVALIDATED_HEURISTIC.
    """

    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold
        self.classifier_version = CLASSIFIER_VERSION
        self.threshold_version = THRESHOLD_VERSION

    def classify_features(self, feature_set: KinematicFeatureSet, selected_stroke_input: StrokeType = StrokeType.AUTO_DETECT) -> StrokeDetectionResult:
        """
        Classifies a KinematicFeatureSet using explainable kinematic heuristic rules.
        """
        # Collect extracted raw feature values
        feature_vals: Dict[str, float] = {}
        for feat_attr in ['arm_phase_correlation', 'mean_body_roll', 'body_roll_amplitude', 
                          'wrist_vertical_range_ratio', 'leg_kick_symmetry', 'wrist_recovery_height_ratio']:
            feat_obj = getattr(feature_set, feat_attr, None)
            if feat_obj and feat_obj.valid and feat_obj.raw_value is not None:
                feature_vals[feat_attr] = float(feat_obj.raw_value)

        # Check if mandatory features are valid
        arm_phase = feature_set.arm_phase_correlation
        body_roll_amp = feature_set.body_roll_amplitude

        if not arm_phase.valid or arm_phase.raw_value is None:
            reason = f"Missing arm phase correlation signal: {arm_phase.missing_data_condition or 'INVALID'}"
            return self._build_unknown_result(reason, feature_vals, selected_stroke_input)

        phi_arm = arm_phase.raw_value
        roll_amp = body_roll_amp.raw_value if (body_roll_amp and body_roll_amp.valid) else 0.0
        leg_sym = feature_set.leg_kick_symmetry.raw_value if (feature_set.leg_kick_symmetry and feature_set.leg_kick_symmetry.valid) else 0.0
        wrist_range = feature_set.wrist_vertical_range_ratio.raw_value if (feature_set.wrist_vertical_range_ratio and feature_set.wrist_vertical_range_ratio.valid) else 0.0

        scores: Dict[StrokeType, float] = {
            StrokeType.FREESTYLE: 0.02,
            StrokeType.BACKSTROKE: 0.02,
            StrokeType.BREASTSTROKE: 0.02,
            StrokeType.BUTTERFLY: 0.02
        }
        contributions: Dict[str, float] = {}

        # -------------------------------------------------------------
        # HEURISTIC RULE EVALUATION (UNVALIDATED_HEURISTIC_v1.0)
        # -------------------------------------------------------------
        # Rule 1: Alternating vs. Simultaneous Arm Motion
        if phi_arm < -0.3:
            # Alternating Stroke (Freestyle or Backstroke)
            contributions["arm_phase_alternating"] = +0.4

            # Sub-Rule 1a: Body Roll / Arm Recovery Range distinguishes Freestyle vs Backstroke
            if wrist_range > 0.12 or roll_amp > 15.0:
                scores[StrokeType.FREESTYLE] += 0.85
                scores[StrokeType.BACKSTROKE] += 0.10
                contributions["freestyle_roll_amplitude"] = +0.85
            else:
                scores[StrokeType.BACKSTROKE] += 0.85
                scores[StrokeType.FREESTYLE] += 0.10
                contributions["backstroke_roll_amplitude"] = +0.85

        elif phi_arm > +0.3:
            # Simultaneous Stroke (Breaststroke or Butterfly)
            contributions["arm_phase_simultaneous"] = +0.4

            # Sub-Rule 1b: Leg Symmetry and Wrist Vertical Excursion distinguish Breaststroke vs Butterfly
            if wrist_range > 0.25:
                scores[StrokeType.BUTTERFLY] += 0.85
                scores[StrokeType.BREASTSTROKE] += 0.10
                contributions["butterfly_wrist_excursion"] = +0.85
            else:
                scores[StrokeType.BREASTSTROKE] += 0.85
                scores[StrokeType.BUTTERFLY] += 0.10
                contributions["breaststroke_wrist_excursion"] = +0.85

            if leg_sym > +0.5:
                scores[StrokeType.BREASTSTROKE] += 0.10
                scores[StrokeType.BUTTERFLY] += 0.10
                contributions["leg_symmetry_simultaneous"] = +0.10
        else:
            # Ambiguous arm phase (-0.3 <= phi_arm <= +0.3)
            scores[StrokeType.FREESTYLE] += 0.25
            scores[StrokeType.BACKSTROKE] += 0.25
            scores[StrokeType.BREASTSTROKE] += 0.25
            scores[StrokeType.BUTTERFLY] += 0.25
            contributions["arm_phase_ambiguous"] = 0.0

        # Normalize Scores via Softmax/Probabilities
        total_score = sum(scores.values())
        predictions: Dict[str, float] = {}
        for st_key, raw_s in scores.items():
            predictions[st_key.value] = round(raw_s / total_score, 4)

        # Identify Top Prediction
        top_stroke_str = max(predictions, key=predictions.get)
        top_confidence = predictions[top_stroke_str]
        predicted_stroke = StrokeType(top_stroke_str)

        # -------------------------------------------------------------
        # CONFIDENCE SAFETY GATING
        # -------------------------------------------------------------
        if top_confidence >= self.confidence_threshold:
            status = "ACCEPTED"
            reason = f"High confidence kinematic match ({top_confidence*100:.1f}%) for {predicted_stroke.value}"
            final_pred_stroke = predicted_stroke
        else:
            status = "INSUFFICIENT_CONFIDENCE"
            reason = f"Top prediction confidence ({top_confidence*100:.1f}%) below safety threshold ({self.confidence_threshold*100:.0f}%). Declared UNKNOWN."
            final_pred_stroke = StrokeType.UNKNOWN

        return StrokeDetectionResult(
            predicted_stroke=final_pred_stroke,
            confidence=top_confidence,
            predictions=predictions,
            selected_stroke=selected_stroke_input,
            manual_override=False,
            is_inconsistent=False,
            classification_status=status,
            classification_reason=reason,
            feature_values=feature_vals,
            feature_contributions=contributions,
            classifier_version=self.classifier_version,
            threshold_version=self.threshold_version
        )

    def _build_unknown_result(self, reason: str, feature_vals: Dict[str, float], selected_stroke: StrokeType) -> StrokeDetectionResult:
        predictions = {
            StrokeType.FREESTYLE.value: 0.25,
            StrokeType.BACKSTROKE.value: 0.25,
            StrokeType.BREASTSTROKE.value: 0.25,
            StrokeType.BUTTERFLY.value: 0.25
        }
        return StrokeDetectionResult(
            predicted_stroke=StrokeType.UNKNOWN,
            confidence=0.0,
            predictions=predictions,
            selected_stroke=selected_stroke,
            manual_override=False,
            is_inconsistent=False,
            classification_status="UNKNOWN",
            classification_reason=reason,
            feature_values=feature_vals,
            feature_contributions={"missing_data": 1.0},
            classifier_version=self.classifier_version,
            threshold_version=self.threshold_version
        )
