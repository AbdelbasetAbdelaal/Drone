"""
Streamlit Web Application entry point.
Acts purely as the presentation layer.
"""
import sys
import os
from pathlib import Path
import numpy as np

# Add the root directory to PYTHONPATH so that absolute imports work from within streamlit
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from core.config import config
from core.constants import APP_TITLE
from services.analysis_service import AnalysisService
from core.logger import setup_logger

logger = setup_logger(__name__)

def safe_log(msg: str):
    try:
        print(f"[TRACE] {msg}", flush=True)
        logger.info(msg)
    except Exception:
        pass


# --- MODULAR RENDERING FUNCTIONS WITH TRACE LOGGING ---

def render_summary(analysis_result):
    safe_log("[TRACE] ENTER render_summary")
    st.markdown("### Analysis Summary")
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    vqa_score = analysis_result.vqa_result.overall_score if analysis_result.vqa_result else 0
    vqa_class = analysis_result.vqa_result.quality_class if analysis_result.vqa_result else "Unknown"
    
    conf_score = 0.0
    rel_score = 0.0
    if analysis_result.reliability:
        conf_score = analysis_result.reliability.analysis_confidence_score
        rel_score = analysis_result.reliability.analysis_reliability_score
    
    tech_score = analysis_result.report.overall_score if analysis_result.report else 0.0
    tech_score_str = f"{tech_score:.1f}/100" if (tech_score > 0.0 or rel_score >= 50.0) else "N/A"
    
    with summary_col1:
        st.metric("Overall Technique Score", tech_score_str)
    with summary_col2:
        st.metric("Video Quality", f"{vqa_score}/100", delta=vqa_class, delta_color="off")
    with summary_col3:
        st.metric("Analysis Confidence", f"{conf_score:.1f}/100", delta="Pose AI", delta_color="off")
    with summary_col4:
        color = "normal" if rel_score >= 50 else "inverse"
        st.metric("Analysis Reliability", f"{rel_score:.1f}/100", delta="Biomechanics Engine", delta_color=color)
    safe_log("[TRACE] EXIT render_summary")


def render_consistency(analysis_result):
    safe_log("[TRACE] ENTER render_consistency")
    if getattr(analysis_result, 'consistency', None):
        cons = analysis_result.consistency
        with st.expander("Analysis Consistency & Scientific Trustworthiness", expanded=(cons.validation_status != "Passed")):
            cons_col1, cons_col2, cons_col3 = st.columns(3)
            cons_col1.metric("Validation Status", cons.validation_status)
            cons_col2.metric("Scientific Confidence", cons.scientific_confidence)
            cons_col3.metric("Consistency Score", f"{cons.overall_score:.1f}/100")
            
            if cons.warnings:
                for w in cons.warnings:
                    if cons.validation_status == "Critical":
                        st.error(w)
                    else:
                        st.warning(w)
                        
            st.markdown(f"**Passed Rules:** {len(cons.passed_rules)}")
            st.markdown(f"**Failed Rules:** {len(cons.failed_rules)}")
    safe_log("[TRACE] EXIT render_consistency")


def render_video_section(output_video_path, video_render_mode):
    safe_log("[TRACE] ENTER render_video_section")
    st.markdown("#### Annotated Video")

    if video_render_mode == "Disabled (text only)":
        safe_log("[TRACE] ENTER render_video_disabled_mode")
        st.success("Video generated successfully.")
        st.write(output_video_path)
        safe_log("[TRACE] EXIT render_video_disabled_mode")

    elif video_render_mode == "Native Streamlit (st.video)":
        safe_log("[TRACE] ENTER render_video_native_mode")
        try:
            # Read bytes directly — no copy to app/static/ needed.
            # Copying to app/static/ triggers Streamlit's file watcher and crashes the server.
            with open(output_video_path, 'rb') as f:
                video_bytes = f.read()
            st.video(video_bytes)
        except Exception as e:
            st.error(f"Error serving video: {e}")
        safe_log("[TRACE] EXIT render_video_native_mode")

    elif video_render_mode == "HTML5 Streaming Player":
        safe_log("[TRACE] ENTER render_video_html5_mode")
        try:
            # Only for HTML5 mode do we need the static URL
            from utils.video_utils import prepare_static_video
            static_url = prepare_static_video(output_video_path, str(Path(__file__).resolve().parent))
            st.markdown(
                f'''
                <video width="100%" controls style="max-height: 480px; border-radius: 8px; background: #000; width: 100%;">
                    <source src="{static_url}" type="video/mp4">
                    Your browser does not support HTML5 video.
                </video>
                ''',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Error encoding HTML5 video: {e}")
        safe_log("[TRACE] EXIT render_video_html5_mode")

    safe_log("[TRACE] EXIT render_video_section")



def render_download_buttons(output_video_path, json_report_path, metadata_path):
    safe_log("[TRACE] ENTER render_download_buttons")
    with open(output_video_path, 'rb') as video_file:
        video_bytes = video_file.read()
    st.download_button(
        label="Download Processed Video",
        data=video_bytes,
        file_name=Path(output_video_path).name,
        mime="video/mp4"
    )
    
    if json_report_path:
        with open(json_report_path, 'r') as json_file:
            json_str = json_file.read()
        st.download_button(
            label="Download JSON Report",
            data=json_str,
            file_name=Path(json_report_path).name,
            mime="application/json"
        )
        
    if metadata_path:
        with open(metadata_path, 'r') as meta_file:
            meta_str = meta_file.read()
        st.download_button(
            label="Download Metadata JSON",
            data=meta_str,
            file_name=Path(metadata_path).name,
            mime="application/json"
        )
    safe_log("[TRACE] EXIT render_download_buttons")


def render_report_tab(analysis_result):
    safe_log("[TRACE] ENTER render_report_tab")
    if analysis_result.report:
        st.markdown(f"**Feedback:** {analysis_result.report.feedback_summary}")
        
        def format_metric(m_obj, is_length=False):
            if getattr(m_obj, 'is_insufficient_data', False):
                return "Insufficient Data"
            if not m_obj.valid:
                return "N/A"
            val_str = f"{m_obj.value:.2f}" if is_length else f"{m_obj.value:.1f}"
            est_str = " (est)" if getattr(m_obj, 'is_estimated', False) else ""
            return f"{val_str}{est_str}"
            
        st.markdown("##### Key Metrics")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            sr_str = format_metric(analysis_result.report.stroke_rate)
            sym_str = format_metric(analysis_result.report.stroke_symmetry)
            st.metric("Stroke Rate", f"{sr_str}" + (" spm" if "N/A" not in sr_str else ""))
            st.metric("Stroke Symmetry", f"{sym_str}" + ("%" if "N/A" not in sym_str else ""))
        with m_col2:
            sl_str = format_metric(analysis_result.report.stroke_length, is_length=True)
            kf_str = format_metric(analysis_result.report.kick_frequency)
            st.metric("Stroke Length", f"{sl_str}" + (" (rel)" if "N/A" not in sl_str else ""))
            st.metric("Kick Frequency", f"{kf_str}" + (" Hz" if "N/A" not in kf_str else ""))
        
        st.caption("*Legend: (est) = Estimated Value. N/A = Unavailable Value.*")
        
        st.markdown("##### Detected Errors")
        if not analysis_result.report.errors:
            st.success("No significant technique errors detected!")
        else:
            for error in analysis_result.report.errors:
                with st.expander(f"{error.error_type} - {error.severity} Severity (Conf: {getattr(error, 'confidence', 1.0)*100:.0f}%)"):
                    st.write(error.description)
                    st.caption(f"Occurred at frame {error.frame_index} ({error.timestamp_ms / 1000.0:.2f} seconds)")
    else:
        st.info("Performance report not available.")
    safe_log("[TRACE] EXIT render_report_tab")


def render_raw_data_tab(analysis_result):
    safe_log("[TRACE] ENTER render_raw_data_tab")
    import pandas as pd
    
    ts_data = {
        "timestamp_ms": [],
        "left_elbow": [], "right_elbow": [],
        "left_knee": [], "right_knee": [],
        "left_shoulder": [], "right_shoulder": [],
        "body_roll": [], "valid": []
    }
    
    for f in analysis_result.frames:
        ts_data["timestamp_ms"].append(f.timestamp_ms)
        ts_data["left_elbow"].append(f.angles.left_elbow.value if f.angles.left_elbow else np.nan)
        ts_data["right_elbow"].append(f.angles.right_elbow.value if f.angles.right_elbow else np.nan)
        ts_data["left_knee"].append(f.angles.left_knee.value if f.angles.left_knee else np.nan)
        ts_data["right_knee"].append(f.angles.right_knee.value if f.angles.right_knee else np.nan)
        ts_data["left_shoulder"].append(f.angles.left_shoulder.value if f.angles.left_shoulder else np.nan)
        ts_data["right_shoulder"].append(f.angles.right_shoulder.value if f.angles.right_shoulder else np.nan)
        ts_data["body_roll"].append(f.angles.body_roll.value if f.angles.body_roll else np.nan)
        ts_data["valid"].append(f.is_valid)
        
    df = pd.DataFrame(ts_data)
    
    for col in ["left_elbow", "right_elbow", "left_knee", "right_knee", "left_shoulder", "right_shoulder", "body_roll"]:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
    
    if not df.empty:
        df.set_index('timestamp_ms', inplace=True)
        
        st.markdown("##### Valid Frames")
        st.write(f"High confidence frames: {df['valid'].sum()} / {len(df)}")
        
        st.markdown("##### Body Roll Angle")
        safe_log("[TRACE] ENTER body_roll_chart")
        try:
            st.line_chart(df[['body_roll']].dropna(how='all'))
        except Exception as e:
            import traceback
            logger.error(f"Error rendering body_roll chart: {traceback.format_exc()}")
        safe_log("[TRACE] EXIT body_roll_chart")
        
        st.markdown("##### Elbow Joint Angles Over Time")
        safe_log("[TRACE] ENTER elbow_chart")
        try:
            st.line_chart(df[['left_elbow', 'right_elbow']].dropna(how='all'))
        except Exception as e:
            import traceback
            logger.error(f"Error rendering elbows chart: {traceback.format_exc()}")
        safe_log("[TRACE] EXIT elbow_chart")
        
        st.markdown("##### Shoulder Angles Over Time")
        safe_log("[TRACE] ENTER shoulder_chart")
        try:
            st.line_chart(df[['left_shoulder', 'right_shoulder']].dropna(how='all'))
        except Exception as e:
            import traceback
            logger.error(f"Error rendering shoulders chart: {traceback.format_exc()}")
        safe_log("[TRACE] EXIT shoulder_chart")
        
        st.markdown("##### Stroke Phase Summary")
        safe_log("[TRACE] ENTER dataframe_render")
        if analysis_result.stroke_statistics:
            stats = analysis_result.stroke_statistics
            st.write(f"Completed Cycles: {stats.completed_cycles}")
            st.write(f"Avg Cycle Duration: {stats.average_cycle_duration_ms:.1f} ms")
            
            st.markdown("###### Time in Phases (ms)")
            phase_time_df = pd.DataFrame(list(stats.time_in_phases.items()), columns=['Phase', 'Time (ms)'])
            st.dataframe(phase_time_df, width='stretch')
        else:
            phases = [f.stroke_phase for f in analysis_result.frames if f.is_valid]
            phase_df = pd.Series(phases).value_counts().reset_index()
            phase_df.columns = ['Phase', 'Frame Count']
            st.dataframe(phase_df, width='stretch')
        safe_log("[TRACE] EXIT dataframe_render")
        
    else:
        st.info("No biomechanical data was successfully extracted.")
    safe_log("[TRACE] EXIT render_raw_data_tab")


def main():
    safe_log("STREAMLIT APP RERUN")
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title(f"🏊‍♂️ {APP_TITLE}")
    st.markdown("### Professional Swimming Performance Analysis Platform")
    st.markdown("Upload a recorded swimming video to generate a biomechanical analysis overlay.")

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        uploaded_file = st.file_uploader(
            "Upload Swimming Video", 
            type=["mp4", "mov", "avi"]
        )

    if uploaded_file is not None:
        safe_log(f"VIDEO UPLOADED: {uploaded_file.name}")
        st.subheader("Original Video")
        
        # Use a UUID-based filename to guarantee Windows path safety.
        # The original filename (e.g. "WhatsApp Video 2026-07-31 at 11.55.18 AM.mp4")
        # can contain dots and time separators that trigger OSError [Errno 22] on Windows
        # even after regex sanitization.
        import uuid
        from pathlib import Path as _Path
        _original_suffix = _Path(uploaded_file.name).suffix.lower() or ".mp4"
        
        # Use a fingerprint (name + size) to avoid re-writing on every Streamlit rerun
        _upload_fingerprint = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("_upload_fingerprint") != _upload_fingerprint:
            safe_name = f"upload_{uuid.uuid4().hex}{_original_suffix}"
            temp_input_path = config.input_dir / safe_name
            with open(temp_input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state["_upload_fingerprint"] = _upload_fingerprint
            st.session_state["_temp_input_path"] = str(temp_input_path)
        else:
            temp_input_path = _Path(st.session_state["_temp_input_path"])

            
        # Sidebar settings
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Video Settings")
        
        stroke_options = ["Auto Detect", "Freestyle", "Backstroke", "Breaststroke", "Butterfly"]
        selected_stroke = st.sidebar.selectbox("Stroke Type", stroke_options, key="stroke_type_select")
        
        # Read app config
        import yaml
        app_config = {}
        try:
            with open(config.app_config_path, 'r') as f:
                app_config = yaml.safe_load(f)
        except Exception:
            pass
            
        analysis_cfg = app_config.get('analysis', {})
        fps_override = analysis_cfg.get('fps_override')
        
        # Read detected FPS
        from utils.video_utils import get_video_info
        video_info = get_video_info(str(temp_input_path))
        detected_fps = video_info.get("fps", 30.0) if video_info.get("fps", 0) > 0 else 30.0
            
        # Validate FPS bounds
        if not (10 <= detected_fps <= 240):
            st.sidebar.warning(f"Detected FPS ({detected_fps:.1f}) seems unusual. Defaulting to 30.")
            detected_fps = 30.0
            
        default_effective_fps = float(fps_override) if fps_override is not None else float(detected_fps)
        effective_fps = st.sidebar.number_input("Effective FPS", min_value=10.0, max_value=240.0, value=default_effective_fps, step=1.0)
        
        st.sidebar.info(f"Detected FPS: {detected_fps:.2f}")

        st.sidebar.markdown("### Visualization")
        viz_mode = st.sidebar.selectbox("Mode", ["User Mode", "Coach Mode", "Developer Mode"])
        
        trajectory_duration_sec = 2.0
        if viz_mode == "Developer Mode":
            traj_option = st.sidebar.selectbox("Trajectory Length", ["Short (1s)", "Normal (2s)", "Long (4s)"], index=1)
            if traj_option == "Short (1s)":
                trajectory_duration_sec = 1.0
            elif traj_option == "Long (4s)":
                trajectory_duration_sec = 4.0
            forced_conf_input = st.sidebar.number_input("Force Stroke Conf (Dev)", min_value=0.0, max_value=1.0, value=1.0, step=0.1)

        # Developer setting for Video Renderer
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Developer Settings")
        video_render_mode = st.sidebar.selectbox(
            "Video Renderer", 
            ["Native Streamlit (st.video)", "HTML5 Streaming Player", "Disabled (text only)"],
            index=0
        )

        if "analysis_state" not in st.session_state:
            st.session_state.analysis_state = "ready"
        if "stroke_result" not in st.session_state:
            st.session_state.stroke_result = None
        if "completed_analysis" not in st.session_state:
            st.session_state.completed_analysis = None

        if st.sidebar.button("Analyze Swimming Technique", type="primary"):
            st.session_state.analysis_state = "checking_stroke"
            st.session_state.stroke_result = None
            st.session_state.completed_analysis = None

        if st.session_state.analysis_state == "checking_stroke":
            with st.spinner("Analyzing stroke type..."):
                from analysis.stroke_classifier import StrokeClassifier
                from models.data_models import StrokeType
                
                classifier = StrokeClassifier()
                forced_conf = forced_conf_input if viz_mode == "Developer Mode" and forced_conf_input < 1.0 else None
                result = classifier.predict(str(temp_input_path), max_frames=60, forced_confidence=forced_conf)
                
                if selected_stroke == "Auto Detect":
                    result.selected_stroke = StrokeType.AUTO_DETECT
                    if result.confidence < 0.80:
                        st.session_state.stroke_result = result
                        st.session_state.analysis_state = "needs_override"
                    else:
                        result.selected_stroke = result.predicted_stroke
                        result.manual_override = False
                        st.session_state.stroke_result = result
                        st.session_state.analysis_state = "processing"
                else:
                    result.selected_stroke = StrokeType(selected_stroke)
                    result.manual_override = True
                    if result.predicted_stroke != result.selected_stroke:
                        result.is_inconsistent = True
                        st.session_state.stroke_result = result
                        st.session_state.analysis_state = "inconsistent_warning"
                    else:
                        st.session_state.stroke_result = result
                        st.session_state.analysis_state = "processing"
            st.rerun()

        if st.session_state.analysis_state == "needs_override":
            st.warning("We are not confident about the detected swimming style.")
            st.write(f"Predicted: {st.session_state.stroke_result.predicted_stroke.value} (Confidence: {st.session_state.stroke_result.confidence*100:.1f}%)")
            from models.data_models import StrokeType
            override_choice = st.selectbox("Please confirm the stroke type:", ["Freestyle", "Backstroke", "Breaststroke", "Butterfly"])
            if st.button("Confirm Stroke & Analyze"):
                st.session_state.stroke_result.selected_stroke = StrokeType(override_choice)
                st.session_state.stroke_result.manual_override = True
                st.session_state.analysis_state = "processing"
                st.rerun()
                
        if st.session_state.analysis_state == "inconsistent_warning":
            st.warning("The selected stroke type appears inconsistent with the detected motion.")
            st.write(f"You selected: {st.session_state.stroke_result.selected_stroke.value}. The AI detected: {st.session_state.stroke_result.predicted_stroke.value}.")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Continue Anyway"):
                    st.session_state.analysis_state = "processing"
                    st.rerun()
            with col_b:
                if st.button("Cancel"):
                    st.session_state.analysis_state = "ready"
                    st.rerun()

        # Run Video Processing if required
        if st.session_state.analysis_state == "processing" and st.session_state.completed_analysis is None:
            st.markdown("---")
            st.subheader("Analysis Processing")
            
            debug_placeholder = st.empty()
            progress_bar = st.progress(0, text="Starting analysis...")
            progress_status = st.empty()
            
            # Get total frame count upfront for the progress bar
            from utils.video_utils import get_video_info
            _vinfo = get_video_info(str(temp_input_path))
            _total_frames = int(_vinfo.get("frame_count", 0))
            
            def debug_callback(frame_data, confidence, mode):
                idx = frame_data.frame_index
                # Update progress bar every 10 frames to reduce overhead
                if idx % 10 == 0:
                    if _total_frames > 0:
                        pct = min(int((idx / _total_frames) * 100), 99)
                        progress_bar.progress(pct, text=f"Processing frame {idx}/{_total_frames} ({pct}%)...")
                    else:
                        progress_status.markdown(f"⏳ Processing frame **{idx}**...")
                if mode == "Developer Mode":
                    with debug_placeholder.container():
                        cols = st.columns(6)
                        cols[0].metric("Frame", idx)
                        cols[1].metric("Time (ms)", frame_data.timestamp_ms)
                        cols[2].metric("Phase", frame_data.stroke_phase)
                        cols[3].metric("Conf", f"{confidence:.2f}")
                        
                        if frame_data.angles.left_elbow and frame_data.angles.left_elbow.valid:
                            cols[4].metric("L. Elbow", f"{frame_data.angles.left_elbow.value:.1f}")
                        if frame_data.angles.right_elbow and frame_data.angles.right_elbow.valid:
                            cols[5].metric("R. Elbow", f"{frame_data.angles.right_elbow.value:.1f}")
            
            vqa_placeholder = st.empty()
            def vqa_callback(vqa_result):
                with vqa_placeholder.container():
                    if vqa_result.quality_class == "Critical":
                        st.error(vqa_result.warning_message)
                    elif vqa_result.quality_class == "Poor":
                        st.warning(vqa_result.warning_message)
                        
                    st.markdown(f"**Video Quality Score:** {vqa_result.overall_score}/100 ({vqa_result.quality_class})")
                    st.markdown(f"**Analysis Confidence:** {vqa_result.analysis_confidence}")
                    
                    with st.expander("Diagnostic Report Breakdown"):
                        for crit in vqa_result.criteria:
                            status = "✅ PASS" if crit.passed else "❌ FAIL"
                            st.markdown(f"#### {status} - {crit.name} (Score: {crit.score}, Weight: {crit.weight*100:.0f}%)")
                            if not crit.passed:
                                st.markdown(f"**Why it matters:** {crit.explanation_matters}")
                                st.markdown(f"**Effect on analysis:** {crit.explanation_effect}")
                                st.markdown(f"**Recommendation:** {crit.explanation_fix}")
                            st.markdown("---")
            
            try:
                with st.spinner(f"Analyzing video at {effective_fps} FPS..."):
                    analysis_service = AnalysisService()
                    
                    safe_log("ENTER: process_video")
                    output_video_path, json_report_path, metadata_path, analysis_result = analysis_service.process_video(
                        str(temp_input_path), 
                        effective_fps,
                        visualization_mode=viz_mode,
                        progress_callback=debug_callback,
                        vqa_callback=vqa_callback,
                        trajectory_duration_sec=trajectory_duration_sec,
                        stroke_detection=st.session_state.stroke_result
                    )
                    safe_log("EXIT: process_video")
                    progress_bar.progress(100, text="✅ Analysis complete!")
                    progress_status.empty()
                    
                    # --- Post-analysis quality gates ---
                    # Only abort (st.stop) if the analysis was early-halted with no output.
                    # If we have a real output_video_path, show warnings but ALWAYS display results.
                    if analysis_result.vqa_result and analysis_result.vqa_result.quality_class == "Critical":
                        if not output_video_path:
                            safe_log("EXIT: process_video_aborted_vqa_critical_early_halt")
                            st.error("⛔ Video quality is too poor to analyze. Please upload a clearer video.")
                            st.stop()
                        else:
                            safe_log("WARN: final_vqa_critical_but_results_available")
                            # Warning already shown by vqa_callback — no duplicate needed
                        
                    if getattr(analysis_result, 'consistency', None) and analysis_result.consistency.validation_status == "Critical":
                        safe_log("WARN: consistency_critical_but_results_available")
                        for w in analysis_result.consistency.warnings:
                            st.warning(f"⚠️ Consistency Warning: {w}")

                    st.session_state.completed_analysis = {
                        "output_video_path": output_video_path,
                        "json_report_path": json_report_path,
                        "metadata_path": metadata_path,
                        "analysis_result": analysis_result
                    }
                    st.session_state.analysis_state = "results_ready"
                    st.rerun()

            except Exception as e:
                import traceback
                err_msg = traceback.format_exc()
                logger.error(f"An error occurred during analysis: {str(e)}")
                st.error(f"An error occurred during analysis: {str(e)}\n\n```python\n{err_msg}\n```")

        # Render Completed Analysis Results via Modular Functions
        if st.session_state.completed_analysis is not None:
            try:
                comp = st.session_state.completed_analysis
                output_video_path = comp["output_video_path"]
                json_report_path = comp["json_report_path"]
                metadata_path = comp["metadata_path"]
                analysis_result = comp["analysis_result"]

                st.success("Analysis complete!")
                st.markdown("---")
                
                # 1. Summary
                render_summary(analysis_result)
                
                # 2. Consistency
                render_consistency(analysis_result)
                
                st.markdown("---")

                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # 3. Video Section
                    render_video_section(output_video_path, video_render_mode)
                    
                    # 4. Download Buttons
                    render_download_buttons(output_video_path, json_report_path, metadata_path)
                    
                with col2:
                    st.markdown("#### Biomechanical Insights")
                    tab1, tab2 = st.tabs(["Performance Report", "Raw Data Charts"])
                    
                    with tab1:
                        # 5. Report Tab
                        render_report_tab(analysis_result)
                            
                    with tab2:
                        # 6. Raw Data Tab
                        render_raw_data_tab(analysis_result)
                        
            except Exception as e:
                import traceback
                err_msg = traceback.format_exc()
                logger.error(f"An error occurred during rendering: {str(e)}")
                st.error(f"An error occurred during rendering: {str(e)}\n\n```python\n{err_msg}\n```")


# Standard Streamlit entry point: call main() at module level.
# Do NOT use `if __name__ == "__main__"` — Streamlit re-executes the
# entire script on every rerun, so the guard IS true each time, which
# caused a new heartbeat thread to be spawned on every rerun.
#
# CRITICAL: Do NOT set threading.excepthook here.
# Streamlit uses background threads for WebSocket heartbeats and the
# file watcher. If threading.excepthook is overridden, those threads'
# exceptions bypass Streamlit's own recovery logic, silently killing
# the server without any Python traceback.
main()
