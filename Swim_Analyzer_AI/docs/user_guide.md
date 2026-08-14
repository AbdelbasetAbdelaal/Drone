# SwimAnalyzer AI — Complete User Guide & Feature Manual

Welcome to **SwimAnalyzer AI**, an advanced sports analytics platform designed to provide evidence-based, scientifically validated swimming technique analysis.

---

## 📌 Table of Contents
1. [Getting Started & Login](#1-getting-started--login)
2. [Video Analysis Workflow](#2-video-analysis-workflow)
3. [Interpreting Analysis Results](#3-interpreting-analysis-results)
4. [Population Benchmarks & Evidence Cards](#4-population-benchmarks--evidence-cards)
5. [Managing Athlete Rosters](#5-managing-athlete-rosters)
6. [Session-to-Session Comparison](#6-session-to-session-comparison)
7. [Downloading PDF Reports & Data](#7-downloading-pdf-reports--data)
8. [Scientific Trustworthiness & Safety Rules](#8-scientific-trustworthiness--safety-rules)

---

## 1. Getting Started & Login

### Launching the Web App
Execute the following command in your terminal:
```bash
streamlit run app/streamlit_app.py
```
Open `http://localhost:8501` in your browser.

### Coach Authentication
- Log in using your registered coach credentials.
- **Default Login**: `coach1` / `password123`.
- Logging in isolates your athlete roster and session logs from other coaching staff.

---

## 2. Video Analysis Workflow

1. **Select Navigation**: Click **🏊‍♂️ Video Analysis** from the sidebar menu.
2. **Assign Athlete**: Select an athlete from your roster dropdown or choose **Guest Swimmer**.
3. **Upload Video**: Click **Browse Files** and upload a video file (`.mp4`, `.mov`, `.avi`).
   - *Recommendation*: Use clear side or underwater view footage.
4. **Mandatory Stroke Selection**:
   - In the sidebar dropdown **`Select Swimming Stroke *`**, choose the exact stroke style being performed:
     - 🏊 **`Freestyle`**
     - 🏊 **`Backstroke`**
     - 🏊 **`Breaststroke`**
     - 🏊 **`Butterfly`**
   - *Note*: You must explicitly select a valid stroke. Leaving the option on `-- Select Swimming Stroke --` will display a warning and block processing.
5. **Adjust Settings** (Sidebar):
   - **Effective FPS**: Verified or overridden frame rate.
   - **Visualization Mode**: `User Mode` (clean overlay), `Coach Mode` (detailed metrics overlay), or `Developer Mode` (raw landmark debug metrics).
6. **Analyze**: Click **Analyze Swimming Technique**. The video is processed at 100% full natural FPS without frame dropping.

---

## 3. Interpreting Analysis Results

Analysis results are presented across 6 full-width tabs:

### 📋 Overview Tab
- **Annotated Video**: High-definition video served via high-performance native Streamlit video renderer (`st.video`).
- **Hero Card Badge**: Clearly displays the selected swimming stroke name and icon.
- **Overall Technique Score**: Composite 0–100 technique score.
- **Video Quality Score**: Evaluates resolution, frame rate, camera stability, and lighting.
- **Analysis Confidence & Reliability**: Pose landmark visibility and noise stability ratings.
- **Diagnostic Report Breakdown**: Single-instance expandable breakdown of video quality criteria.

### 🧬 Biomechanics Tab
- **Key Metrics**:
  - **Stroke Rate (spm)**: Arm stroke cycle tempo.
  - **Stroke Length (m)**: Distance per arm cycle.
  - **Kick Frequency (Hz)**: Kick cycle tempo.
  - **Stroke Symmetry (%)**: Bilateral force and velocity symmetry index.
- **Detected Technical Errors**: Lists movement flaws (e.g., *Low Elbow Catch*, *Asymmetrical Pull*, *Excessive Body Roll*) with frame numbers, timestamps, and severity levels.
- **Coaching Feedback & Recommended Drills**: Specific drills tailored to address detected errors.

### 🧊 3D Analysis Tab
- **3D Spatial Metrics**:
  - **3D Body Roll Rotation**: Peak roll angle around the spine axis.
  - **Core Torsion Angle**: Relative twist between shoulders and hips.

---

## 4. Population Benchmarks & Evidence Cards

Navigate to the **📊 Population Benchmarks** tab to view population reference comparisons:

### Demographic Compatibility Guard
- **Valid Population**: Adult Competitive Male Swimmers (Age 18–25).
- **Non-Compatible Athletes** (Female, Youth U10/U13/U17, Masters >35):
  - Displays a warning banner: `"⚠️ No validated reference population is currently available for this athlete's demographic group."`

---

## 5. Managing Athlete Rosters

Click **👥 Athlete Profiles** in the sidebar:
- Add, edit, or search athlete profiles.
- View training history, preferred stroke, age group, and notes.

---

## 6. Session-to-Session Comparison

Click **📊 Session Comparison** in the sidebar:
- Select two sessions for an athlete (e.g., Baseline vs Recent).
- Side-by-side metric comparison chart and flaw resolution report.

---

## 7. Downloading PDF Reports & Data

In the **📥 Downloads** tab:
- Download full session PDF report via `PDFReportService`.
- Export JSON analysis report and metadata.

---

## 8. Scientific Trustworthiness & Safety Rules

- **Deterministic Pipeline**: 100% local Python execution. No LLM hallucinations or uncalibrated scores.
- **No Fabricated Fallbacks**: Values remain `INSUFFICIENT_EVIDENCE` when data is missing or low quality.
