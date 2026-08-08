# One-Click Scientific Database Update System Architecture & User Manual

**Platform**: SwimAnalyzer AI  
**Author**: Lead Scientific Software Architect & Research Data Engineer  
**Date**: August 8, 2026  
**Document Version**: 2.0.0  

---

## 📌 1. System Overview & Architecture

The **One-Click Scientific Database Update System** enables coaches and sports biomechanists to execute explicit, user-triggered scientific literature update transactions directly from the SwimAnalyzer AI application interface.

```
+-------------------------------------------------------------------+
|                        STREAMLIT APP UI                           |
|        [ 🔄 تحديث قاعدة البيانات العلمية / Update Scientific Database ]        |
+---------------------------------+---------------------------------+
                                  | (Explicit User Click Only)
                                  v
+-------------------------------------------------------------------+
|                  SCIENTIFIC UPDATER SERVICE                       |
|           (services/scientific_updater_service.py)                |
+---------------------------------+---------------------------------+
                                  |
            +---------------------+---------------------+
            |                                           |
            v                                           v
+-----------------------+                   +-----------------------+
|  PUBMED / PMC APIS    |                   |  ATOMIC STAGING AREA  |
|  (E-Utilities Search) |                   | (data/update_staging/)|
+-----------+-----------+                   +-----------+-----------+
            |                                           |
            +---------------------+---------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|             SCIENTIFIC SAFETY & PROVENANCE VALIDATION             |
|   (Population Matching, Definition Matching, Traceability Tests)  |
+---------------------------------+---------------------------------+
                                  |
                     +------------+------------+
                     |                         |
             (Pass: 100%)              (Fail / Offline)
                     v                         v
+-------------------------------+   +-------------------------------+
|    ATOMIC PRODUCTION COMMIT   |   |        SAFETY ROLLBACK        |
| - source_registry.yaml        |   | - Previous DB Preserved       |
| - evidence_registry.yaml      |   | - Staging Workspace Cleaned   |
| - benchmark YAMLs             |   | - Warning / Error Banner      |
| - coverage_matrix.json        |   | - History Log Recorded        |
+-------------------------------+   +-------------------------------+
```

---

## 🏛️ 2. Approved Source Policy & Access Level Hierarchy

The updater queries approved scientific databases in order of priority:
1. **PubMed / NCBI E-Utilities** (`esearch`, `efetch`)
2. **PubMed Central (PMC)**
3. **Europe PMC**
4. **Crossref & Official Open Access Repositories**

### Source Access Level Hierarchy

| Access Level Tag | Legal & Technical Criteria | Benchmark Eligibility |
|---|---|---|
| **`FULL_TEXT_VERIFIED`** | Article full text legally retrieved, parsed, and table/page citations verified. | **Eligible** for production benchmark promotion. |
| **`PEER_REVIEWED_ABSTRACT_ONLY`** | Only abstract text available in PubMed/PMC. | **Ineligible** for table-level benchmark promotion (stored as `REFERENCE_ONLY`). |
| **`METADATA_ONLY`** | Only bibliographic metadata (title, authors, year) resolved. | **Ineligible** for benchmark promotion. |
| **`SECONDARY_SOURCE`** | ASCA monographs, non-peer-reviewed summaries. | **Ineligible** for primary benchmark promotion. |
| **`TEXTBOOK`** | Academic books (e.g. Maglischo 2003). | Stored as `LEVEL_C` reference only. |
| **`REJECTED`** | Duplicate entry, invalid methodology, or non-swimming study. | **Excluded**. |

---

## 🔍 3. Traceability Chain & Benchmark Acceptance Rules

Every candidate scientific metric value must satisfy an unbroken **11-Point Provenance Chain**:

```
Production Benchmark YAML Value
  └── Derived or Direct Relation Tag
        └── Original Reported Value & Units
              └── Metric Definition Match Status (EXACT_MATCH)
                    └── Table / Figure / Page Citation
                          └── Primary Study Title & Authors
                                └── PMID / PMCID / DOI
                                      └── Source Access Level (FULL_TEXT_VERIFIED)
                                            └── Retrieval Timestamp & Verification Status
```

### Mandatory Safety Gates
1. **No Demographic Leakage**: Male data is NEVER applied to Female athletes; Adult data is NEVER scaled to Youth or Masters.
2. **No Stroke Leakage**: Freestyle, Backstroke, Breaststroke, and Butterfly metrics are strictly isolated.
3. **No Definition Mismatch**: Incompatible parameters (e.g. torso vector vs shoulder roll) are tagged `DEFINITION_MISMATCH` and excluded.
4. **No Value Fabrication**: Missing demographic combinations return `status: INSUFFICIENT_EVIDENCE` and `benchmark: null`.

---

## 🔄 4. Atomic Staging & Rollback Mechanism

1. **Isolation**: All download, parsing, extraction, YAML updating, coverage matrix rebuilding, and testing occur inside `data/scientific_update_staging/`.
2. **Automated Safety Test Execution**: Before committing, the engine runs automated safety tests (`_run_scientific_safety_tests()`).
3. **Atomic Commit**: If tests pass 100%, files are atomically copied to production directories (`scientific_reference/`, `config/benchmarks/`, `data/`).
4. **Safety Rollback**: If an internet failure, HTTP 500 error, or test failure occurs:
   - Staging workspace is purged.
   - Production scientific database remains 100% untouched.
   - UI displays: `"تعذر الوصول إلى المصادر العلمية. لم يتم تغيير قاعدة البيانات."`

---

## 🖥️ 5. User Interface Instructions

1. Navigate to **Developer Settings / Scientific Database Management** in the Streamlit sidebar.
2. Click **`"🔄 تحديث قاعدة البيانات العلمية"`** (`"Update Scientific Database"`).
3. The UI will show real-time progress steps:
   - *Connecting to scientific databases...*
   - *Searching peer-reviewed literature...*
   - *Verifying source access levels...*
   - *Extracting population evidence & rebuilding coverage matrix...*
   - *Running scientific safety tests...*
4. Upon completion, a compact summary card displays discovered studies, verified full texts, evidence records added, newly verified cohorts, and transaction timestamps.

---

```
==================================================
ONE-CLICK UPDATER MANUAL & SPECIFICATION COMPLETE
SYSTEM STATUS: PRODUCTION READY
PHASE 8 AI COACH: UNTOUCHED & BLOCKED
==================================================
```
