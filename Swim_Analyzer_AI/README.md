# 🏊 SwimAnalyzer AI — Professional Sports Analytics & Scientific Biomechanics Platform

**SwimAnalyzer AI** is a commercial-grade, peer-reviewed sports analytics and biomechanics platform built for competitive swimming coaches, biomechanists, and elite sports institutes.

It transforms raw video of swimming technique into auditable, 3D kinematic measurements, reliability scores, consistency validations, population benchmark comparisons, and longitudinal progression tracking across all four competitive stroke styles (**Freestyle, Backstroke, Breaststroke, Butterfly**).

---

## 🌟 Key Features Overview

### 1. 🎥 Multi-Stroke Pose Detection & Biomechanical Kinematics
- **Explicit Stroke Selection**: Mandatory user/coach selection of stroke style (**Freestyle, Backstroke, Breaststroke, Butterfly**) with default `-- Select Swimming Stroke --` validation to prevent accidental misanalysis.
- **Full Natural FPS Processing**: Operates at 100% native video FPS (`selected_stride = 1`), analyzing every frame without frame skipping.
- **3D Pose Estimation**: 3D body roll rotation, core torsion, joint angles (elbow, knee, shoulder), stroke cycle phase segmentation, and time-in-phase breakdown.
- **Biomechanical Metrics**:
  - **Stroke Rate (tempo)**: Measured in cycles per minute (spm) and Hz.
  - **Stroke Length (distance per stroke)**: Distance traveled per arm cycle in meters (m).
  - **Kick Frequency**: Kick cycles per second / minute.
  - **Stroke Symmetry**: Bilateral pull force and velocity symmetry index (%).
  - **3D Body Roll & Core Torsion**: Peak rotation angles relative to water plane.

### 2. 🛡️ Video Quality Assessment (VQA) & Reliability Engine
- **VQA Diagnostic Engine**: Evaluates resolution, frame rate, lighting, occlusion, and camera stability before analysis.
- **VQA Safety Mode**: Allows coaches to choose strict abort on critical video quality or continue analysis with a warning for edge-case footage.
- **Reliability Scoring**: Calculates confidence scores based on landmark visibility, jitter, and pose stability.
- **Scientific Consistency Validator**: Enforces mathematical consistency rules (e.g. flagging contradictions between high technique scores and poor video quality).

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
- **Annotated Video & Data Exports**: Export processed MP4 video with pose overlays via high-performance native renderer (`st.video`), JSON analysis reports, and metadata files.

---

## 🛠️ System Architecture

```
Swim_Analyzer_AI/
├── analysis/                        # Core Biomechanical Analysis Engines
│   ├── benchmarks/                  # Population BenchmarkEngine & percentile math
│   ├── classification/              # Deterministic temporal kinematic classification engine
│   ├── strategies/                  # Stroke-specific biomechanics & scoring strategies
│   ├── consistency_validator.py     # Scientific consistency rules
│   ├── reliability_engine.py       # Landmark reliability & confidence weighting
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
├── services/                        # Service Orchestration Layer
│   ├── analysis_service.py          # Complete video analysis orchestrator
│   ├── athlete_service.py           # Athlete profile CRUD service
│   ├── auth_service.py              # Coach login & authentication
│   ├── pdf_report_service.py        # FPDF PDF report exporter
│   └── scientific_evidence_service.py# Citation formatter & evidence resolver
└── tests/                           # Automated Pytest Suite
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

### 2. Launching Application
```bash
venv\Scripts\streamlit run app/streamlit_app.py
```
Open `http://localhost:8501` in your browser. Default login: `coach1` / `password123`.

---

## 🧪 Automated Testing

Run the test suite:
```bash
venv\Scripts\python -m pytest tests/ -v
```