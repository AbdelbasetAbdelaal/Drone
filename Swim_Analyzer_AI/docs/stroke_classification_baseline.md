# Swimming Stroke Classification Baseline Specification & Technical Manual

**Platform**: SwimAnalyzer AI  
**Author**: Lead Computer Vision Architect & Sports Biomechanics Engineer  
**Date**: August 8, 2026  
**Status**: BASELINE IMPLEMENTED — NOT SCIENTIFICALLY VALIDATED  

---

## 📌 Executive Summary

This document specifies the implementation of **Stage 1 & Stage 2** of the Stroke Classification Layer for SwimAnalyzer AI.

It introduces a deterministic, explainable **Kinematic Feature Extractor** and **Stroke Heuristic Classifier**. All decision rules and probability parameters are explicitly tagged as `UNVALIDATED_HEURISTIC_v1.0`.

> [!CAUTION]
> **SCIENTIFIC DISCLAIMER**: The thresholds and decision rules defined herein are initial kinematic heuristics designed for software pipeline integration. They have **NOT** been scientifically validated on a multi-stroke empirical dataset. The system must not claim production ML classification accuracy until a ground-truth dataset is annotated and evaluated via confusion matrix protocol.

---

## 1. Implemented Features & Formulations

### 1.1 `arm_phase_correlation` ($\phi_{\text{arm}}$)
- **Formula**:
  $$\phi_{\text{arm}} = \text{corr}\left(y_{\text{left\_wrist}}(t), y_{\text{right\_wrist}}(t)\right) = \frac{\sum (y_L(t) - \bar{y}_L)(y_R(t) - \bar{y}_R)}{\sqrt{\sum (y_L(t) - \bar{y}_L)^2 \sum (y_R(t) - \bar{y}_R)^2}}$$
- **Utility**: Distinguishes alternating stroke styles (Freestyle, Backstroke where $\phi_{\text{arm}} < -0.3$) from simultaneous stroke styles (Breaststroke, Butterfly where $\phi_{\text{arm}} > +0.3$).
- **Missing Data Condition**: Returns `valid = False` with reason `INSUFFICIENT_VISIBILITY_SERIES` if wrist landmarks fall below `visibility_threshold = 0.5`.

### 1.2 `mean_body_roll` ($\theta_{\text{roll\_mean}}$)
- **Formula**:
  $$\theta_{\text{roll\_mean}} = \frac{1}{N} \sum_{t=1}^{N} \text{BodyRoll}(t)$$
- **Utility**: Distinguishes supine orientation (Backstroke $\approx 180^\circ$ or inverted torso normal) from prone orientation (Freestyle, Breaststroke, Butterfly).

### 1.3 `body_roll_amplitude` ($\theta_{\text{roll\_range}}$)
- **Formula**:
  $$\theta_{\text{roll\_range}} = \max_{t}(\text{BodyRoll}(t)) - \min_{t}(\text{BodyRoll}(t))$$
- **Utility**: Distinguishes high body roll styles (Freestyle $> 15.0^\circ$) from flat body position styles (Breaststroke, Butterfly).

### 1.4 `wrist_vertical_range_ratio` ($\Delta Y_{\text{wrist}}$)
- **Formula**:
  $$\Delta Y_{\text{wrist}} = \frac{(\max y_{L} - \min y_{L}) + (\max y_{R} - \min y_{R})}{2}$$
- **Utility**: Distinguishes high vertical recovery excursion (Butterfly $> 0.25$) from underwater recovery sweep (Breaststroke $< 0.25$).

### 1.5 `leg_kick_symmetry` ($\text{Sym}_{\text{leg}}$)
- **Formula**:
  $$\text{Sym}_{\text{leg}} = \text{corr}\left(y_{\text{left\_ankle}}(t), y_{\text{right\_ankle}}(t)\right)$$
- **Utility**: Identifies simultaneous leg movement in Breaststroke whip kicks and Butterfly dolphin kicks ($\text{Sym}_{\text{leg}} > +0.5$).

### 1.6 `wrist_recovery_height_ratio` ($r_{\text{arm\_LR}}$)
- **Formula**:
  $$r_{\text{arm\_LR}} = \left| \min y_{L} - \min y_{R} \right|$$
- **Utility**: Assesses bilateral recovery height parity.

---

## 2. Unvalidated Heuristic Decision Thresholds (`UNVALIDATED_HEURISTIC_v1.0`)

| Parameter / Feature | Threshold | Rule / Logic | Status Tag |
|---|---|---|---|
| **Arm Phase Correlation** ($\phi_{\text{arm}}$) | $< -0.3$ | Classify as Alternating (Freestyle or Backstroke candidate) | `UNVALIDATED_HEURISTIC` |
| **Arm Phase Correlation** ($\phi_{\text{arm}}$) | $> +0.3$ | Classify as Simultaneous (Breaststroke or Butterfly candidate) | `UNVALIDATED_HEURISTIC` |
| **Wrist Vertical Excursion** ($\Delta Y_{\text{wrist}}$) | $> 0.12$ | Distinguishes Freestyle from Backstroke in alternating mode | `UNVALIDATED_HEURISTIC` |
| **Wrist Vertical Excursion** ($\Delta Y_{\text{wrist}}$) | $> 0.25$ | Distinguishes Butterfly from Breaststroke in simultaneous mode | `UNVALIDATED_HEURISTIC` |
| **Body Roll Amplitude** ($\theta_{\text{roll\_range}}$) | $> 15.0^\circ$ | Distinguishes Freestyle from Backstroke | `UNVALIDATED_HEURISTIC` |
| **Leg Kick Symmetry** ($\text{Sym}_{\text{leg}}$) | $> +0.50$ | Adds confidence bonus for Breaststroke / Butterfly | `UNVALIDATED_HEURISTIC` |
| **Safety Confidence Gate** ($\tau_{\text{conf}}$) | $\ge 0.75$ | Accepts classification (`ACCEPTED`); otherwise `INSUFFICIENT_CONFIDENCE` $\rightarrow$ `UNKNOWN` | `UNVALIDATED_HEURISTIC` |

---

## 3. Confidence Safety & Unknown Handling

1. **Safety Gate Threshold**:
   - `confidence >= 0.75`: `classification_status = "ACCEPTED"`, `predicted_stroke` assigned to highest probability stroke.
   - `confidence < 0.75`: `classification_status = "INSUFFICIENT_CONFIDENCE"`, `predicted_stroke = StrokeType.UNKNOWN`.
2. **No Silent Freestyle Fallback**:
   - If feature data is missing, incomplete, or ambiguous ($\phi_{\text{arm}} \in [-0.3, +0.3]$), `predicted_stroke` is set to `StrokeType.UNKNOWN` with `confidence = 0.0`.
   - The system **NEVER** silently defaults to Freestyle.

---

## 4. Known Limitations & Real-World Dataset Requirements

### Limitations
- **Camera View Angle**: Single side-view cameras may experience landmark occlusion on the far-side arm.
- **Short Video Clips**: Windows with $< 10$ valid frames return `valid = False` for all features.
- **Swimming Drills & Transitions**: Drills (e.g. single-arm drills) or flip turns generate ambiguous phase signals.

### Required Dataset for Validation
To transition from `UNVALIDATED_HEURISTIC_v1.0` to a scientifically validated production classifier, the following empirical dataset must be collected:
- **Sample Size**: Minimum 120 video clips (30 per stroke style).
- **Inter-Rater Agreement**: Ground-truth stroke labels verified by 2 certified sports biomechanists.
- **Proposed Evaluation Protocol**: Confusion matrix, per-stroke Precision, Recall, F1-Score, and Cohen's Kappa ($\kappa$).

---

## 5. Final Implementation Declaration

```
==================================================
BASELINE IMPLEMENTED — NOT SCIENTIFICALLY VALIDATED
==================================================
```
