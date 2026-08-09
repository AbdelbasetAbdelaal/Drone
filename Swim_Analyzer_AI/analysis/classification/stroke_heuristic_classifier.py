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
CONFIDENCE_THRESHOLD = 0.40

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
        feature_vals: Dict[str, Any] = {}
        missing_evidence: List[str] = []

        # Extract features without 0.0 fallbacks
        arm_phase = getattr(feature_set, 'arm_phase_correlation', None)
        body_roll_amp = getattr(feature_set, 'body_roll_amplitude', None)
        wrist_range = getattr(feature_set, 'wrist_vertical_range_ratio', None)
        leg_sym = getattr(feature_set, 'leg_kick_symmetry', None)

        phi_arm = arm_phase.raw_value if (arm_phase and arm_phase.valid and arm_phase.raw_value is not None) else None
        roll_amp = body_roll_amp.raw_value if (body_roll_amp and body_roll_amp.valid and body_roll_amp.raw_value is not None) else None
        wrist_range_val = wrist_range.raw_value if (wrist_range and wrist_range.valid and wrist_range.raw_value is not None) else None
        leg_sym_val = leg_sym.raw_value if (leg_sym and leg_sym.valid and leg_sym.raw_value is not None) else None

        if phi_arm is not None:
            feature_vals["arm_phase_correlation"] = phi_arm
        else:
            missing_evidence.append("arm_phase_correlation")

        if roll_amp is not None:
            feature_vals["body_roll_amplitude"] = roll_amp
        else:
            missing_evidence.append("body_roll_amplitude")

        if wrist_range_val is not None:
            feature_vals["wrist_vertical_range_ratio"] = wrist_range_val
        else:
            missing_evidence.append("wrist_vertical_range_ratio")

        if leg_sym_val is not None:
            feature_vals["leg_kick_symmetry"] = leg_sym_val
        else:
            missing_evidence.append("leg_kick_symmetry")

        # Strict evidence check: if arm phase is missing and body roll is missing
        if phi_arm is None and roll_amp is None:
            return StrokeDetectionResult(
                predicted_stroke=StrokeType.UNKNOWN,
                confidence=None,
                predictions={},
                selected_stroke=selected_stroke_input,
                manual_override=False,
                is_inconsistent=False,
                classification_status="INSUFFICIENT_EVIDENCE",
                classification_reason="Missing primary arm phase and body roll kinematic signals.",
                feature_values=feature_vals,
                feature_contributions={},
                missing_evidence=missing_evidence,
                classifier_version=self.classifier_version,
                threshold_version=self.threshold_version
            )

        # Fallback for submerged/low visibility arms: infer stroke rhythm from body roll amplitude ONLY if roll_amp exists
        if phi_arm is None and roll_amp is not None:
            if roll_amp > 10.0:
                phi_arm = -0.5 # High body roll implies alternating stroke
            else:
                phi_arm = +0.5 # Low body roll implies simultaneous stroke

        scores: Dict[StrokeType, float] = {
            StrokeType.FREESTYLE: 0.02,
            StrokeType.BACKSTROKE: 0.02,
            StrokeType.BREASTSTROKE: 0.02,
            StrokeType.BUTTERFLY: 0.02
        }
        contributions: Dict[str, float] = {}

        # Rule evaluation
        if phi_arm is not None and phi_arm < -0.3:
            contributions["arm_phase_alternating"] = +0.4
            roll_amp_check = roll_amp if roll_amp is not None else 0.0
            wrist_range_check = wrist_range_val if wrist_range_val is not None else 0.0
            if wrist_range_check > 0.12 or roll_amp_check > 15.0:
                scores[StrokeType.FREESTYLE] += 0.85
                scores[StrokeType.BACKSTROKE] += 0.10
                contributions["freestyle_roll_amplitude"] = +0.85
            else:
                scores[StrokeType.BACKSTROKE] += 0.85
                scores[StrokeType.FREESTYLE] += 0.10
                contributions["backstroke_roll_amplitude"] = +0.85

        elif phi_arm is not None and phi_arm > +0.3:
            contributions["arm_phase_simultaneous"] = +0.4
            wrist_range_check = wrist_range_val if wrist_range_val is not None else 0.0
            if wrist_range_check > 0.08:
                scores[StrokeType.BUTTERFLY] += 0.85
                scores[StrokeType.BREASTSTROKE] += 0.10
                contributions["butterfly_wrist_excursion"] = +0.85
            else:
                scores[StrokeType.BREASTSTROKE] += 0.85
                scores[StrokeType.BUTTERFLY] += 0.10
                contributions["breaststroke_wrist_excursion"] = +0.85

            if leg_sym_val is not None and leg_sym_val > +0.5:
                scores[StrokeType.BREASTSTROKE] += 0.10
                scores[StrokeType.BUTTERFLY] += 0.10
                contributions["leg_symmetry_simultaneous"] = +0.10
        else:
            # Ambiguous arm phase
            scores[StrokeType.FREESTYLE] += 0.40
            scores[StrokeType.BACKSTROKE] += 0.20
            scores[StrokeType.BREASTSTROKE] += 0.20
            scores[StrokeType.BUTTERFLY] += 0.20
            contributions["arm_phase_ambiguous"] = 0.40

        total_score = sum(scores.values())
        predictions: Dict[str, float] = {st.value: round(sc / total_score, 4) for st, sc in scores.items()}

        top_stroke_str = max(predictions, key=predictions.get)
        top_confidence = predictions[top_stroke_str]
        predicted_stroke = StrokeType(top_stroke_str)

        return StrokeDetectionResult(
            predicted_stroke=predicted_stroke,
            confidence=top_confidence,
            predictions=predictions,
            selected_stroke=selected_stroke_input,
            manual_override=False,
            is_inconsistent=False,
            classification_status="ACCEPTED" if top_confidence >= self.confidence_threshold else "MODERATE_CONFIDENCE",
            classification_reason=f"Kinematic rule match ({top_confidence*100:.1f}%) for {predicted_stroke.value}",
            feature_values=feature_vals,
            feature_contributions=contributions,
            missing_evidence=missing_evidence,
            rule_prediction=predicted_stroke,
            classifier_version=self.classifier_version,
            threshold_version=self.threshold_version
        )
