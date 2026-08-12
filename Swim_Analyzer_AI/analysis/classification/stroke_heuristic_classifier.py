"""
Explainable Stroke Heuristic Classifier for SwimAnalyzer AI.
Evaluates kinematic feature sets against explicit UNVALIDATED_HEURISTIC thresholds.
"""
from typing import Any, Dict, List
from models.data_models import StrokeType, StrokeDetectionResult
from analysis.classification.feature_extractor import KinematicFeatureSet
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
        Missing evidence propagates strictly without zero substitutions or artificial inferences.
        """
        feature_vals: Dict[str, Any] = {}
        missing_evidence: List[str] = []

        # Extract features without 0.0 fallbacks or artificial inferences
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

        # Zero-Fallback Guard: Return INSUFFICIENT_EVIDENCE if arm phase is missing or ambiguous
        if phi_arm is None:
            return StrokeDetectionResult(
                predicted_stroke=StrokeType.UNKNOWN,
                confidence=None,
                predictions={},
                selected_stroke=selected_stroke_input,
                manual_override=False,
                is_inconsistent=False,
                classification_status="INSUFFICIENT_EVIDENCE",
                classification_reason="Arm phase correlation signal is unavailable.",
                feature_values=feature_vals,
                feature_contributions={},
                missing_evidence=missing_evidence,
                classifier_version=self.classifier_version,
                threshold_version=self.threshold_version
            )

        if -0.3 <= phi_arm <= +0.3:
            missing_evidence.append("unambiguous_arm_phase")
            return StrokeDetectionResult(
                predicted_stroke=StrokeType.UNKNOWN,
                confidence=None,
                predictions={},
                selected_stroke=selected_stroke_input,
                manual_override=False,
                is_inconsistent=False,
                classification_status="INSUFFICIENT_EVIDENCE",
                classification_reason=f"Kinematic arm phase signal is ambiguous ({phi_arm:.2f}).",
                feature_values=feature_vals,
                feature_contributions={},
                missing_evidence=missing_evidence,
                classifier_version=self.classifier_version,
                threshold_version=self.threshold_version
            )

        scores: Dict[StrokeType, float] = {
            StrokeType.FREESTYLE: 0.0,
            StrokeType.BACKSTROKE: 0.0,
            StrokeType.BREASTSTROKE: 0.0,
            StrokeType.BUTTERFLY: 0.0
        }
        contributions: Dict[str, float] = {}

        # Rule evaluation strictly on measured signals (no 0.0 fallbacks)
        if phi_arm < -0.3:
            contributions["arm_phase_alternating"] = +0.4
            
            is_freestyle_roll = (roll_amp is not None and roll_amp > 15.0)
            is_freestyle_wrist = (wrist_range_val is not None and wrist_range_val > 0.12)

            # Alternating arm motion is shared by Freestyle and Backstroke.
            # Without explicit supine orientation, high roll/excursion gives slight edge to Freestyle,
            # but maintains an ambiguous candidate margin so AI Verifier is invoked for validation.
            if is_freestyle_wrist or is_freestyle_roll:
                scores[StrokeType.FREESTYLE] += 0.60
                scores[StrokeType.BACKSTROKE] += 0.40
                contributions["freestyle_roll_amplitude"] = +0.60
            else:
                scores[StrokeType.BACKSTROKE] += 0.60
                scores[StrokeType.FREESTYLE] += 0.40
                contributions["backstroke_roll_amplitude"] = +0.60

        elif phi_arm > +0.3:
            contributions["arm_phase_simultaneous"] = +0.4

            if wrist_range_val is not None and wrist_range_val > 0.08:
                scores[StrokeType.BUTTERFLY] += 0.60
                scores[StrokeType.BREASTSTROKE] += 0.40
                contributions["butterfly_wrist_excursion"] = +0.60
            else:
                scores[StrokeType.BREASTSTROKE] += 0.60
                scores[StrokeType.BUTTERFLY] += 0.40
                contributions["breaststroke_wrist_excursion"] = +0.60

            if leg_sym_val is not None and leg_sym_val > +0.5:
                scores[StrokeType.BREASTSTROKE] += 0.15
                scores[StrokeType.BUTTERFLY] += 0.05
                contributions["leg_symmetry_simultaneous"] = +0.15


        total_score = sum(scores.values())
        if total_score <= 0.0:
            return StrokeDetectionResult(
                predicted_stroke=StrokeType.UNKNOWN,
                confidence=None,
                predictions={},
                selected_stroke=selected_stroke_input,
                manual_override=False,
                is_inconsistent=False,
                classification_status="INSUFFICIENT_EVIDENCE",
                classification_reason="Kinematic heuristic rules scored zero confidence.",
                feature_values=feature_vals,
                feature_contributions={},
                missing_evidence=missing_evidence,
                classifier_version=self.classifier_version,
                threshold_version=self.threshold_version
            )

        predictions: Dict[str, float] = {st.value: round(sc / total_score, 4) for st, sc in scores.items() if sc > 0.0}

        top_stroke_str = max(predictions, key=predictions.get)
        top_confidence = predictions[top_stroke_str]
        predicted_stroke = StrokeType(top_stroke_str)

        evidence_list = [f"Rule contribution: {k} ({v:+.2f})" for k, v in contributions.items()]

        return StrokeDetectionResult(
            predicted_stroke=predicted_stroke,
            confidence=top_confidence,
            predictions=predictions,
            selected_stroke=selected_stroke_input,
            manual_override=False,
            is_inconsistent=False,
            classification_status="ACCEPTED" if top_confidence >= self.confidence_threshold else "MODERATE_CONFIDENCE",
            classification_reason=f"Kinematic rule match ({top_confidence*100:.1f}% decision score) for {predicted_stroke.value}",
            feature_values=feature_vals,
            feature_contributions=contributions,
            missing_evidence=missing_evidence,
            rule_prediction=predicted_stroke,
            confidence_type="UNCALIBRATED_DECISION_SCORE",
            evidence={"rule_evidence": evidence_list},
            classifier_version=self.classifier_version,
            threshold_version=self.threshold_version
        )

