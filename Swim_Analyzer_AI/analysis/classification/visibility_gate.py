"""
Visibility and Quality Gate for Stroke Classification.
Evaluates pose landmark visibility and completeness before passing to classification engines.
"""
from dataclasses import dataclass
from typing import List, Any, Dict

@dataclass
class VisibilityGateResult:
    is_sufficient: bool
    total_frames: int
    valid_frames: int
    visibility_ratio: float
    wrist_visibility: float
    shoulder_visibility: float
    gate_reason: str

class VisibilityGate:
    """Quality & Visibility Gate for Pose Landmark Sequences."""

    def __init__(self, min_visibility_threshold: float = 0.15, min_valid_ratio: float = 0.05):
        self.min_visibility_threshold = min_visibility_threshold
        self.min_valid_ratio = min_valid_ratio

    def evaluate(self, frames: List[Any]) -> VisibilityGateResult:
        if not frames:
            return VisibilityGateResult(
                is_sufficient=False, total_frames=0, valid_frames=0,
                visibility_ratio=0.0, wrist_visibility=0.0, shoulder_visibility=0.0,
                gate_reason="No frames provided to visibility gate."
            )

        total_frames = len(frames)
        valid_frames = [f for f in frames if getattr(f, 'raw_landmarks', None) and len(f.raw_landmarks) > 28]
        valid_count = len(valid_frames)
        vis_ratio = valid_count / total_frames if total_frames > 0 else 0.0

        if valid_count == 0:
            return VisibilityGateResult(
                is_sufficient=False, total_frames=total_frames, valid_frames=0,
                visibility_ratio=0.0, wrist_visibility=0.0, shoulder_visibility=0.0,
                gate_reason="Zero frames contain 3D pose landmarks."
            )

        # Average wrist and shoulder visibilities
        wrist_vis = []
        shoulder_vis = []

        for f in valid_frames:
            lms = f.raw_landmarks
            l_wr, r_wr = lms[15], lms[16]
            l_sh, r_sh = lms[11], lms[12]
            if l_wr and r_wr:
                wrist_vis.append((getattr(l_wr, 'visibility', 1.0) + getattr(r_wr, 'visibility', 1.0)) / 2.0)
            if l_sh and r_sh:
                shoulder_vis.append((getattr(l_sh, 'visibility', 1.0) + getattr(r_sh, 'visibility', 1.0)) / 2.0)

        avg_wrist_vis = sum(wrist_vis) / len(wrist_vis) if wrist_vis else 0.5
        avg_sh_vis = sum(shoulder_vis) / len(shoulder_vis) if shoulder_vis else 0.5

        is_sufficient = vis_ratio >= self.min_valid_ratio
        reason = f"Visibility ratio: {vis_ratio*100:.1f}%, Wrist Vis: {avg_wrist_vis:.2f}, Shoulder Vis: {avg_sh_vis:.2f}"

        return VisibilityGateResult(
            is_sufficient=is_sufficient,
            total_frames=total_frames,
            valid_frames=valid_count,
            visibility_ratio=vis_ratio,
            wrist_visibility=avg_wrist_vis,
            shoulder_visibility=avg_sh_vis,
            gate_reason=reason
        )
