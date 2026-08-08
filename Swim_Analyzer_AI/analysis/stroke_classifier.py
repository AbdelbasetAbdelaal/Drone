import cv2
from models.data_models import StrokeType, StrokeDetectionResult
from analysis.pose_detector import PoseDetector
from core.logger import setup_logger
from core.config import config

logger = setup_logger(__name__)

class StrokeClassifier:
    """Analyzes a short clip to determine the swimming stroke."""
    
    def __init__(self):
        self.pose_detector = PoseDetector()
        
    def predict(self, video_path: str, max_frames: int = 60, forced_confidence: float = None) -> StrokeDetectionResult:
        """
        Predict the stroke type using a limited frame sample.
        Forced confidence is a backdoor for testing ambiguous detection flows.
        """
        logger.info(f"Starting Stroke Type Detection on: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Could not open video for stroke detection.")
            self.pose_detector.close()
            return self._fallback()
            
        frame_idx = 0
        
        # We will collect alternating heuristics.
        # But for this simulation, if we see a valid person, we'll just predict Freestyle with high confidence.
        # This will be replaced with real heuristics later (e.g., alternating vs simultaneous wrist Y trajectories).
        
        # Collect detected frames with landmarks
        frames_list = []
        frame_idx = 0
        
        while cap.isOpened() and frame_idx < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
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
                'frame_index': frame_idx,
                'is_valid': is_valid,
                'raw_landmarks': safe_landmarks,
                'angles': None
            })()
            frames_list.append(frame_data)
            frame_idx += 1
            
        cap.release()
        self.pose_detector.close()
        
        from analysis.classification.feature_extractor import KinematicFeatureExtractor
        from analysis.classification.stroke_heuristic_classifier import StrokeHeuristicClassifier

        extractor = KinematicFeatureExtractor(min_valid_frames=10)
        feature_set = extractor.extract_features(frames_list)

        classifier = StrokeHeuristicClassifier()
        res = classifier.classify_features(feature_set, selected_stroke_input=StrokeType.AUTO_DETECT)

        if forced_confidence is not None:
            res.confidence = forced_confidence
            if forced_confidence < 0.75:
                res.classification_status = "INSUFFICIENT_CONFIDENCE"
                res.predicted_stroke = StrokeType.UNKNOWN

        return res
        
    def _fallback(self) -> StrokeDetectionResult:
        from analysis.classification.stroke_heuristic_classifier import CLASSIFIER_VERSION, THRESHOLD_VERSION
        return StrokeDetectionResult(
            predicted_stroke=StrokeType.UNKNOWN,
            confidence=0.0,
            predictions={
                StrokeType.FREESTYLE.value: 0.25,
                StrokeType.BACKSTROKE.value: 0.25,
                StrokeType.BREASTSTROKE.value: 0.25,
                StrokeType.BUTTERFLY.value: 0.25
            },
            selected_stroke=StrokeType.AUTO_DETECT,
            manual_override=False,
            is_inconsistent=False,
            classification_status="UNKNOWN",
            classification_reason="No person detected during stroke classification.",
            feature_values={},
            feature_contributions={"no_landmarks": 1.0},
            classifier_version=CLASSIFIER_VERSION,
            threshold_version=THRESHOLD_VERSION
        )
