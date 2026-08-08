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
   - *Recommendation*: Use 60 FPS or higher camera footage with clear side or underwater view.
4. **Select Stroke**:
   - Choose **Auto Detect** to let the AI classify the stroke style (Freestyle, Backstroke, Breaststroke, Butterfly).
   - Or manually select the stroke type.
5. **Adjust Settings** (Sidebar):
   - **Effective FPS**: Verified or overridden frame rate.
   - **Visualization Mode**: `User Mode` (clean overlay), `Coach Mode` (detailed metrics overlay), or `Developer Mode` (raw landmark debug metrics).
6. **Analyze**: Click **Analyze Swimming Technique**.

---

## 3. Interpreting Analysis Results

Analysis results are presented across 6 full-width tabs:

### 📋 Overview Tab
- **Annotated Video**: High-definition video with skeleton pose tracking and stroke cycle phase indicators.
- **Overall Technique Score**: Composite 0–100 technique score.
- **Video Quality Score**: Evaluates resolution, frame rate, camera stability, and lighting.
- **Analysis Confidence & Reliability**: Pose landmark visibility and noise stability ratings.
- **Consistency Rules**: Evaluates 7 mathematical rules to detect potential analysis contradictions.

### 🧬 Biomechanics Tab
- **Key Metrics**:
  - **Stroke Rate (spm)**: Arm stroke cycle tempo.
  - **Stroke Length (m)**: Distance per arm cycle.
  - **Kick Frequency (Hz)**: Kick cycle tempo.
  - **Stroke Symmetry (%)**: Bilateral force and velocity symmetry index.
- **Detected Technical Errors**: Lists movement flaws (e.g., *Low Elbow Catch*, *Asymmetrical Pull*, *Excessive Body Roll*) with frame numbers, timestamps, and severity levels.
- **Coaching Feedback & Recommended Drills**: Specific drills tailored to address detected errors.

---

## 4. Population Benchmarks & Evidence Cards

Navigate to the **📊 Population Benchmarks** tab to view population reference comparisons:

### Demographic Compatibility Guard
- **Valid Population**: Adult Competitive Male Swimmers (Age 18–25).
- **Non-Compatible Athletes** (Female, Youth U10/U13/U17, Masters >35):
  - Displays a warning banner: `"⚠️ No validated reference population is currently available for this athlete's demographic group."`
  - Raw measurements and reference means are displayed for context, but **misleading Z-scores and Percentiles are strictly suppressed**.

### Population Cards & Badges
Each metric card displays:
- **Athlete Value** vs **Scientific Reference Mean & Unit**
- **Evidence Status Badge**:
  - `✓ SCIENTIFICALLY ACCEPTED` (Green)
  - `⚠ REFERENCE ONLY` (Yellow)
  - `⚠ INSUFFICIENT EVIDENCE` (Orange)
  - `✕ REJECTED` (Red)
- **Citation & Relationship**: Shows author/year and whether the metric is `Directly supported` or `Derived from source`.

### 🔬 Scientific Evidence Drawer
Click **🔬 Scientific Evidence & Provenance Details** to expand:
- Publication title, authors, year, journal, DOI.
- Sample size ($N$), original measurement, original unit.
- Converted derived value and conversion formula (e.g. `0.90 Hz * 60 = 54.0 spm`).
- Exact table and page number references in the published paper.

---

## 5. Managing Athlete Rosters

Navigate to **👥 Athletes**:
- **Directory Tab**: View all athletes in your roster, swimming level, preferred stroke, age, height, and weight.
- **Create New Athlete Tab**: Add new athlete profiles with training goals and notes.
- **Athlete Profile View**:
  - Longitudinal performance progression graphs (Plotly).
  - Recorded session logs table.
  - One-click **📄 Download PDF Report** for the athlete's complete history.

---

## 6. Session-to-Session Comparison

Navigate to **📜 History** or an Athlete Profile page:
1. Select **Session A (Baseline)** and **Session B (Recent)**.
2. Click **Generate Comparison Report**.
3. View:
   - Overall score delta and confidence progression.
   - Specific metric deltas (e.g. `+0.12 m` stroke length, `-2.5 spm` stroke rate).
   - **Resolved Errors** (green), **New Errors** (red), and **Persistent Errors** (yellow).

---

## 7. Downloading PDF Reports & Data

In the **📥 Downloads** tab or Athlete Profile header:
- **📄 Download Detailed PDF Report**: Professional PDF report containing executive summary, key metrics, consistency rules, population benchmarks, and scientific literature citations (`PDFReportService`).
- **Download Processed Video**: MP4 annotated video file.
- **Download JSON Report**: Raw structured analysis data for programmatic export.

---

## 8. Scientific Trustworthiness & Safety Rules

SwimAnalyzer AI operates under strict scientific invariants:
1. **Zero Guessed Benchmarks**: Every accepted benchmark comes from a verified paper table/page.
2. **Demographic Guard**: Adult male data is never silently applied to female, youth, or masters swimmers.
3. **Derived Conversion Traceability**: Unit conversions (Hz to spm) preserve original values and explicit conversion formulas.
4. **Definition Matching Guard**: Measurements with definition mismatches (e.g. Body Roll 3D vector vs shoulder roll) are downgraded to `REFERENCE_ONLY`.
5. **Proprietary Score Isolation**: The 0–100 composite score is explicitly tagged as a proprietary index and excluded from scientific benchmark totals.
