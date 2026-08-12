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

        # Smart frame sampling window: for short/medium clips (<=300 frames), sample entire sequence
        if total_frames <= 300:
            start_frame = 0
            end_frame = total_frames
        else:
            start_frame = int(total_frames * 0.10)
            end_frame = int(total_frames * 0.90)

        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Frame stride to sample up to max_frames across usable duration
        usable_duration = max(1, end_frame - start_frame)
        sample_stride = max(1, usable_duration // max_frames) if usable_duration > max_frames else 1

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
        from analysis.classification.hybrid_stroke_decision_engine import HybridStrokeDecisionEngine

        vis_gate = VisibilityGate()
        vis_res = vis_gate.evaluate(frames_list)

        # PIPELINE LAYER 2: Primary Python Kinematic Classifier (Sole Authority)
        extractor = KinematicFeatureExtractor(min_valid_frames=2, visibility_threshold=0.1)
        feature_set = extractor.extract_features(frames_list)
        rule_classifier = StrokeHeuristicClassifier()
        rule_res = rule_classifier.classify_features(feature_set, selected_stroke_input=StrokeType.AUTO_DETECT)

        # Diagnostic Logging for Execution Traceability
        valid_cnt = getattr(feature_set, 'valid_frames_in_window', 0)
        usable_pct = (valid_cnt / max(1, len(frames_list))) * 100.0
        vis_pct = vis_res.visibility_ratio * 100.0
        conf_str = f"{rule_res.confidence:.2f}" if rule_res.confidence is not None else "0.00"

        logger.info("[STROKE_CLASSIFIER] Classification engine: Python Kinematic Engine")
        logger.info("[STROKE_CLASSIFIER] AI verification: DISABLED (Python-only classification mode)")
        logger.info(
            "[STROKE_CLASSIFIER] Diagnostic Frame Metrics | Total video frames: %d | Sampled: %d | "
            "Valid pose frames: %d (%.1f%%) | Landmark visibility: %.1f%%",
            total_frames, len(frames_list), valid_cnt, usable_pct, vis_pct
        )
        logger.info("[STROKE_CLASSIFIER] Extracted Kinematic Features: %s", rule_res.feature_values)
        logger.info("[STROKE_CLASSIFIER] Candidate Stroke Scores: %s", rule_res.predictions)
        logger.info("[STROKE_CLASSIFIER] Status: %s | Reason: %s", rule_res.classification_status, rule_res.classification_reason)
        logger.info("[STROKE_CLASSIFIER] Prediction: %s", rule_res.predicted_stroke.value)
        logger.info("[STROKE_CLASSIFIER] Confidence: %s", conf_str)

        # PIPELINE LAYER 3: Python-Only Decision Output (AI Agent Bypassed)
        ai_res = None
        hybrid_engine = HybridStrokeDecisionEngine(rule_weight=1.0, ai_weight=0.0)
        hybrid_decision = hybrid_engine.evaluate_hybrid_decision(
            rule_result=rule_res,
            ai_result=ai_res,
            visibility_result=vis_res,
            selected_stroke_input=StrokeType.AUTO_DETECT
        )

        # PIPELINE LAYER 4: Output Unified Decision Structure
        res = hybrid_decision.raw_detection_result
        res.feature_values["uncertainty"] = hybrid_decision.uncertainty
        res.feature_values["visibility_ratio"] = vis_res.visibility_ratio

        if forced_confidence is not None:
            res.confidence = forced_confidence

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
