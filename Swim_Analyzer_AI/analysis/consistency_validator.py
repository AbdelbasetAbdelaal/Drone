"""
Validates the internal consistency and scientific trustworthiness of the final analysis.
Ensures that no contradictory metrics or feedback are presented to the user.
"""
from typing import List, Dict, Any
from core.logger import setup_logger
from models.data_models import AnalysisResult, ConsistencyReport

logger = setup_logger(__name__)

class AnalysisConsistencyValidator:
    """
    Final stage verification module.
    Scales scores and flags contradictory or unreliable data.
    """
    
    @staticmethod
    def validate(result: AnalysisResult) -> ConsistencyReport:
        report = ConsistencyReport()
        report.validation_status = "Passed"
        report.scientific_confidence = "High"
        
        if not result.report:
            report.validation_status = "Critical"
            report.warnings.append("Analysis produced no performance report.")
            report.failed_rules.append("Rule_Missing_Report")
            return report
            
        # Initial score is the raw score from the ScoringEngine
        raw_score = result.report.overall_score
        
        # Rule 3: Critical Video Quality
        if result.vqa_result and result.vqa_result.quality_class == "Critical":
            report.validation_status = "Critical"
            report.scientific_confidence = "Inconclusive"
            report.warnings.append("Video Quality is Critical. Analysis aborted.")
            report.failed_rules.append("Rule_3_Critical_VQA")
            # If critical, we should essentially zero out the score and return immediately.
            report.overall_score = 0.0
            return report
        else:
            report.passed_rules.append("Rule_3_Critical_VQA")
            
        # Extract necessary metrics
        avg_phase_conf = 1.0
        if result.stroke_statistics:
            avg_phase_conf = result.stroke_statistics.average_phase_confidence
            
        reliability_score = 100.0
        if result.reliability:
            reliability_score = result.reliability.analysis_reliability_score
            
        vqa_score = 100.0
        is_poor_quality = False
        if result.vqa_result:
            vqa_score = result.vqa_result.overall_score
            if result.vqa_result.quality_class == "Poor":
                is_poor_quality = True
                
        # Rule 2: Poor Video Quality -> Max Reliability is Medium
        if is_poor_quality:
            if result.reliability and result.reliability.analysis_reliability_score > 66.0:
                result.reliability.analysis_reliability_score = min(result.reliability.analysis_reliability_score, 66.0)
                result.reliability.analysis_reliability_level = "Medium"
                reliability_score = result.reliability.analysis_reliability_score
                
            report.warnings.append("Video quality limits measurement accuracy.")
            report.failed_rules.append("Rule_2_Poor_VQA_Reliability")
            report.scientific_confidence = "Medium"
            
            if report.validation_status == "Passed":
                report.validation_status = "Warning"
        else:
            report.passed_rules.append("Rule_2_Poor_VQA_Reliability")
            
        # Rule 1: Average Phase Confidence < 0.50 -> Score capped at 75
        if avg_phase_conf < 0.50:
            if raw_score > 75.0:
                raw_score = 75.0
            report.warnings.append("Low phase confidence detected.")
            report.failed_rules.append("Rule_1_Low_Phase_Confidence")
            report.scientific_confidence = "Low"
            
            if report.validation_status == "Passed":
                report.validation_status = "Warning"
        else:
            report.passed_rules.append("Rule_1_Low_Phase_Confidence")
            
        # Rule 4: Insufficient Stroke Cycles
        cycles = 0
        if result.stroke_statistics:
            cycles = result.stroke_statistics.completed_cycles
            
        if cycles < 2:
            if result.report:
                result.report.stroke_rate.is_insufficient_data = True
                result.report.stroke_length.is_insufficient_data = True
                result.report.stroke_symmetry.is_insufficient_data = True
                result.report.kick_frequency.is_insufficient_data = True
                
            report.warnings.append("Stroke cycle count is insufficient.")
            report.failed_rules.append("Rule_4_Insufficient_Cycles")
            
            if report.scientific_confidence == "High":
                report.scientific_confidence = "Medium"
                
            if report.validation_status == "Passed":
                report.validation_status = "Warning"
        else:
            report.passed_rules.append("Rule_4_Insufficient_Cycles")
            
        # Rule 6: Estimated Joint Angles
        estimated_count = 0
        total_angles_checked = 0
        
        # Check a sample of frames (or all) for estimated angles
        # To avoid massive loops, we can check the validity flags in the frames
        valid_frames = sum(1 for f in result.frames if f.is_valid)
        invalid_frames = len(result.frames) - valid_frames
        
        if len(result.frames) > 0 and (invalid_frames / len(result.frames)) > 0.25:
            report.warnings.append("Several joint angles were estimated due to poor visibility.")
            report.failed_rules.append("Rule_6_Estimated_Angles")
            
            if result.reliability:
                result.reliability.analysis_reliability_score *= 0.8 # Drop by 20%
                reliability_score = result.reliability.analysis_reliability_score
                if result.reliability.analysis_reliability_score < 33.0:
                    result.reliability.analysis_reliability_level = "Low"
                    
            if report.scientific_confidence != "Low":
                report.scientific_confidence = "Medium"
            if report.validation_status == "Passed":
                report.validation_status = "Warning"
        else:
            report.passed_rules.append("Rule_6_Estimated_Angles")
            
        # Rule 7: Pose Detection Unstable -> Lower Biomechanics Confidence
        if result.reliability and result.reliability.analysis_confidence_score < 50.0:
            report.warnings.append("Pose detection is unstable. Biomechanics results should be interpreted cautiously.")
            report.failed_rules.append("Rule_7_Unstable_Pose")
            report.scientific_confidence = "Low"
            if report.validation_status == "Passed":
                report.validation_status = "Warning"
        else:
            report.passed_rules.append("Rule_7_Unstable_Pose")
            
        # Rule 5: Low Reliability -> Inconclusive Recommendations
        if result.reliability and result.reliability.analysis_reliability_score < 40.0:
            if result.report:
                result.report.feedback_summary = "Inconclusive due to insufficient confidence."
                result.report.errors = [] # Clear specific actionable errors since they can't be trusted
            report.warnings.append("Analysis is too unreliable to provide coaching recommendations.")
            report.failed_rules.append("Rule_5_Low_Reliability")
            report.scientific_confidence = "Low"
            if report.validation_status == "Passed":
                report.validation_status = "Warning"
        else:
            report.passed_rules.append("Rule_5_Low_Reliability")
            
        # Rule 8: Performance Score Decoupling
        # Performance score reflects movement mechanics strictly.
        # Video quality, phase confidence, and reliability govern Scientific Confidence level, not technique.
        report.overall_score = raw_score if cycles > 0 else 0.0
        
        # Sync the final score to the report so UI can pick it up
        if result.report:
            result.report.overall_score = report.overall_score
            
        report.passed_rules.append("Rule_8_Score_Scaled")
        
        logger.info(f"Consistency Validation complete. Status: {report.validation_status}. Scientific Confidence: {report.scientific_confidence}")
        
        return report
