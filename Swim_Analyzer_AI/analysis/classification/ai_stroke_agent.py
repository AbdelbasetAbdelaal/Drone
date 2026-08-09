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
        """
        valid_frames = [f for f in frames if getattr(f, 'raw_landmarks', None) and len(f.raw_landmarks) > 28]
        if len(valid_frames) < 3:
            return self._build_default_result(selected_stroke_input, "Insufficient valid landmark frames in video clip.")

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

                # Wrist elevation relative to shoulder
                if l_wr and r_wr:
                    avg_sh_y = (l_sh.y + r_sh.y) / 2.0
                    min_wr_y = min(l_wr.y, r_wr.y)
                    wrist_rel_shoulder.append(min_wr_y - avg_sh_y)

                # Chest orientation (supine vs prone)
                # In Backstroke, nose y is higher in frame (smaller Y coordinate in MediaPipe) relative to shoulders/hips
                if nose and l_hip and r_hip:
                    avg_hip_y = (l_hip.y + r_hip.y) / 2.0
                    avg_sh_y = (l_sh.y + r_sh.y) / 2.0
                    # Check if face/nose is above shoulder level (supine float position)
                    if nose.y < avg_sh_y and (avg_sh_y - nose.y) > 0.05:
                        supine_indicators.append(1)
                    else:
                        supine_indicators.append(0)

        # Use elbows as trajectory fallback if wrists are submerged
        y1_series = lw_y if len(lw_y) >= 3 else le_y
        y2_series = rw_y if len(rw_y) >= 3 else re_y

        # Compute Phase Correlation
        arm_phase_corr = self._calc_corr(y1_series, y2_series)
        kick_symmetry = self._calc_corr(la_y, ra_y)
        body_roll_amp = (max(body_rolls) - min(body_rolls)) if len(body_rolls) >= 3 else 15.0
        wrist_range_y = ((max(y1_series) - min(y1_series)) + (max(y2_series) - min(y2_series))) / 2.0 if len(y1_series) >= 3 else 0.15
        wrist_recovery_height = min(wrist_rel_shoulder) if wrist_rel_shoulder else 0.0
        is_supine = (sum(supine_indicators) / max(1, len(supine_indicators))) > 0.6

        # 2. Multi-Feature Weighted Voting Classifier
        scores: Dict[StrokeType, float] = {
            StrokeType.FREESTYLE: 0.05,
            StrokeType.BACKSTROKE: 0.05,
            StrokeType.BREASTSTROKE: 0.05,
            StrokeType.BUTTERFLY: 0.05
        }
        reasons: List[str] = []

        # Feature A: Arm Phase (Alternating vs Simultaneous)
        if arm_phase_corr < -0.15:
            # Alternating arm motion -> Freestyle or Backstroke
            reasons.append(f"Alternating arm rhythm (correlation: {arm_phase_corr:.2f})")
            if is_supine:
                scores[StrokeType.BACKSTROKE] += 0.80
                scores[StrokeType.FREESTYLE] += 0.10
                reasons.append("Supine chest orientation (face-up)")
            elif body_roll_amp > 12.0 or wrist_range_y > 0.08:
                scores[StrokeType.FREESTYLE] += 0.85
                scores[StrokeType.BACKSTROKE] += 0.10
                reasons.append(f"Prone position with active body roll ({body_roll_amp:.1f}°)")
            else:
                scores[StrokeType.FREESTYLE] += 0.60
                scores[StrokeType.BACKSTROKE] += 0.35

        elif arm_phase_corr > +0.15:
            # Simultaneous arm motion -> Breaststroke or Butterfly
            reasons.append(f"Simultaneous arm rhythm (correlation: {arm_phase_corr:+.2f})")
            
            if wrist_range_y > 0.08 or wrist_recovery_height < -0.02:
                scores[StrokeType.BUTTERFLY] += 0.85
                scores[StrokeType.BREASTSTROKE] += 0.10
                reasons.append(f"High vertical arm recovery (range: {wrist_range_y:.2f})")
            else:
                scores[StrokeType.BREASTSTROKE] += 0.85
                scores[StrokeType.BUTTERFLY] += 0.10
                reasons.append("Underwater arm pull & recovery pattern")

            if kick_symmetry > 0.3:
                scores[StrokeType.BREASTSTROKE] += 0.10
                scores[StrokeType.BUTTERFLY] += 0.10
                reasons.append(f"Symmetrical kick motion (symmetry: {kick_symmetry:.2f})")

        else:
            # Ambiguous phase signal -> Default to Freestyle baseline
            scores[StrokeType.FREESTYLE] += 0.60
            scores[StrokeType.BACKSTROKE] += 0.15
            scores[StrokeType.BREASTSTROKE] += 0.15
            scores[StrokeType.BUTTERFLY] += 0.10
            reasons.append("Defaulted candidate to Freestyle baseline")

        # Normalize Scores
        total = sum(scores.values())
        predictions = {st.value: round(sc / total, 4) for st, sc in scores.items()}

        top_stroke_str = max(predictions, key=predictions.get)
        top_confidence = predictions[top_stroke_str]
        predicted_stroke = StrokeType(top_stroke_str)

        explanation = f"AI Agent Analysis: Top candidate {predicted_stroke.value} ({top_confidence*100:.1f}% confidence). Key signals: " + "; ".join(reasons) + "."
        logger.info(explanation)

        return StrokeDetectionResult(
            predicted_stroke=predicted_stroke,
            confidence=top_confidence,
            predictions=predictions,
            selected_stroke=selected_stroke_input,
            manual_override=False,
            is_inconsistent=False,
            classification_status="ACCEPTED" if top_confidence >= self.confidence_threshold else "MODERATE_CONFIDENCE",
            classification_reason=explanation,
            feature_values={
                "arm_phase_correlation": arm_phase_corr,
                "body_roll_amplitude": body_roll_amp,
                "wrist_vertical_range_ratio": wrist_range_y,
                "kick_symmetry": kick_symmetry
            },
            feature_contributions={"ai_agent_ensemble": top_confidence},
            classifier_version=self.version,
            threshold_version="AI_AGENT_v2.0"
        )

    def _calc_corr(self, s1: List[float], s2: List[float]) -> float:
        if len(s1) < 3 or len(s2) < 3 or len(s1) != len(s2):
            return 0.0
        a1, a2 = np.array(s1), np.array(s2)
        v1, v2 = np.std(a1), np.std(a2)
        if v1 < 1e-4 or v2 < 1e-4:
            return 0.0
        r = float(np.corrcoef(a1, a2)[0, 1])
        return 0.0 if math.isnan(r) else r

    def _build_default_result(self, selected_stroke: StrokeType, reason: str) -> StrokeDetectionResult:
        predictions = {
            StrokeType.FREESTYLE.value: 0.40,
            StrokeType.BACKSTROKE.value: 0.20,
            StrokeType.BREASTSTROKE.value: 0.20,
            StrokeType.BUTTERFLY.value: 0.20
        }
        return StrokeDetectionResult(
            predicted_stroke=StrokeType.FREESTYLE,
            confidence=0.40,
            predictions=predictions,
            selected_stroke=selected_stroke,
            manual_override=False,
            is_inconsistent=False,
            classification_status="FALLBACK_DEFAULT",
            classification_reason=f"AI Agent Fallback: {reason}",
            feature_values={},
            feature_contributions={"fallback": 1.0},
            classifier_version=self.version,
            threshold_version="AI_AGENT_v2.0"
        )
