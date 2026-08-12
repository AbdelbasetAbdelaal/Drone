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

        # Smart start frame offset: if video is longer than 60 frames, skip first ~10% (pre-swim dive/glide)
        start_frame = int(total_frames * 0.10) if total_frames > 90 else 0
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Frame stride to sample up to max_frames across active duration
        sample_stride = 1
        usable_duration = max(1, total_frames - start_frame)
        if usable_duration > max_frames:
            sample_stride = max(1, usable_duration // max_frames)

        frames_list = []
        raw_counter = start_frame
        sampled_count = 0

        while cap.isOpened() and sampled_count < max_frames:
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

        # PIPELINE LAYER 2: Existing Rule-Based Classifier
        extractor = KinematicFeatureExtractor(min_valid_frames=2, visibility_threshold=0.1)
        feature_set = extractor.extract_features(frames_list)
        rule_classifier = StrokeHeuristicClassifier()
        rule_res = rule_classifier.classify_features(feature_set, selected_stroke_input=StrokeType.AUTO_DETECT)

        # PIPELINE LAYER 3: AI Stroke Classifier Agent
        ai_agent = AIStrokeAgent()
        ai_res = ai_agent.analyze_sequence(frames_list, selected_stroke_input=StrokeType.AUTO_DETECT)

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
