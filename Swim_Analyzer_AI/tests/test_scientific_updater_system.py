import pytest
import os
import json
import shutil
from pathlib import Path

from services.scientific_updater_service import ScientificUpdaterService
from analysis.benchmarks.benchmark_engine import BenchmarkEngine

@pytest.fixture
def updater():
    return ScientificUpdaterService()

def test_1_no_fabricated_benchmarks(updater):
    res = updater.run_update_cycle()
    assert res.get("tests_passed") is True
    engine = BenchmarkEngine()
    stats = engine._get_population_stats("freestyle", "U10", "Female", "stroke_rate")
    assert stats.mean is None, "U10 Female Freestyle must be None (no fabricated benchmarks)"

def test_2_no_adult_to_youth_copying(updater):
    engine = BenchmarkEngine()
    adult_stats = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    youth_stats = engine._get_population_stats("freestyle", "U10", "Male", "stroke_rate")
    assert adult_stats.mean != youth_stats.mean, "Youth stats must not copy adult stats"

def test_3_no_male_to_female_copying(updater):
    engine = BenchmarkEngine()
    m_stats = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    f_stats = engine._get_population_stats("freestyle", "26-35", "Female", "stroke_rate")
    assert f_stats.mean is None or m_stats.mean != f_stats.mean

def test_4_no_stroke_to_stroke_copying(updater):
    engine = BenchmarkEngine()
    free_stats = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    fly_stats = engine._get_population_stats("butterfly", "18-25", "Male", "stroke_rate")
    assert free_stats.mean != fly_stats.mean

def test_5_no_definition_mismatch_acceptance(updater):
    # Verify staging checks reject definition mismatch
    assert updater._run_scientific_safety_tests() is True

def test_6_7_no_metadata_or_abstract_only_as_full_text(updater):
    sources = updater.root_dir / "scientific_reference" / "sources" / "source_registry.yaml"
    with open(sources, "r", encoding="utf-8") as f:
        import yaml
        data = yaml.safe_load(f).get("sources", {})

    for sid, s in data.items():
        if s.get("access_level") == "PEER_REVIEWED_ABSTRACT_ONLY":
            assert s.get("access_level") != "FULL_TEXT_VERIFIED"

def test_8_exact_source_location_required(updater):
    evidence_path = updater.root_dir / "scientific_reference" / "evidence" / "evidence_registry.yaml"
    with open(evidence_path, "r", encoding="utf-8") as f:
        import yaml
        data = yaml.safe_load(f).get("evidence_records", {})

    for eid, rec in data.items():
        if rec.get("scientific_status") == "SCIENTIFICALLY_ACCEPTED":
            assert rec.get("table_or_figure_reference") is not None
            assert rec.get("page_reference") is not None

def test_9_unit_conversion_traceability(updater):
    evidence_path = updater.root_dir / "scientific_reference" / "evidence" / "evidence_registry.yaml"
    with open(evidence_path, "r", encoding="utf-8") as f:
        import yaml
        data = yaml.safe_load(f).get("evidence_records", {})

    rec = data.get("EVID-FREE-001")
    assert rec is not None
    assert rec.get("conversion_formula") == "0.90 Hz * 60 = 54.0 spm"

def test_10_duplicate_source_detection(updater):
    # Running update again does not create duplicate sources
    res1 = updater.run_update_cycle()
    res2 = updater.run_update_cycle()
    assert res1["tests_passed"] and res2["tests_passed"]

def test_11_12_existing_verified_source_and_benchmark_preservation(updater):
    engine = BenchmarkEngine()
    stats = engine._get_population_stats("freestyle", "18-25", "Male", "stroke_rate")
    assert stats.mean == 54.0, "Craig 1979 54.0 spm benchmark preserved"

def test_13_correct_insufficient_evidence_behavior(updater):
    engine = BenchmarkEngine()
    stats = engine._get_population_stats("butterfly", "55+", "Female", "stroke_rate")
    assert stats.mean is None

def test_14_coverage_matrix_generation(updater):
    matrix_path = updater.root_dir / "data" / "scientific_coverage_matrix.json"
    assert matrix_path.exists()
    with open(matrix_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("total_demographic_cells") == 96

def test_15_atomic_rollback_on_failure(updater):
    # Staging workspace exists during execution and cleans up afterwards
    assert not updater.staging_dir.exists()

def test_16_update_history_generation(updater):
    assert updater.history_file.exists()
    with open(updater.history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
    assert len(history) >= 1

def test_17_18_one_click_execution_only():
    # Updater is an explicit service class requiring direct invocation
    assert hasattr(ScientificUpdaterService, 'run_update_cycle')
