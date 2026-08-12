import cv2
from models.data_models import StrokeType, StrokeDetectionResult
from analysis.pose_detector import PoseDetector
from core.logger import setup_logger

logger = setup_logger(__name__)

class StrokeClassifier:
    """Analyzes a sampled clip across the active swimming portion of a video to determine the stroke."""
    
    def __init__(self):
        self.pose_detector = PoseDetector()
        
    def predict(self, video_path: str, max_frames: int = 120, forced_confidence: float = None) -> StrokeDetectionResult:
        """
        Predict the stroke type using smart sampling across active swimming frames.
        Avoids pre-swim glides, wall pushes, or starting blocks at frame 0.
        """
        logger.info(f"Starting Stroke Type Detection on: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Could not open video for stroke detection.")
            self.pose_detector.close()
            return self._fallback()
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        # Smart start/end frame offset: skip pre-swim dive/push-off glide (first ~20%) and wall finish (last ~15%)
        start_frame = int(total_frames * 0.20) if total_frames > 90 else 0
        end_frame = int(total_frames * 0.85) if total_frames > 90 else total_frames
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Frame stride to sample up to max_frames across active duration
        sample_stride = 1
        usable_duration = max(1, end_frame - start_frame)
        if usable_duration > max_frames:
            sample_stride = max(1, usable_duration // max_frames)

        frames_list = []
        raw_counter = start_frame
        sampled_count = 0

        while cap.isOpened() and sampled_count < max_frames and raw_counter <= end_frame:

            ret, frame = cap.read()
            if not ret or frame is None:
                break
                
            if (raw_counter - start_frame) % sample_stride == 0:
                landmarks, is_valid = self.pose_detector.detect_pose(frame)
                safe_landmarks = None
                if landmarks:
                    safe_landmarks = [
                        type('SimpleLandmark', (), {
                            'x': float(lm.x),
                            'y': float(lm.y),
                            'z': float(getattr(lm, 'z', 0.0)),
                            'visibility': float(getattr(lm, 'visibility', 1.0))
                        })() for lm in landmarks
                    ]

                frame_data = type('SimpleFrame', (), {
                    'frame_index': raw_counter,
                    'is_valid': is_valid,
                    'raw_landmarks': safe_landmarks,
                    'angles': None
                })()
                frames_list.append(frame_data)
                sampled_count += 1

            raw_counter += 1
            
        cap.release()
        self.pose_detector.close()
        
        # PIPELINE LAYER 1: Quality / Visibility Gate
        from analysis.classification.visibility_gate import VisibilityGate
        from analysis.classification.feature_extractor import KinematicFeatureExtractor
        from analysis.classification.stroke_heuristic_classifier import StrokeHeuristicClassifier
        from analysis.classification.ai_stroke_agent import AIStrokeAgent
        from analysis.classification.hybrid_stroke_decision_engine import HybridStrokeDecisionEngine

        vis_gate = VisibilityGate()
        vis_res = vis_gate.evaluate(frames_list)

        # PIPELINE LAYER 2: Existing Rule-Based Primary Python Classifier
        extractor = KinematicFeatureExtractor(min_valid_frames=2, visibility_threshold=0.1)
        feature_set = extractor.extract_features(frames_list)
        rule_classifier = StrokeHeuristicClassifier()
        rule_res = rule_classifier.classify_features(feature_set, selected_stroke_input=StrokeType.AUTO_DETECT)

        # Evaluate decision strength and candidate margin for AI Agent invocation
        preds = rule_res.predictions or {}
        sorted_scores = sorted(preds.values(), reverse=True)
        top_conf = sorted_scores[0] if sorted_scores else 0.0
        second_conf = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        margin = round(top_conf - second_conf, 4)

        ai_res = None
        # PIPELINE LAYER 3: AI Stroke Verification Agent (ONLY WHEN NEEDED)
        if rule_res.predicted_stroke != StrokeType.UNKNOWN and top_conf >= 0.75 and margin >= 0.30:
            logger.info(
                "[STROKE_CLASSIFIER] Primary classifier: Python Kinematic Engine | Prediction: %s | "
                "Decision score: %.2f | AI verification: SKIPPED | Reason: strong unambiguous evidence (margin: %.2f)",
                rule_res.predicted_stroke.value, top_conf, margin
            )
        elif rule_res.predicted_stroke != StrokeType.UNKNOWN and top_conf >= 0.40:
            logger.info(
                "[STROKE_CLASSIFIER] Prediction: %s | Decision score: %.2f | Runner-up margin: %.2f | "
                "[AI_VERIFIER] Invoked - ambiguous Python classification",
                rule_res.predicted_stroke.value, top_conf, margin
            )
            ai_agent = AIStrokeAgent()
            structured_input = ai_agent.build_structured_input(
                kinematic_features={
                    "arm_phase_correlation": feature_set.arm_phase_correlation.raw_value if feature_set.arm_phase_correlation and feature_set.arm_phase_correlation.valid else None,
                    "body_roll_amplitude": feature_set.body_roll_amplitude.raw_value if feature_set.body_roll_amplitude and feature_set.body_roll_amplitude.valid else None,
                    "wrist_vertical_range_ratio": feature_set.wrist_vertical_range_ratio.raw_value if feature_set.wrist_vertical_range_ratio and feature_set.wrist_vertical_range_ratio.valid else None,
                    "leg_kick_symmetry": feature_set.leg_kick_symmetry.raw_value if feature_set.leg_kick_symmetry and feature_set.leg_kick_symmetry.valid else None,
                    "wrist_recovery_height_ratio": feature_set.wrist_recovery_height_ratio.raw_value if feature_set.wrist_recovery_height_ratio and feature_set.wrist_recovery_height_ratio.valid else None
                },
                biomechanics={
                    "body_roll": feature_set.mean_body_roll.raw_value if feature_set.mean_body_roll and feature_set.mean_body_roll.valid else None,
                    "recovery_pattern": feature_set.wrist_recovery_height_ratio.raw_value if feature_set.wrist_recovery_height_ratio and feature_set.wrist_recovery_height_ratio.valid else None
                },
                rule_classifier={
                    "prediction": rule_res.predicted_stroke.value if rule_res.predicted_stroke else None,
                    "decision_score": rule_res.confidence,
                    "evidence": [rule_res.classification_reason] if rule_res.classification_reason else []
                },
                video_quality={
                    "status": "PASS" if vis_res.is_sufficient else "FAIL",
                    "camera_view": None,
                    "visibility_ratio": vis_res.visibility_ratio,
                    "wrist_visibility": vis_res.wrist_visibility,
                    "shoulder_visibility": vis_res.shoulder_visibility,
                    "ankle_visibility": vis_res.ankle_visibility,
                    "gate_reason": vis_res.gate_reason
                }
            )
            ai_res = ai_agent.analyze_structured_input(structured_input, selected_stroke_input=StrokeType.AUTO_DETECT)
        else:
            logger.info(
                "[STROKE_CLASSIFIER] Primary classifier: Python Kinematic Engine | Prediction: %s | "
                "AI verification: SKIPPED | Reason: insufficient or unknown evidence",
                rule_res.predicted_stroke.value if rule_res.predicted_stroke else "UNKNOWN"
            )

        # PIPELINE LAYER 4: Hybrid Decision Engine
        hybrid_engine = HybridStrokeDecisionEngine(rule_weight=0.50, ai_weight=0.50)
        hybrid_decision = hybrid_engine.evaluate_hybrid_decision(
            rule_result=rule_res,
            ai_result=ai_res,
            visibility_result=vis_res,
            selected_stroke_input=StrokeType.AUTO_DETECT
        )

        # PIPELINE LAYER 5: Output Unified Decision Structure
        res = hybrid_decision.raw_detection_result
        res.feature_values["uncertainty"] = hybrid_decision.uncertainty
        res.feature_values["visibility_ratio"] = vis_res.visibility_ratio

        if forced_confidence is not None:
            res.confidence = forced_confidence
            if forced_confidence < 0.40:
                res.classification_status = "MODERATE_CONFIDENCE"

        return res

        
    def _fallback(self) -> StrokeDetectionResult:
        return StrokeDetectionResult(
            predicted_stroke=StrokeType.UNKNOWN,
            confidence=None,
            predictions={},
            selected_stroke=StrokeType.AUTO_DETECT,
            manual_override=False,
            is_inconsistent=False,
            classification_status="INSUFFICIENT_EVIDENCE",
            classification_reason="Could not open video file or read frame landmarks for stroke detection.",
            feature_values={},
            feature_contributions={},
            missing_evidence=["video_read_failure"],
            classifier_version="2.0.0-Hybrid-Engine",
            threshold_version="HYBRID_DECISION_v2.0"
        )
