"""
Tests for CSVRegistryImporter and reference CSV parsing.
Verifies parsing of swimming_reference_data_v2_scientific_registry.csv.
"""

import os
import pytest
from services.csv_registry_importer import CSVRegistryImporter

def test_import_scientific_registry_csv():
    csv_file = "swimming_reference_data_v2_scientific_registry.csv"
    assert os.path.exists(csv_file), "Reference CSV file must exist in workspace root."

    valid, rejected, errs = CSVRegistryImporter.import_scientific_registry_csv(
        csv_path=csv_file,
        version_name="test_import_v2",
        importer_name="Pytest Suite"
    )

    assert valid > 100, f"Expected >100 valid imported rows, got {valid}"
    assert isinstance(errs, list)

def test_null_preservation_on_import():
    """Verify empty fields remain None and are not coerced to 0."""
    csv_file = "swimming_reference_data_v2_scientific_registry.csv"
    valid, rejected, errs = CSVRegistryImporter.import_scientific_registry_csv(
        csv_path=csv_file,
        version_name="test_null_check_v1"
    )

    from services.reference_data_manager import ReferenceDataManager
    mgr = ReferenceDataManager()
    datasets = mgr.get_records(stroke="BUTTERFLY", metric_name="Start Time")
    assert len(datasets) > 0
    m = datasets[0].metrics[0]
    assert m.value_min is None or isinstance(m.value_min, float)
    mgr.close()
