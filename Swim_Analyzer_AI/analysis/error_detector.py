"""
Heuristics-based engine for detecting swimming movement errors.
"""
from typing import List
from models.data_models import AnalysisResult, MovementError, PerformanceReport
from core.logger import setup_logger

logger = setup_logger(__name__)

class ErrorDetector:
    """
    Evaluates biomechanical data across an entire video to detect technique flaws
    and generate a performance report.
    """
    
    def __init__(self):
        # We start with 100 points and deduct based on severity
        self.starting_score = 100.0
        self.severity_deductions = {
            "Low": 2.0,
            "Medium": 5.0,
            "High": 10.0
        }
        
    def generate_report(self, analysis_result: AnalysisResult) -> PerformanceReport:
        """
        Analyzes the result frames and builds a comprehensive report.
        
        Args:
            analysis_result: The completed result containing all frames.
            
        Returns:
            PerformanceReport: The generated report.
        """
        report = PerformanceReport(overall_score=self.starting_score)
        
        try:
            report.errors = self._detect_errors(analysis_result)
            
            # Deduct points
            for error in report.errors:
                deduction = self.severity_deductions.get(error.severity, 0.0)
                report.overall_score -= deduction
                
            # Clamp score between 0 and 100
            report.overall_score = max(0.0, min(100.0, report.overall_score))
            
            # Generate summary feedback
            report.feedback_summary = self._generate_feedback_summary(report.overall_score, len(report.errors))
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            
        return report

    def _detect_errors(self, analysis_result: AnalysisResult) -> List[MovementError]:
        """
        Runs specific heuristics to find flaws in the swimming technique.
        """
        errors = []
        
        # Example Heuristic 1: Dropped Elbow during Pull phase
        # If the elbow angle is too wide (>160 degrees) during the Pull phase, the swimmer
        # isn't catching enough water (straight arm pull).
        dropped_elbow_cooldown = 0
        
        for frame in analysis_result.frames:
            if dropped_elbow_cooldown > 0:
                dropped_elbow_cooldown -= 1
                
            # Only check during the Pull phase
            if frame.stroke_phase == "Pull" and dropped_elbow_cooldown == 0:
                
                # Check right arm
                if frame.angles.right_elbow is not None and frame.angles.right_elbow > 160:
                    errors.append(MovementError(
                        frame_index=frame.frame_index,
                        timestamp_ms=frame.timestamp_ms,
                        error_type="Dropped Elbow (Right)",
                        description="Right arm is too straight during the pull phase, reducing water catch efficiency.",
                        severity="Medium"
                    ))
                    dropped_elbow_cooldown = 30 # Prevent flagging every single frame
                    continue # Wait until cooldown finishes to flag again
                    
                # Check left arm
                if frame.angles.left_elbow is not None and frame.angles.left_elbow > 160:
                    errors.append(MovementError(
                        frame_index=frame.frame_index,
                        timestamp_ms=frame.timestamp_ms,
                        error_type="Dropped Elbow (Left)",
                        description="Left arm is too straight during the pull phase, reducing water catch efficiency.",
                        severity="Medium"
                    ))
                    dropped_elbow_cooldown = 30
                    
        return errors

    def _generate_feedback_summary(self, score: float, error_count: int) -> str:
        """Generates textual feedback based on the final score."""
        if score >= 90:
            return "Excellent technique! Minimal flaws detected. Keep up the great form."
        elif score >= 70:
            return f"Good solid swim, but there is room for improvement. We found {error_count} areas to focus on."
        elif score >= 50:
            return f"Fair technique. We detected {error_count} major technique errors that are costing you efficiency."
        else:
            return "Significant technique adjustments are recommended. Focus on core mechanics before building speed."
