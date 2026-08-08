# Stroke Classification Status

**Date:** 2026-08-08

## 1. Algorithmic State
The stroke classifier (`HeuristicStrokeClassifier`) processes normalized kinematic time-series data extracted from Mediapipe pose landmarks. 
It analyzes:
* Leg Symmetry (Flutter vs Dolphin/Whip)
* Arm Periodicity
* Body Roll & Body Orientation
* Stroke Rate & Cycle timing

## 2. Safety Rules Enforced
1. **No Silent Freestyle Fallbacks:** If the confidence threshold is not met (or features are highly ambiguous), the classifier returns `UNKNOWN`. The old implementation that defaulted to Freestyle has been securely patched.
2. **Confidence Penalties:** Missing keypoints, poor orientation, or low-quality video inherently degrade the probability scores.
3. **Multi-Stroke Support:** The pipeline is wired to support all four strokes (Freestyle, Breaststroke, Butterfly, Backstroke).

## 3. Scientific Validation Status
**Status:** UNVALIDATED (`1.0.0-unvalidated`)
While technically complete and mathematically deterministic, the stroke classifier lacks rigorous real-world validation against an annotated multi-stroke ground-truth dataset. 
*Do NOT claim clinical correctness until formal verification occurs.*
