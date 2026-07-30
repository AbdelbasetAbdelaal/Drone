# SwimAnalyzer AI

Professional AI-powered swimming performance analysis platform.

## Overview
This application uses MediaPipe Pose to analyze recorded swimming videos, extracting body landmarks and overlaying a generated skeleton. It features a Streamlit-based web UI and follows Clean Architecture principles for maximum maintainability and extensibility.

## Features (Phase 1)
- Upload swimming videos via web UI
- Process video frame-by-frame with MediaPipe Pose
- Draw skeleton overlays on the swimmer
- Save and display the processed video

## Architecture
- **app/**: Streamlit presentation layer
- **services/**: Application orchestration
- **analysis/**: Core domain logic (Pose estimation)
- **utils/**: Infrastructure and helpers (OpenCV video processing)
- **core/**: Configurations, constants, and logging

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit application:
```bash
streamlit run app/streamlit_app.py
```
