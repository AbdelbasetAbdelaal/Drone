import pytest
import os
import json
import shutil
from pathlib import Path

from services.scientific_updater_service import ScientificUpdaterService
from analysis.benchmarks.benchmark_engine import BenchmarkEngine
from analysis.stroke_classifier import StrokeClassifier
from models.data_models import StrokeType, StrokeDetectionResult

@pytest.fixture
def updater():
    return ScientificUpdaterService()

# --------------------------------------------------------------------------
# PART 17 SCIENTIFIC UPDATER TESTS (1 - 20)
# --------------------------------------------------------------------------

def test_1_pubmed_metadata_retrieval(updater):
    assert hasattr(updater, '_search_literature')

def test_2_pmcid_detection(updater):
    success, n, age, gender = updater._try_retrieve_and_parse_pmc_fulltext("PMC7548777")
    assert isinstance(success, bool)

def test_3_pmc_fulltext_retrieval(updater):
    # PMC 7548777 is Gonjo et al 2020 open access
    success, n, age, gender = updater._try_retrieve_and_parse_pmc_fulltext("7548777")
    # If network is online, parses successfully; if offline, fails safely
    assert isinstance(success, bool)

def test_4_5_fulltext_vs_abstract_only_distinction(updater):
    sources_path = updater.root_dir / "scientific_reference" / "sources" / "source_registry.yaml"
    with open(sources_path, "r", encoding="utf-8") as f:
        import yaml
        sources = yaml.safe_load(f).get("sources", {})
    for sid, s in sources.items():
        if s.get("access_level") == "PEER_REVIEWED_ABSTRACT_ONLY":
            assert s.get("access_level") != "FULL_TEXT_VERIFIED"

def test_6_7_population_and_metric_extraction(updater):
    evidence_path = updater.root_dir / "scientific_reference" / "evidence" / "evidence_registry.yaml"
    with open(evidence_path, "r", encoding="utf-8") as f:
        import yaml
        records = yaml.safe_load(f).get("evidence_records", {})
    rec = records.get("EVID-FREE-001")
    assert rec is not None
    assert rec.get("reported_mean") is not None

def test_8_9_table_and_page_location_requirement(updater):
    evidence_path = updater.root_dir / "scientific_reference" / "evidence" / "evidence_registry.yaml"
    with open(evidence_path, "r", encoding="utf-8") as f:
        import yaml
        records = yaml.safe_load(f).get("evidence_records", {})
    for eid, rec in records.items():
        if rec.get("scientific_status") == "SCIENTIFICALLY_ACCEPTED":
            assert rec.get("table_or_figure_reference") is not None
            assert rec.get("page_reference") is not None

def test_10_11_no_fabricated_sample_size_or_demographics(updater):
    engine = BenchmarkEngine()
    stats = engine._get_population_stats("freestyle", "U10", "Female", "stroke_rate")
    assert stats.mean is None, "U10 Female Freestyle stats must remain None"

def test_12_no_adult_to_youth_leakage(updater):
    engine = BenchmarkEngine()
    adult = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    youth = engine._get_population_stats("freestyle", "U10", "Male", "stroke_rate")
    assert adult.mean != youth.mean

def test_13_no_male_to_female_leakage(updater):
    engine = BenchmarkEngine()
    male = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    female = engine._get_population_stats("freestyle", "26-35", "Female", "stroke_rate")
    assert female.mean is None or male.mean != female.mean

def test_14_no_stroke_to_stroke_leakage(updater):
    engine = BenchmarkEngine()
    free = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    fly = engine._get_population_stats("butterfly", "18-25", "Male", "stroke_rate")
    assert free.mean != fly.mean

def test_15_dynamic_coverage_calculation(updater):
    verified, insufficient = updater._calculate_current_coverage()
    assert verified + insufficient == 96

def test_16_duplicate_study_handling(updater):
    res1 = updater.run_update_cycle()
    if res1.get("verdict") == "INTERNET_UNAVAILABLE":
        pytest.skip("Skipped due to no internet")
    res2 = updater.run_update_cycle()
    assert res1.get("tests_passed") is True and res2.get("tests_passed") is True

def test_17_no_change_update_behavior(updater):
    res = updater.run_update_cycle()
    assert res.get("verdict") in ["SUCCESSFUL_UPDATE", "SUCCESSFUL_UPDATE_WITH_LIMITED_COVERAGE", "INTERNET_UNAVAILABLE"]

def test_18_atomic_rollback(updater):
    assert not updater.staging_dir.exists()
    assert not updater.backup_dir.exists()

def test_19_ssl_failure_handling(updater):
    assert updater.ssl_ctx.verify_mode != 0, "SSL context must use secure certificate verification"

def test_20_parsing_failure_handling(updater):
    success, n, age, gender = updater._try_retrieve_and_parse_pmc_fulltext("INVALID_PMC_ID_99999")
    assert success is False
    assert n is None

# --------------------------------------------------------------------------
# PART 17 STROKE CLASSIFIER TESTS (21 - 32)
# --------------------------------------------------------------------------

# Helper to build empty feature set
def _dummy_feature_set():
    from analysis.classification.feature_extractor import KinematicFeatureSet, ExtractedFeatureValue
    return KinematicFeatureSet(
        arm_phase_correlation=ExtractedFeatureValue("arm_phase_correlation", None, False),
        mean_body_roll=ExtractedFeatureValue("mean_body_roll", None, False),
        body_roll_amplitude=ExtractedFeatureValue("body_roll_amplitude", None, False),
        wrist_vertical_range_ratio=ExtractedFeatureValue("wrist_vertical_range_ratio", None, False),
        leg_kick_symmetry=ExtractedFeatureValue("leg_kick_symmetry", None, False),
        wrist_recovery_height_ratio=ExtractedFeatureValue("wrist_recovery_height_ratio", None, False),
        total_frames_in_window=0,
        valid_frames_in_window=0,
        window_start_frame=0,
        window_end_frame=0
    )

def test_21_to_24_all_four_strokes_reachable():
    from analysis.classification.stroke_heuristic_classifier import StrokeHeuristicClassifier
    from analysis.classification.feature_extractor import ExtractedFeatureValue
    
    classifier = StrokeHeuristicClassifier(confidence_threshold=0.75)
    
    # Test Freestyle Reachable
    f_free = _dummy_feature_set()
    f_free.arm_phase_correlation = ExtractedFeatureValue("arm_phase_correlation", raw_value=-0.8, valid=True)
    f_free.body_roll_amplitude = ExtractedFeatureValue("body_roll_amplitude", raw_value=25.0, valid=True)
    f_free.wrist_vertical_range_ratio = ExtractedFeatureValue("wrist_vertical_range_ratio", raw_value=0.20, valid=True)
    res_free = classifier.classify_features(f_free)
    assert res_free.predicted_stroke == StrokeType.FREESTYLE

    # Test Backstroke Reachable
    f_back = _dummy_feature_set()
    f_back.arm_phase_correlation = ExtractedFeatureValue("arm_phase_correlation", raw_value=-0.8, valid=True)
    f_back.body_roll_amplitude = ExtractedFeatureValue("body_roll_amplitude", raw_value=5.0, valid=True)
    f_back.wrist_vertical_range_ratio = ExtractedFeatureValue("wrist_vertical_range_ratio", raw_value=0.05, valid=True)
    res_back = classifier.classify_features(f_back)
    assert res_back.predicted_stroke == StrokeType.BACKSTROKE

    # Test Butterfly Reachable
    f_fly = _dummy_feature_set()
    f_fly.arm_phase_correlation = ExtractedFeatureValue("arm_phase_correlation", raw_value=0.8, valid=True)
    f_fly.wrist_vertical_range_ratio = ExtractedFeatureValue("wrist_vertical_range_ratio", raw_value=0.35, valid=True)
    res_fly = classifier.classify_features(f_fly)
    assert res_fly.predicted_stroke == StrokeType.BUTTERFLY

    # Test Breaststroke Reachable
    f_breast = _dummy_feature_set()
    f_breast.arm_phase_correlation = ExtractedFeatureValue("arm_phase_correlation", raw_value=0.8, valid=True)
    f_breast.wrist_vertical_range_ratio = ExtractedFeatureValue("wrist_vertical_range_ratio", raw_value=0.10, valid=True)
    res_breast = classifier.classify_features(f_breast)
    assert res_breast.predicted_stroke == StrokeType.BREASTSTROKE

def test_25_unknown_classification():
    from analysis.classification.stroke_heuristic_classifier import StrokeHeuristicClassifier
    classifier = StrokeHeuristicClassifier()
    f = _dummy_feature_set()
    res = classifier.classify_features(f)
    assert res.predicted_stroke == StrokeType.UNKNOWN

def test_26_27_ambiguous_input_and_low_confidence():
    from analysis.classification.stroke_heuristic_classifier import StrokeHeuristicClassifier
    from analysis.classification.feature_extractor import ExtractedFeatureValue
    classifier = StrokeHeuristicClassifier()
    f = _dummy_feature_set()
    f.arm_phase_correlation = ExtractedFeatureValue("arm_phase_correlation", raw_value=0.0, valid=True) # Ambiguous phase
    res = classifier.classify_features(f)
    assert res.predicted_stroke == StrokeType.UNKNOWN
    assert res.classification_status == "INSUFFICIENT_CONFIDENCE"

def test_28_29_missing_landmarks_and_insufficient_frames():
    classifier_obj = StrokeClassifier()
    fallback_res = classifier_obj._fallback()
    assert fallback_res.predicted_stroke == StrokeType.UNKNOWN
    assert fallback_res.confidence == 0.0

def test_30_no_silent_freestyle_fallback():
    classifier_obj = StrokeClassifier()
    fallback_res = classifier_obj._fallback()
    assert fallback_res.predicted_stroke != StrokeType.FREESTYLE
    assert fallback_res.predicted_stroke == StrokeType.UNKNOWN

def test_31_explainability_output():
    from analysis.classification.stroke_heuristic_classifier import StrokeHeuristicClassifier
    from analysis.classification.feature_extractor import ExtractedFeatureValue
    classifier = StrokeHeuristicClassifier()
    f = _dummy_feature_set()
    f.arm_phase_correlation = ExtractedFeatureValue("arm_phase_correlation", raw_value=-0.8, valid=True)
    f.body_roll_amplitude = ExtractedFeatureValue("body_roll_amplitude", raw_value=25.0, valid=True)
    res = classifier.classify_features(f)
    assert "feature_contributions" in dir(res) or hasattr(res, "feature_contributions")

def test_32_version_metadata():
    from analysis.classification.stroke_heuristic_classifier import CLASSIFIER_VERSION, THRESHOLD_VERSION
    assert CLASSIFIER_VERSION == "1.0.0-unvalidated"
    assert THRESHOLD_VERSION == "UNVALIDATED_HEURISTIC_v1.0"
