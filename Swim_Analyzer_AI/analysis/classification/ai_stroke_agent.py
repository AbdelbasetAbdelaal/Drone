"""
AI Stroke Detection Agent for SwimAnalyzer AI.
Performs multi-feature 3D time-series vector analysis to classify swimming stroke styles
(Freestyle, Backstroke, Breaststroke, Butterfly) with high precision and explainable coach breakdown metrics.
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from models.data_models import StrokeType, StrokeDetectionResult
from core.logger import setup_logger

logger = setup_logger(__name__)

# MediaPipe Pose Landmark Indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
NOSE = 0

@dataclass
class AgentFeatureVector:
    """Holds extracted kinematic indicators for AI stroke agent classification."""
    arm_phase_corr: float        # Cross-correlation of arm movement (-1.0 = alternating, +1.0 = simultaneous)
    body_roll_amp: float         # Longitudinal body roll amplitude in degrees
    wrist_range_y: float         # Vertical excursion of wrist relative to frame/body
    wrist_recovery_height: float # Max height of wrist relative to shoulder (negative = above shoulder)
    kick_symmetry: float         # Ankle movement correlation (+1.0 = symmetrical frog/dolphin, -1.0 = flutter)
    chest_orientation: str       # 'prone' (facing down) or 'supine' (facing up / Backstroke)
    valid_frames: int            # Total valid landmark frames used

class AIStrokeAgent:
    """
    AI Agent that combines spatial-temporal landmark vector analysis with multi-feature weighted voting 
    to determine stroke type with high confidence and explainable coaching reasoning.
    """

    def __init__(self, confidence_threshold: float = 0.40):
        self.confidence_threshold = confidence_threshold
        self.version = "2.0.0-AI-Agent"

    def analyze_sequence(self, frames: List[Any], selected_stroke_input: StrokeType = StrokeType.AUTO_DETECT) -> StrokeDetectionResult:
        """
        Analyzes a sequence of landmark frames and returns an explainable StrokeDetectionResult.
        Missing evidence propagates as None without fabricated default values.
        """
        valid_frames = [f for f in frames if getattr(f, 'raw_landmarks', None) and len(f.raw_landmarks) > 28]
        missing_evidence: List[str] = []

        if len(valid_frames) < 3:
            missing_evidence.append("valid_landmark_frames")
            return self._build_insufficient_evidence_result(selected_stroke_input, "Insufficient valid landmark frames in video clip.", missing_evidence)

        # 1. Extract Biomechanical Trajectories
        lw_y, rw_y = [], []
        le_y, re_y = [], []
        la_y, ra_y = [], []
        body_rolls = []
        wrist_rel_shoulder = []
        supine_indicators = []

        for f in valid_frames:
            lms = f.raw_landmarks
            l_sh, r_sh = lms[LEFT_SHOULDER], lms[RIGHT_SHOULDER]
            l_wr, r_wr = lms[LEFT_WRIST], lms[RIGHT_WRIST]
            l_el, r_el = lms[LEFT_ELBOW], lms[RIGHT_ELBOW]
            l_hip, r_hip = lms[LEFT_HIP], lms[RIGHT_HIP]
            l_ak, r_ak = lms[LEFT_ANKLE], lms[RIGHT_ANKLE]
            nose = lms[NOSE]

            if l_wr and r_wr:
                lw_y.append(l_wr.y)
                rw_y.append(r_wr.y)
            if l_el and r_el:
                le_y.append(l_el.y)
                re_y.append(r_el.y)
            if l_ak and r_ak:
                la_y.append(l_ak.y)
                ra_y.append(r_ak.y)

            # Shoulder roll
            if l_sh and r_sh:
                dx = r_sh.x - l_sh.x
                dy = r_sh.y - l_sh.y
                roll_deg = abs(math.degrees(math.atan2(dy, dx)))
                body_rolls.append(roll_deg)

                if l_wr and r_wr:
                    avg_sh_y = (l_sh.y + r_sh.y) / 2.0
                    min_wr_y = min(l_wr.y, r_wr.y)
                    wrist_rel_shoulder.append(min_wr_y - avg_sh_y)

                if nose and l_hip and r_hip:
                    avg_sh_y = (l_sh.y + r_sh.y) / 2.0
                    if nose.y <= avg_sh_y + 0.05:
                        supine_indicators.append(1)
                    else:
                        supine_indicators.append(0)

        # Compute arm phase correlation (prefer wrist, fallback to elbow)
        wrist_corr = self._calc_corr(lw_y, rw_y)
        elbow_corr = self._calc_corr(le_y, re_y)

        # If elbow correlation indicates strong alternating motion (-1.0 to -0.15) while wrist is submerged, use elbow
        if elbow_corr is not None and elbow_corr < -0.15:
            arm_phase_corr = elbow_corr
        elif wrist_corr is not None:
            arm_phase_corr = wrist_corr
        else:
            arm_phase_corr = elbow_corr

        kick_symmetry = self._calc_corr(la_y, ra_y)
        body_roll_amp = (max(body_rolls) - min(body_rolls)) if len(body_rolls) >= 3 else None
        
        y1_series = lw_y if len(lw_y) >= 3 else le_y
        y2_series = rw_y if len(rw_y) >= 3 else re_y
        wrist_range_y = ((max(y1_series) - min(y1_series)) + (max(y2_series) - min(y2_series))) / 2.0 if len(y1_series) >= 3 else None
        wrist_recovery_height = min(wrist_rel_shoulder) if wrist_rel_shoulder else None
        is_supine = (sum(supine_indicators) / max(1, len(supine_indicators))) > 0.5 if supine_indicators else False

        feature_vals: Dict[str, Any] = {}
        if arm_phase_corr is not None: feature_vals["arm_phase_correlation"] = arm_phase_corr
        else: missing_evidence.append("arm_phase_correlation")

        if body_roll_amp is not None: feature_vals["body_roll_amplitude"] = body_roll_amp
        else: missing_evidence.append("body_roll_amplitude")

        if wrist_range_y is not None: feature_vals["wrist_vertical_range_ratio"] = wrist_range_y
        else: missing_evidence.append("wrist_vertical_range_ratio")

        if kick_symmetry is not None: feature_vals["kick_symmetry"] = kick_symmetry
        else: missing_evidence.append("kick_symmetry")

        if arm_phase_corr is None and body_roll_amp is None:
            return self._build_insufficient_evidence_result(selected_stroke_input, "Missing valid arm phase and body roll landmark data.", missing_evidence)

        # Multi-Feature Weighted Classifier
        scores: Dict[StrokeType, float] = {
            StrokeType.FREESTYLE: 0.05,
            StrokeType.BACKSTROKE: 0.05,
            StrokeType.BREASTSTROKE: 0.05,
            StrokeType.BUTTERFLY: 0.05
        }
        reasons: List[str] = []

        if arm_phase_corr is not None and arm_phase_corr < -0.15:
            reasons.append(f"Alternating arm rhythm (correlation: {arm_phase_corr:.2f})")
            roll_amp_check = body_roll_amp if body_roll_amp is not None else 0.0
            wrist_range_check = wrist_range_y if wrist_range_y is not None else 0.0
            if is_supine:
                scores[StrokeType.BACKSTROKE] += 0.80
                scores[StrokeType.FREESTYLE] += 0.10
                reasons.append("Supine chest orientation (face-up)")
            elif roll_amp_check > 12.0 or wrist_range_check > 0.08:
                scores[StrokeType.FREESTYLE] += 0.85
                scores[StrokeType.BACKSTROKE] += 0.10
                reasons.append(f"Prone position with active body roll ({roll_amp_check:.1f}°)")
            else:
                scores[StrokeType.FREESTYLE] += 0.60
                scores[StrokeType.BACKSTROKE] += 0.35

        elif arm_phase_corr is not None and arm_phase_corr > +0.15:
            reasons.append(f"Simultaneous arm rhythm (correlation: {arm_phase_corr:+.2f})")
            wrist_range_check = wrist_range_y if wrist_range_y is not None else 0.0
            wrist_rec_check = wrist_recovery_height if wrist_recovery_height is not None else 0.0
            
            if wrist_range_check > 0.08 or wrist_rec_check < -0.02:
                scores[StrokeType.BUTTERFLY] += 0.85
                scores[StrokeType.BREASTSTROKE] += 0.10
                reasons.append("High vertical arm recovery")
            else:
                scores[StrokeType.BREASTSTROKE] += 0.85
                scores[StrokeType.BUTTERFLY] += 0.10
                reasons.append("Underwater arm pull & recovery pattern")

            if kick_symmetry is not None and kick_symmetry > 0.3:
                scores[StrokeType.BREASTSTROKE] += 0.10
                scores[StrokeType.BUTTERFLY] += 0.10
                reasons.append(f"Symmetrical kick motion (symmetry: {kick_symmetry:.2f})")

        else:
            scores[StrokeType.FREESTYLE] += 0.40
            scores[StrokeType.BACKSTROKE] += 0.20
            scores[StrokeType.BREASTSTROKE] += 0.20
            scores[StrokeType.BUTTERFLY] += 0.20
            reasons.append("Ambiguous kinematic phase signal")

        total = sum(scores.values())
        predictions = {st.value: round(sc / total, 4) for st, sc in scores.items()}

        top_stroke_str = max(predictions, key=predictions.get)
        top_confidence = predictions[top_stroke_str]
        predicted_stroke = StrokeType(top_stroke_str)

        explanation = f"AI Agent Analysis: Top candidate {predicted_stroke.value} ({top_confidence*100:.1f}% confidence). Key signals: " + "; ".join(reasons) + "."

        return StrokeDetectionResult(
            predicted_stroke=predicted_stroke,
            confidence=top_confidence,
            predictions=predictions,
            selected_stroke=selected_stroke_input,
            manual_override=False,
            is_inconsistent=False,
            classification_status="ACCEPTED" if top_confidence >= self.confidence_threshold else "MODERATE_CONFIDENCE",
            classification_reason=explanation,
            feature_values=feature_vals,
            feature_contributions={"ai_agent_ensemble": top_confidence},
            missing_evidence=missing_evidence,
            ai_prediction=predicted_stroke,
            classifier_version=self.version,
            threshold_version="AI_AGENT_v2.0"
        )

    def _calc_corr(self, s1: List[float], s2: List[float]) -> Optional[float]:
        if len(s1) < 3 or len(s2) < 3 or len(s1) != len(s2):
            return None
        a1, a2 = np.array(s1), np.array(s2)
        v1, v2 = np.std(a1), np.std(a2)
        if v1 < 1e-4 or v2 < 1e-4:
            return None
        r = float(np.corrcoef(a1, a2)[0, 1])
        return None if math.isnan(r) else r

    def _build_insufficient_evidence_result(self, selected_stroke: StrokeType, reason: str, missing: List[str]) -> StrokeDetectionResult:
        return StrokeDetectionResult(
            predicted_stroke=StrokeType.UNKNOWN,
            confidence=None,
            predictions={},
            selected_stroke=selected_stroke,
            manual_override=False,
            is_inconsistent=False,
            classification_status="INSUFFICIENT_EVIDENCE",
            classification_reason=f"AI Agent: {reason}",
            feature_values={},
            feature_contributions={},
            missing_evidence=missing,
            ai_prediction=None,
            classifier_version=self.version,
            threshold_version="AI_AGENT_v2.0"
        )
