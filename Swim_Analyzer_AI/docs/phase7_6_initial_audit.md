# Phase 7.6 Initial Architecture & Codebase Audit Report

**Platform**: SwimAnalyzer AI  
**Author**: Lead Scientific Software Architect & Research Data Engineer  
**Date**: August 8, 2026  
**Status**: FACTUAL SOURCE CODE AUDIT COMPLETE — REPAIR INITIATED  

---

## 📌 Executive Summary

This report establishes the factual baseline of the SwimAnalyzer AI repository prior to Phase 7.6 repairs. Every entry is based directly on inspection of the active source code, ignoring prior task summaries or unverified claims.

---

## 🔍 Detailed Codebase Discrepancies & Problems Identified

| Problem ID | Component / File | Function / Class | Current Code Behavior | Why Incorrect | Required Correction | Severity |
|---|---|---|---|---|---|---|
| **BUG-01** | `services/scientific_updater_service.py` | `ScientificUpdaterService.__init__` | Sets `self.ssl_ctx.verify_mode = ssl.CERT_NONE` and `check_hostname = False`. | Disables HTTPS certificate validation, violating SSL security requirements (Part 11). | Remove `CERT_NONE` and use secure default SSL context with HTTPS verification. Abort safely on SSL failure. | **HIGH** |
| **BUG-02** | `services/scientific_updater_service.py` | `_search_literature` | Automatically marks `access_level = "FULL_TEXT_VERIFIED"` whenever `pmc_id` exists in PubMed metadata. | Violates Part 3 rule prohibiting auto-marking full text without actual retrieval and XML parsing. | Retrieve real PMC full-text XML, parse `<body>` and `<table>` tags, and set `FULL_TEXT_VERIFIED` ONLY upon successful parsing. | **CRITICAL** |
| **BUG-03** | `services/scientific_updater_service.py` | `_search_literature` | Hardcodes default metadata for discovered studies (`sample_size: 20`, `age_range: "18-25"`, `gender: "Mixed"`). | Violates Rule 1 & Part 4 prohibiting fabricated sample sizes, age ranges, or sex distributions. | Parse actual participant demographics from PMC XML or leave as `None` with `INSUFFICIENT_EVIDENCE`. | **CRITICAL** |
| **BUG-04** | `services/scientific_updater_service.py` | `_rebuild_coverage_matrix` | Hardcodes `verified_count = 12` and `insufficient_count = 84`. | Violates Part 8 requiring dynamic matrix calculation across 96 demographic cells. | Dynamically query `ScientificEvidenceService` / taxonomy across 4 strokes × 3 sexes × 12 age groups. | **HIGH** |
| **BUG-05** | `services/scientific_updater_service.py` | `_commit_staging_files` | Uses basic `shutil.copytree(..., dirs_exist_ok=True)`. | Lacks backup snapshot before committing, violating Part 10 transaction & rollback requirements. | Implement backup snapshot (`data/scientific_db_backup/`), atomic replacement, and rollback. | **HIGH** |
| **BUG-06** | `analysis/stroke_classifier.py` | `predict` | Contains legacy comment referring to simulation fallback. | Outdated comment creates confusion about classification mechanics. | Remove legacy comments, verify feature extractor, and enforce confidence gate $< 0.75 \rightarrow$ `UNKNOWN`. | **MEDIUM** |

---

## 🛑 Action Plan for Phase 7.6 Implementation

1. **Repair Scientific Literature Engine (`services/scientific_updater_service.py`)**:
   - Secure SSL HTTPS context (`ssl.create_default_context()`).
   - Implement real PMC XML full-text retrieval (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_id}&retmode=xml`).
   - Implement XML parser for `<abstract>`, `<body>`, `<sec>`, `<table>`, `<fig>`, extracting actual participant sample sizes $N$, mean age, and biomechanical metric values (mean/SD/unit).
   - Require successful XML parsing before assigning `FULL_TEXT_VERIFIED`. Otherwise assign `PEER_REVIEWED_ABSTRACT_ONLY`.
   - Remove all default/fabricated metadata assignments (`sample_size = 20`, `age_range = "18-25"`).

2. **Repair Dynamic Coverage Matrix Calculation**:
   - Dynamically compute supported vs `INSUFFICIENT_EVIDENCE` cells by cross-referencing evidence records with `PopulationTaxonomyService` across 96 total cells (4 strokes × 3 sexes × 12 age groups).

3. **Repair Atomic Transaction Model & Rollback**:
   - Create production snapshot backup before staging commit.
   - Restore snapshot and roll back atomically if any validation step or test fails.

4. **Verify Stroke Classifier & Safety Gate**:
   - Ensure predictions with confidence $< 0.75$ output `predicted_stroke = UNKNOWN` and `classification_status = "INSUFFICIENT_CONFIDENCE"`. Zero silent fallback to Freestyle.

5. **Test Suite Expansion**:
   - Add/update tests in `tests/test_scientific_updater_system.py` and `tests/test_stroke_classifier.py` covering all 32 required test scenarios.

---

```
==================================================
PHASE 7.6 FACTUAL AUDIT COMPLETE
AUDIT REPORT CREATED: docs/phase7_6_initial_audit.md
REPAIR PHASE READY TO START
==================================================
```
