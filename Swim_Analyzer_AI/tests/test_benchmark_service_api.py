"""
Regression test for BenchmarkService -> BenchmarkEngine API compatibility.
Ensures evaluate_session and evaluate_full_analysis execute without AttributeError,
and verifies zero-fallback handling for missing metrics.
"""

import pytest
from services.benchmark_service import BenchmarkService
from analysis.benchmarks.benchmark_engine import BenchmarkEngine
from models.data_models import AnalysisResult, PerformanceReport, ValidatedMetric, StrokeDetectionResult, StrokeType
from models.athlete_profile import AthleteProfile
from models.scientific_evidence_models import ValidationStatus


def test_benchmark_service_evaluate_session_api_compatibility():
    """Verify BenchmarkService calls BenchmarkEngine without AttributeError."""
    service = BenchmarkService()

    analysis_result = AnalysisResult(video_path="dummy.mp4")
    # stroke_detection lives on VideoMetadata, NOT AnalysisResult.
    # The engine uses getattr(..., None) so this is fine.
    analysis_result.report = PerformanceReport(
        overall_score=85.0,
        stroke_rate=ValidatedMetric(name="stroke_rate", value=55.0, valid=True, unit="spm"),
        stroke_length=ValidatedMetric(name="stroke_length", value=None, valid=False, unit="m"),
    )

    athlete = AthleteProfile(
        full_name="Test Athlete",
        age=22,
        gender="Male",
        height_cm=180.0,
        weight_kg=75.0,
        swimming_level="Elite",
        preferred_stroke="Freestyle",
    )

    res = service.evaluate_session(analysis_result, athlete)

    assert res is not None
    assert res.stroke_type == "Freestyle"   # default when no stroke_detection
    assert res.age_group == "18-25"
    assert res.gender == "Male"
    # stroke_rate has a valid value, must appear in comparisons
    assert "stroke_rate" in res.comparisons

    # stroke_length value is None — zero-fallback policy: must NOT appear or raw_value must be None
    if "stroke_length" in res.comparisons:
        assert res.comparisons["stroke_length"].raw_value is None


def test_benchmark_engine_evaluate_full_analysis_alias():
    """Verify BenchmarkEngine.evaluate_full_analysis alias delegates correctly."""
    engine = BenchmarkEngine()

    analysis_result = AnalysisResult(video_path="dummy.mp4")
    analysis_result.report = PerformanceReport(
        overall_score=90.0,
        stroke_rate=ValidatedMetric(name="stroke_rate", value=60.0, valid=True, unit="spm"),
    )

    res = engine.evaluate_full_analysis(analysis_result)
    assert res is not None
    assert res.stroke_type == "Freestyle"
    assert "stroke_rate" in res.comparisons


def test_benchmark_engine_no_stroke_detection_no_error():
    """Verify that missing stroke_detection attribute does NOT raise AttributeError."""
    engine = BenchmarkEngine()
    ar = AnalysisResult(video_path="dummy.mp4")
    # Intentionally no stroke_detection attribute set
    try:
        res = engine.evaluate_analysis(ar)
        assert res is not None
        assert res.stroke_type == "Freestyle"
    except AttributeError as e:
        pytest.fail(f"AttributeError raised: {e}")


def test_benchmark_result_none_metric_stays_none():
    """Verify zero-fallback: ValidatedMetric with value=None does NOT produce a comparison."""
    engine = BenchmarkEngine()
    ar = AnalysisResult(video_path="dummy.mp4")
    ar.report = PerformanceReport(
        overall_score=None,
        stroke_rate=ValidatedMetric(name="stroke_rate", value=None, valid=False),
        stroke_length=ValidatedMetric(name="stroke_length", value=None, valid=False),
    )
    res = engine.evaluate_analysis(ar)
    # None metrics must NOT generate comparisons with fabricated fallback values
    for name, comp in res.comparisons.items():
        assert comp.raw_value is not None, f"Expected no comparison for {name} with None value, but got one."
