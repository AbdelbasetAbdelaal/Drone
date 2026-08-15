# 🏊 SwimAnalyzer AI — Professional Sports Analytics & Scientific Biomechanics Platform

**SwimAnalyzer AI** is a commercial-grade, peer-reviewed sports analytics and biomechanics platform built for competitive swimming coaches, biomechanists, and elite sports institutes.

It transforms raw video of swimming technique into auditable, 3D kinematic measurements, reliability scores, consistency validations, population benchmark comparisons, and longitudinal progression tracking across all four competitive stroke styles (**Freestyle, Backstroke, Breaststroke, Butterfly**).

---

## 🌟 Key Features Overview

### 1. 🏊 Mandatory User Stroke Selection & Biomechanical Kinematics
- **Single Source of Truth (`selected_stroke`)**: The user MUST explicitly select the swimming stroke style (**Freestyle**, **Backstroke**, **Breaststroke**, or **Butterfly**) before starting analysis. The system default `-- Select Swimming Stroke --` blocks execution until a valid stroke is selected.
- **Zero Inferencing / Overrides**: The system never overrides, infers, or recalculates the user-selected stroke.
- **100% Full Natural Native FPS Processing**: Operates at native video resolution and 100% FPS (`selected_stride = 1`), analyzing every single frame.
- **3D Pose & Kinematics**: Calculates 3D body roll rotation, core torsion, joint angles (elbow, knee, shoulder), stroke cycle phase segmentation, and time-in-phase breakdown.
- **Key Metrics**:
  - **Stroke Rate (tempo)**: Cycles per minute (spm) and Hz.
  - **Stroke Length (distance per stroke)**: Distance traveled per arm cycle in meters (m).
  - **Kick Frequency**: Kick cycles per second / minute.
  - **Stroke Symmetry**: Bilateral force and velocity symmetry index (%).
  - **3D Body Roll & Core Torsion**: Rotation angles relative to water plane.

### 2. 🔬 Transparent Video Analysis Reliability Engine
- **Decoupled Quality Model**: "Confidence" refers exclusively to empirical **Video Analysis Reliability** (pose tracking stability, landmark visibility, frame coverage, cycle quality), and NEVER to stroke classification probability.
- **Reliability Formula**:
  $$\text{Reliability} = 0.25 \cdot \text{FrameCoverage} + 0.25 \cdot \text{PoseValidity} + 0.20 \cdot \text{LandmarkVisibility} + 0.15 \cdot \text{TemporalStability} + 0.15 \cdot \text{CycleQuality}$$
- **Data Quality Warnings**: Automatically detects low-quality footage (insufficient valid frames, low landmark visibility, swimmer leaving frame) and logs explicit quality warnings.

### 3. 🛡️ Video Quality Assessment (VQA) & Safety Engine
- **VQA Pre-check**: Evaluates resolution, frame rate, lighting, occlusion, and camera stability.
- **Scientific Consistency Validator**: Enforces 7 mathematical rules to ensure scientific trustworthiness.

### 4. 👥 Coach Command Center & Roster Management
- **Coach Authentication**: Isolated coach accounts and athlete rosters.
- **Longitudinal Progression Tracking**: Tracks scores, metrics, and technical flaw resolution over time.
- **Session-to-Session Comparison**: Side-by-side comparison of baseline vs recent sessions.

### 5. 🔬 Literature Provenance & Scientific Benchmarks
- **100% Traceable Literature**: Population benchmark values link directly to peer-reviewed studies (Craig & Pendergast 1979, Psycharakis & Sanders 2008/2010, Gonjo et al. 2020, Leblanc et al. 2005).
- **Demographic Compatibility Guard**: Suppresses percentile math for non-compatible cohorts (Youth, Female, Masters) with clear warning banners.

### 6. 📄 Export & Reporting System
- **PDF Report Exporter**: Generates detailed single-session and athlete summary PDF reports displaying `Swimming Stroke: <User Selected>` and `Analysis Reliability`.
- **JSON Data Exports**: Exports structured JSON report, metadata, and frame-by-frame timelines with guaranteed serialization.

---

## 🛠️ System Architecture

```
Swim_Analyzer_AI/
├── analysis/                        # Biomechanical Analysis Engines
│   ├── benchmarks/                  # BenchmarkEngine & percentile math
│   ├── strategies/                  # Stroke-specific strategies (Freestyle, Backstroke, Breaststroke, Butterfly)
│   ├── consistency_validator.py     # Scientific consistency rules
│   ├── pose_detector.py             # MediaPipe PoseLandmarker (Contiguous C-Memory)
│   ├── reliability_engine.py       # Transparent Video Analysis Reliability Engine
│   └── vqa_engine.py                # Video Quality Assessment engine
├── app/                             # Web Application & UI Components
│   ├── streamlit_app.py             # Main Streamlit SaaS application
│   └── ui/                          # Benchmark UI cards & Plotly charts
├── config/                          # Benchmark YAML files & application config
├── models/                          # Dataclasses & Domain Schemas
│   ├── athlete_profile.py           # Athlete Profile schema
│   ├── benchmark_models.py          # Benchmark result schemas
│   └── data_models.py               # StrokeSelection, AnalysisResult, ReliabilityResult
├── services/                        # Service Layer
│   ├── analysis_service.py          # Video analysis orchestrator (User selected stroke)
│   ├── athlete_service.py           # Athlete roster service
│   ├── export_service.py            # JSON report exporter
│   ├── pdf_report_service.py        # FPDF report generator
│   └── scientific_evidence_service.py# Citation formatter
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

### 2. Launching Web App
```bash
venv\Scripts\streamlit run app/streamlit_app.py
```
Open `http://localhost:8501`. Default login: `coach1` / `password123`.

---

## 🧪 Automated Testing

Run the full test suite:
```bash
venv\Scripts\python -m pytest tests/ -v
```
Run user stroke selection and reliability tests:
```bash
venv\Scripts\python -m pytest tests/test_user_stroke_selection_and_reliability.py -v
```