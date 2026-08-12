"""
CSV Import & Validation Preview Service for Reference Data Manager.
Parses CSV files, validates rows against scientific integrity rules,
previews errors/warnings, generates sample CSV template, and imports validated rows.
"""

import io
import csv
from typing import List, Dict, Any, Tuple
from models.reference_data_models import (
    ReferenceDataset, ReferenceMetric, ReferenceSource,
    ReferenceBenchmarkEligibility, ReferenceValidationStatus, ReferenceSourceType
)
from services.reference_data_validator import ReferenceDataValidator

class CSVRowValidationResult:
    def __init__(self, row_index: int, raw_data: Dict[str, str]):
        self.row_index = row_index
        self.raw_data = raw_data
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.dataset_name: str = raw_data.get("dataset_name", "")
        self.stroke: str = raw_data.get("stroke", "FREESTYLE").upper()
        self.metric_name: str = raw_data.get("metric_name", "")

class CSVValidationPreview:
    def __init__(self):
        self.total_rows: int = 0
        self.valid_rows: int = 0
        self.invalid_rows: int = 0
        self.warnings_count: int = 0
        self.duplicate_rows: int = 0
        self.row_results: List[CSVRowValidationResult] = []

class ReferenceCSVService:
    EXPECTED_COLUMNS = [
        "dataset_name", "stroke", "age_min", "age_max", "sex", "skill_level", "athlete_category",
        "metric_name", "value_min", "value_typical", "value_median", "value_max", "unit",
        "measurement_domain", "status", "method",
        "source_type", "source_title", "authors", "publication_year", "doi", "pmid", "url", "sample_size"
    ]

    @classmethod
    def generate_sample_csv_template(cls) -> str:
        """Returns CSV template string with headers and sample valid rows."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cls.EXPECTED_COLUMNS)
        # Sample row 1: Primary study freestyle stroke rate
        writer.writerow([
            "Olympic 100m Freestyle Reference", "FREESTYLE", "18", "25", "Male", "Elite", "Sprinter",
            "stroke_rate", "52.0", "58.5", "58.0", "64.0", "spm",
            "CALIBRATED_PHYSICAL", "available", "video_2d",
            "PEER_REVIEWED_PRIMARY_STUDY", "Kinematic analysis of 100m elite swimmers", "Smith et al.", "2024", "10.1016/j.jbiomech.2024.100123", "38123456", "https://doi.org/10.1016/j.jbiomech.2024.100123", "24"
        ])
        # Sample row 2: Coach defined team reference
        writer.writerow([
            "Varsity Team Freestyle Baseline", "FREESTYLE", "18", "22", "Mixed", "Intermediate", "Adult",
            "stroke_length", "1.80", "2.10", "2.05", "2.40", "m",
            "CALIBRATED_PHYSICAL", "available", "manual_timing",
            "COACH_DEFINED", "Club Baseline Testing", "Coach Alex", "2026", "", "", "", "16"
        ])
        return output.getvalue()

    @classmethod
    def parse_and_validate_csv(cls, csv_content: str) -> CSVValidationPreview:
        """Parses CSV text and produces detailed validation preview."""
        preview = CSVValidationPreview()
        reader = csv.DictReader(io.StringIO(csv_content))
        
        seen_keys = set()

        for idx, row in enumerate(reader, start=1):
            preview.total_rows += 1
            row_res = CSVRowValidationResult(idx, row)

            # Mandatory dataset & metric names
            ds_name = row.get("dataset_name", "").strip()
            metric_name = row.get("metric_name", "").strip()
            stroke = row.get("stroke", "FREESTYLE").strip().upper()

            if not ds_name:
                row_res.is_valid = False
                row_res.errors.append("Missing required field 'dataset_name'.")

            if not metric_name:
                row_res.is_valid = False
                row_res.errors.append("Missing required field 'metric_name'.")

            # Numeric range checks
            def parse_float(val_str):
                if not val_str or val_str.strip() == "" or val_str.strip().lower() in ["none", "null", "n/a"]:
                    return None
                try:
                    return float(val_str.strip())
                except ValueError:
                    return "INVALID"

            v_min = parse_float(row.get("value_min", ""))
            v_typ = parse_float(row.get("value_typical", ""))
            v_med = parse_float(row.get("value_median", ""))
            v_max = parse_float(row.get("value_max", ""))

            for name, val in [("value_min", v_min), ("value_typical", v_typ), ("value_median", v_med), ("value_max", v_max)]:
                if val == "INVALID":
                    row_res.is_valid = False
                    row_res.errors.append(f"Field '{name}' must be a valid number or empty.")

            # Validate range order if numbers are valid
            if isinstance(v_min, float) and isinstance(v_max, float) and v_min > v_max:
                row_res.is_valid = False
                row_res.errors.append(f"value_min ({v_min}) cannot be greater than value_max ({v_max}).")

            if isinstance(v_min, float) and isinstance(v_typ, float) and v_min > v_typ:
                row_res.is_valid = False
                row_res.errors.append(f"value_min ({v_min}) cannot be greater than value_typical ({v_typ}).")

            if isinstance(v_typ, float) and isinstance(v_max, float) and v_typ > v_max:
                row_res.is_valid = False
                row_res.errors.append(f"value_typical ({v_typ}) cannot be greater than value_max ({v_max}).")

            # Domain check
            domain = row.get("measurement_domain", "UNAVAILABLE").strip().upper()
            if domain and domain not in ReferenceDataValidator.VALID_DOMAINS:
                row_res.is_valid = False
                row_res.errors.append(f"Invalid measurement_domain '{domain}'. Must be one of {sorted(list(ReferenceDataValidator.VALID_DOMAINS))}.")

            # Duplicate check within file
            dedup_key = f"{ds_name.lower()}_{stroke}_{metric_name.lower()}"
            if dedup_key in seen_keys:
                row_res.warnings.append(f"Duplicate entry for dataset '{ds_name}' and metric '{metric_name}' in CSV.")
                preview.duplicate_rows += 1
            else:
                seen_keys.add(dedup_key)

            # Rule 5 check: Imported CSV data defaults to DRAFT / CONTEXT_ONLY
            source_type = row.get("source_type", "IMPORTED_REFERENCE").strip().upper()
            if source_type not in ReferenceSourceType.__members__:
                row_res.warnings.append(f"Unrecognized source_type '{source_type}'. Defaulting to IMPORTED_REFERENCE.")

            if row_res.is_valid:
                preview.valid_rows += 1
            else:
                preview.invalid_rows += 1

            if row_res.warnings:
                preview.warnings_count += len(row_res.warnings)

            preview.row_results.append(row_res)

        return preview

    @classmethod
    def convert_csv_to_datasets(cls, preview: CSVValidationPreview) -> List[ReferenceDataset]:
        """
        Converts validated CSV rows into domain ReferenceDataset instances.
        Groups metrics by dataset_name.
        """
        dataset_map: Dict[str, ReferenceDataset] = {}

        for row_res in preview.row_results:
            if not row_res.is_valid:
                continue

            row = row_res.raw_data
            ds_name = row.get("dataset_name", "").strip()
            if not ds_name:
                continue

            if ds_name not in dataset_map:
                source_type = row.get("source_type", "IMPORTED_REFERENCE").strip().upper()
                if source_type not in ReferenceSourceType.__members__:
                    source_type = "IMPORTED_REFERENCE"

                # Rule 5: Imported CSV datasets default to DRAFT and CONTEXT_ONLY
                ds = ReferenceDataset(
                    name=ds_name,
                    stroke=row.get("stroke", "FREESTYLE").strip().upper(),
                    age_min=int(row.get("age_min", 0) or 0),
                    age_max=int(row.get("age_max", 100) or 100),
                    sex=row.get("sex", "Mixed").strip(),
                    skill_level=row.get("skill_level", "Unknown").strip(),
                    athlete_category=row.get("athlete_category", "Adult").strip(),
                    source_type=source_type,
                    evidence_status="INSUFFICIENT_EVIDENCE",
                    benchmark_eligibility=ReferenceBenchmarkEligibility.CONTEXT_ONLY.value,
                    validation_status=ReferenceValidationStatus.DRAFT.value
                )

                # Attach source metadata if available
                if row.get("source_title") or row.get("authors") or row.get("doi"):
                    pub_yr = row.get("publication_year")
                    sample_sz = row.get("sample_size")
                    src = ReferenceSource(
                        source_type=source_type,
                        source_title=row.get("source_title", ""),
                        authors=row.get("authors", ""),
                        publication_year=int(pub_yr) if pub_yr and pub_yr.isdigit() else None,
                        doi=row.get("doi", ""),
                        pmid=row.get("pmid", ""),
                        url=row.get("url", ""),
                        sample_size=int(sample_sz) if sample_sz and sample_sz.isdigit() else None
                    )
                    ds.sources.append(src)

                dataset_map[ds_name] = ds

            # Parse metric
            def parse_float(val_str):
                if not val_str or val_str.strip() == "" or val_str.strip().lower() in ["none", "null", "n/a"]:
                    return None
                try:
                    return float(val_str.strip())
                except ValueError:
                    return None

            m = ReferenceMetric(
                metric_name=row.get("metric_name", "").strip(),
                display_name=row.get("metric_name", "").replace("_", " ").title(),
                value_min=parse_float(row.get("value_min")),
                value_typical=parse_float(row.get("value_typical")),
                value_median=parse_float(row.get("value_median")),
                value_max=parse_float(row.get("value_max")),
                unit=row.get("unit", "").strip(),
                measurement_domain=row.get("measurement_domain", "UNAVAILABLE").strip().upper(),
                status=row.get("status", "available").strip(),
                method=row.get("method", "").strip()
            )
            dataset_map[ds_name].metrics.append(m)

        return list(dataset_map.values())
