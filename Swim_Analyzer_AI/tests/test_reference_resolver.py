"""
Tests for ReferenceDataResolver demographic compatibility and priority scoring.
"""

import pytest
from models.reference_data_models import ReferenceDataset, ReferenceMetric, ReferenceValidationStatus
from services.reference_resolver import ReferenceDataResolver

def test_demographic_incompatibility_returns_zero_score():
    """Verify that demographic incompatibility gives REFERENCE_MATCH_SCORE = 0.0."""
    ds = ReferenceDataset(
        name="Adult Male Freestyle Dataset",
        stroke="FREESTYLE",
        age_min=18,
        age_max=25,
        sex="Male"
    )

    # Stroke mismatch
    score_stroke, warn1 = ReferenceDataResolver.calculate_compatibility(ds, stroke="BUTTERFLY", age=20, sex="Male")
    assert score_stroke == 0.0
    assert any("Incompatible stroke" in w for w in warn1)

    # Youth vs Adult age mismatch
    score_age, warn2 = ReferenceDataResolver.calculate_compatibility(ds, stroke="FREESTYLE", age=12, sex="Male")
    assert score_age == 0.0
    assert any("Youth vs Adult age boundary violation" in w for w in warn2)

def test_priority_ranking_peer_reviewed_wins():
    """Verify peer-reviewed study outranks coach-defined dataset when both are demographic compatible."""
    ds_coach = ReferenceDataset(
        dataset_id="ds_coach",
        name="Coach Baseline",
        stroke="FREESTYLE",
        age_min=18,
        age_max=25,
        sex="Male",
        source_type="COACH_DEFINED",
        validation_status="COACH_VALIDATED",
        metrics=[ReferenceMetric(metric_name="stroke_rate", value_typical=56.0, unit="spm")]
    )

    ds_peer = ReferenceDataset(
        dataset_id="ds_peer",
        name="Peer Reviewed Olympic Study",
        stroke="FREESTYLE",
        age_min=18,
        age_max=25,
        sex="Male",
        source_type="PEER_REVIEWED_PRIMARY_STUDY",
        validation_status="SCIENTIFICALLY_VALIDATED",
        metrics=[ReferenceMetric(metric_name="stroke_rate", value_typical=58.0, unit="spm")]
    )

    resolved = ReferenceDataResolver.resolve_metric_reference(
        datasets=[ds_coach, ds_peer],
        metric_name="stroke_rate",
        stroke="FREESTYLE",
        athlete_age=20,
        athlete_sex="Male"
    )

    assert resolved.selected_dataset_id == "ds_peer"
    assert resolved.selected_dataset_name == "Peer Reviewed Olympic Study"
    assert resolved.scientific_confidence == "High"
    assert resolved.compatibility_score >= 90.0
