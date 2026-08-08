# 🏊 SwimAnalyzer AI — Professional Sports Analytics & Scientific Biomechanics Platform

**SwimAnalyzer AI** is a commercial-grade, peer-reviewed sports analytics and biomechanics platform built for competitive swimming coaches, biomechanists, and elite sports institutes.

It transforms raw video of swimming technique into auditable, 3D kinematic measurements, reliability scores, consistency validations, population benchmark comparisons, and longitudinal progression tracking across all four competitive stroke styles (**Freestyle, Backstroke, Breaststroke, Butterfly**).

---

## 🌟 Key Features Overview

### 1. 🎥 Multi-Stroke Pose Detection & Biomechanical Kinematics
- **Automatic Stroke Classification**: AI-powered stroke detection for Freestyle, Backstroke, Breaststroke, and Butterfly with confidence scoring and manual coach override.
- **3D Pose Estimation**: 3D body roll, core torsion, joint angles (elbow, knee, shoulder), stroke cycle phase segmentation, and time-in-phase breakdown.
- **Biomechanical Metrics**:
  - **Stroke Rate (tempo)**: Measured in cycles per minute (spm) and Hz.
  - **Stroke Length (distance per stroke)**: Distance traveled per arm cycle in meters (m).
  - **Kick Frequency**: Kick cycles per second / minute.
  - **Stroke Symmetry**: Bilateral pull force and velocity symmetry index (%).
  - **3D Body Roll & Core Torsion**: Peak rotation angles relative to water plane.

### 2. 🛡️ Video Quality Assessment (VQA) & Reliability Engine
- **VQA Diagnostic Engine**: Evaluates resolution, frame rate, lighting, occlusion, and camera stability before analysis.
- **Reliability Scoring**: Calculates confidence scores based on landmark visibility, jitter, and pose stability.
- **Scientific Consistency Validator**: Enforces 7 mathematical consistency rules (e.g. flagging contradictions between high technique scores and poor video quality).

### 3. 👥 Coach Command Center & Athlete Management
- **Multi-Coach Authentication**: Secure login system with coach-isolated athlete rosters.
- **Athlete Profile Directory**: Comprehensive profiles including age, gender, height, weight, swimming level, preferred stroke, notes, and training goals.
- **Longitudinal History & Progression**: Tracks performance scores, completed cycles, and metrics over time with interactive Plotly charts.
- **Session Comparison Tool**: Side-by-side comparison of baseline vs recent sessions to measure technical progression and resolved movement flaws.

### 4. 🔬 Evidence-First Scientific Benchmarking & Provenance
- **100% Traceable Literature Provenance**: Every population benchmark value links directly to published peer-reviewed studies (e.g., Craig & Pendergast 1979, Psycharakis & Sanders 2008/2010, Gonjo et al. 2020, Leblanc et al. 2005, Seifert et al. 2008).
- **Audit Decision Taxonomy**: Benchmarks classified as `ACCEPT`, `ACCEPT_AS_DERIVED`, `REFERENCE_ONLY`, or `REJECT`.
- **Demographic Compatibility Guard**: Percentiles and Z-scores are strictly suppressed for non-compatible demographic groups (Female, Youth U10/U13/U17, Masters) with clear warning banners to prevent false scientific claims.
- **Interactive Evidence Cards**: Expandable `"🔬 Scientific Evidence"` drawers displaying DOI, journal, authors, sample size ($N$), original values, conversion formulas, and exact page/table locations.

### 5. 📄 Export & Reporting
- **Automated PDF Reports**: Detailed session analysis and longitudinal athlete summary reports via `PDFReportService`.
- **Annotated Video & Data Exports**: Export processed MP4 video with pose overlays, JSON analysis reports, and metadata files.

---

## 🛠️ System Architecture

```
Swim_Analyzer_AI/
├── analysis/                        # Core Biomechanical Analysis Engines
│   ├── benchmarks/                  # Population BenchmarkEngine & percentile math
│   ├── strategies/                  # Stroke-specific biomechanics & scoring strategies
│   ├── consistency_validator.py     # 7 scientific consistency rules
│   ├── reliability_engine.py       # Landmark reliability & confidence weighting
│   ├── stroke_classifier.py         # AI stroke type detection & override
│   └── vqa_engine.py                # Video Quality Assessment engine
├── app/                             # Web Application & UI Components
│   ├── streamlit_app.py             # Main Streamlit SaaS application
│   └── ui/
│       ├── benchmark_ui.py          # Population Benchmark Cards & evidence drawers
│       └── charts.py                # Interactive Plotly progression & bell curve charts
├── config/
│   └── benchmarks/                  # Provenance-enriched YAML benchmark datasets
│       ├── freestyle.yaml
│       ├── backstroke.yaml
│       ├── breaststroke.yaml
│       └── butterfly.yaml
├── models/                          # Dataclasses & Domain Schemas
│   ├── athlete_profile.py           # Athlete Profile data model
│   ├── benchmark_models.py          # Benchmark comparisons & results
│   ├── data_models.py               # Biomechanical frames & analysis reports
│   └── scientific_evidence_models.py# Evidence records, provenance, and audit enums
├── scientific_reference/            # Science Layer & Literature Pipeline
│   ├── discovery/                   # PubMed / Europe PMC legal API discovery
│   ├── retrieval/                   # Open-access document retriever
│   ├── storage/                     # EvidenceRegistry repository
│   ├── evidence/                    # evidence_registry.yaml database
│   └── scientific_benchmark_builder.py# Benchmark dataset compiler
├── services/                        # Service Orchestration Layer
│   ├── analysis_service.py          # Complete video analysis orchestrator
│   ├── athlete_service.py           # Athlete profile CRUD service
│   ├── auth_service.py              # Coach login & authentication
│   ├── pdf_report_service.py        # FPDF PDF report exporter
│   └── scientific_evidence_service.py# Citation formatter & evidence resolver
└── tests/                           # Automated Pytest Suite (63 Tests)
```

---

## 🚀 Quickstart & Installation

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/AbdelbasetAbdelaal/Drone.git Swim_Analyzer_AI
cd Swim_Analyzer_AI

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Streamlit Application
```bash
streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

**Default Coach Credentials**:
- **Username**: `coach1`
- **Password**: `password123`

---

## 📖 Usage Guide

### 🏊‍♂️ Analyzing a Swimming Video
1. Log in to the application and navigate to **🏊‍♂️ Video Analysis**.
2. Select an athlete from your roster or analyze as a **Guest Swimmer**.
3. Upload a swimming technique MP4 video.
4. Select the stroke type or choose **Auto Detect**.
5. Click **Analyze Swimming Technique**.
6. View results across full-width SaaS tabs:
   - **📋 Overview**: Video playback, video quality score, analysis reliability, and consistency rules.
   - **🧬 Biomechanics**: Key metrics, stroke rate, stroke length, symmetry, kick frequency, detected movement errors, and coaching feedback.
   - **📊 Population Benchmarks**: Benchmark Cards, evidence status badges, demographic compatibility checks, and expandable `"🔬 Scientific Evidence"` drawers.
   - **🧊 3D Analysis**: 3D body roll and core torsion angles.
   - **📈 Raw Data Charts**: Interactive joint angle time-series graphs and phase statistics.
   - **📥 Downloads**: Download PDF summary reports, processed video, and JSON metadata.

### 👥 Managing Athlete Profiles
1. Navigate to **👥 Athletes**.
2. Click **Create New Athlete** to add an athlete profile (Name, Age, Gender, Height, Weight, Level, Preferred Stroke, Coach Notes, Goals).
3. Click **View Profile** to inspect progression charts, session history, and download longitudinal PDF reports.

### ⚖️ Comparing Analysis Sessions
1. Navigate to **📜 History** or an Athlete Profile page.
2. Select **Session A (Baseline)** and **Session B (Recent)**.
3. Click **Generate Comparison Report** to compare technique metric deltas, score progression, resolved errors, and new movement flaws.

---

## 🧪 Automated Verification & Test Suite

SwimAnalyzer AI includes an automated test suite containing 63 unit and integration test cases enforcing zero scientific regressions:

```bash
# Run full test suite
pytest tests/ -v
```

**Test Coverage Breakdown**:
- `tests/test_final_scientific_audit.py`: Audit safety rules, exact source locations, definition mismatch guards, derived conversion formulas.
- `tests/test_phase7_5_ui_safety.py`: Demographic compatibility guards, percentile safety, stroke isolation, PDF/Streamlit alignment.
- `tests/test_scientific_extraction_pipeline.py`: Literature extraction pipeline, unit conversion layer, population matching.
- `tests/test_source_value_traceability.py`: Source-to-value traceability tags and validated metric relationships.
- `tests/test_consistency_validator.py`: 7 scientific consistency rules and contradiction detection.
- `tests/test_reliability_engine.py`: Pose landmark confidence and noise jitter calculations.
- `tests/test_athlete_profile.py`: Athlete profile CRUD and JSON persistence.
- `tests/test_analysis_history.py`: Session logging and comparison.

---

## 📜 License & Citation

Developed for **SwimAnalyzer AI**. All scientific literature citations and DOIs are preserved in `scientific_reference/sources/source_registry.yaml`.


venv\Scripts\activate
streamlit run app/streamlit_app.py
http://localhost:8501