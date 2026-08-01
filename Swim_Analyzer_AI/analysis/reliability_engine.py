from typing import List, Dict
from models.data_models import AnalysisResult, ReliabilityResult
from core.logger import setup_logger

logger = setup_logger(__name__)

class ReliabilityEngine:
    """
    Evaluates the Analysis Confidence (how well the AI tracked the pose) 
    and Analysis Reliability (how trustworthy the biomechanics report is).
    """
    
    @staticmethod
    def evaluate(analysis: AnalysisResult) -> ReliabilityResult:
        result = ReliabilityResult()
        
        try:
            # -----------------------------------------------------
            # 1. Calculate Analysis Confidence
            # -----------------------------------------------------
            total_frames = len(analysis.frames)
            if total_frames == 0:
                result.analysis_confidence_score = 0.0
                result.analysis_confidence_level = "Low"
                result.analysis_reliability_score = 0.0
                result.analysis_reliability_level = "Low"
                result.reasons.append("No frames to analyze.")
                return result
                
            valid_frames = sum(1 for f in analysis.frames if f.is_valid)
            frame_coverage_ratio = valid_frames / total_frames
            
            # Use phase_confidence as a proxy for tracking stability
            phase_confidences = [f.phase_confidence for f in analysis.frames if f.is_valid]
            avg_phase_confidence = sum(phase_confidences) / len(phase_confidences) if phase_confidences else 0.0
            
            confidence_score = (frame_coverage_ratio * 0.7 + avg_phase_confidence * 0.3) * 100.0
            result.analysis_confidence_score = min(100.0, max(0.0, confidence_score))
            
            if result.analysis_confidence_score >= 80:
                result.analysis_confidence_level = "High"
            elif result.analysis_confidence_score >= 50:
                result.analysis_confidence_level = "Medium"
            else:
                result.analysis_confidence_level = "Low"
                
            # -----------------------------------------------------
            # 2. Calculate Analysis Reliability
            # -----------------------------------------------------
            reliability_score = 100.0
            
            # Factor A: Completed Cycles
            cycles = analysis.stroke_statistics.completed_cycles if analysis.stroke_statistics else 0
            if cycles == 0:
                reliability_score -= 60.0
                result.reasons.append("Zero complete stroke cycles detected. Rate and length cannot be measured.")
            elif cycles < 3:
                reliability_score -= 20.0
                result.reasons.append("Very few stroke cycles detected. Metrics may be heavily estimated.")
                
            # Factor B: Low Confidence Penalizes Reliability
            if result.analysis_confidence_level == "Low":
                reliability_score -= 30.0
                result.reasons.append("Low tracking confidence degrades biomechanical reliability.")
            elif result.analysis_confidence_level == "Medium":
                reliability_score -= 10.0
                
            # Factor C: Extracted Metrics Validity
            if analysis.report:
                if not analysis.report.stroke_rate.valid:
                    reliability_score -= 15.0
                if not analysis.report.stroke_length.valid:
                    reliability_score -= 15.0
                    
            result.analysis_reliability_score = min(100.0, max(0.0, reliability_score))
            
            if result.analysis_reliability_score >= 70:
                result.analysis_reliability_level = "High"
            elif result.analysis_reliability_score >= 40:
                result.analysis_reliability_level = "Medium"
            else:
                result.analysis_reliability_level = "Low"
                
        except Exception as e:
            logger.error(f"Error in ReliabilityEngine: {e}")
            result.analysis_reliability_score = 0.0
            result.analysis_reliability_level = "Low"
            result.reasons.append(f"Engine failure: {e}")
            
        return result
