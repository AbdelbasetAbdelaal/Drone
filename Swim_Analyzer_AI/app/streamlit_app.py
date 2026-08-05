"""
Streamlit Web Application entry point.
Acts purely as the presentation layer.
"""
import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd

# Add the root directory to PYTHONPATH so that absolute imports work from within streamlit
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.ui.charts import create_performance_trend_chart, create_cycles_trend_chart
from app.ui.dashboard import render_dashboard_page
import streamlit as st
from core.config import config
from core.constants import APP_TITLE
from services.analysis_service import AnalysisService
from services.athlete_service import AthleteService
from services.analysis_history_service import AnalysisHistoryService
from services.comparison_service import ComparisonService
from services.pdf_report_service import PDFReportService
from models.athlete_profile import AthleteProfile
from models.analysis_session import AnalysisSession
from models.comparison_models import ComparisonReport
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
    
    # --- Detected Stroke Badge ---
    stroke_icons = {
        "Freestyle": "🏊",
        "Backstroke": "🔄",
        "Breaststroke": "🐸",
        "Butterfly": "🦋",
        "Auto Detect": "🔍",
    }
    stroke_result = getattr(st.session_state, 'stroke_result', None)
    if stroke_result and hasattr(stroke_result, 'selected_stroke'):
        stroke_name = stroke_result.selected_stroke.value.title()
        icon = stroke_icons.get(stroke_name, "🏊")
        st.markdown(
            f"""<div style="display:inline-block; background:linear-gradient(135deg,#0055FF,#00F0FF);
            color:white; padding:6px 18px; border-radius:20px; font-size:1rem;
            font-weight:700; letter-spacing:1px; margin-bottom:12px;">
            {icon} Detected Stroke: {stroke_name}
            </div>""",
            unsafe_allow_html=True
        )
    
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

def render_athletes_page():
    st.title("👥 Athletes")
    st.markdown("Create and manage athlete profiles for longitudinal tracking and personalized analysis.")
    
    athlete_service = AthleteService()
    profiles = athlete_service.get_all_profiles()
    
    tab1, tab2 = st.tabs(["Athlete Directory", "Create New Athlete"])
    
    with tab1:
        if not profiles:
            st.info("No athlete profiles found. Create one in the next tab.")
        else:
            for p in profiles:
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"### 👤 {p.full_name}")
                        st.markdown(f"**Level:** {p.swimming_level} | **Stroke:** {p.preferred_stroke}")
                    with col_btn:
                        if st.button("View Profile", key=f"view_{p.athlete_id}", width="stretch"):
                            st.session_state.viewing_athlete_id = p.athlete_id
                            st.rerun()

    with tab2:
        with st.form("create_athlete_form"):
            st.subheader("New Athlete Profile")
            full_name = st.text_input("Full Name *")
            
            col1, col2 = st.columns(2)
            age = col1.number_input("Age *", min_value=1, max_value=150, value=25)
            gender = col2.selectbox("Gender *", ["Male", "Female", "Other"])
            
            col3, col4 = st.columns(2)
            height = col3.number_input("Height (cm) *", min_value=50.0, max_value=300.0, value=175.0)
            weight = col4.number_input("Weight (kg) *", min_value=20.0, max_value=200.0, value=70.0)
            
            col5, col6 = st.columns(2)
            level = col5.selectbox("Swimming Level *", ["Beginner", "Intermediate", "Advanced", "Elite"])
            stroke = col6.selectbox("Preferred Stroke *", ["Freestyle", "Backstroke", "Breaststroke", "Butterfly"])
            
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Create Profile")
            if submitted:
                if not full_name.strip():
                    st.error("Full Name is required.")
                else:
                    existing_profiles = athlete_service.get_all_profiles()
                    name_exists = any(p.full_name.lower() == full_name.strip().lower() for p in existing_profiles)
                    if name_exists:
                        st.error(f"An athlete with the name '{full_name.strip()}' already exists. Please use a unique name.")
                    else:
                        athlete_service.create_profile(
                            full_name=full_name.strip(),
                            age=age,
                            gender=gender,
                            height_cm=height,
                            weight_kg=weight,
                            swimming_level=level,
                            preferred_stroke=stroke,
                            notes=notes
                        )
                        st.success(f"Athlete profile for '{full_name}' created successfully!")
                        st.rerun()

def render_athlete_profile_page():
    athlete_id = st.session_state.viewing_athlete_id
    athlete_service = AthleteService()
    profile = athlete_service.load_profile(athlete_id)
    
    if not profile:
        st.error("Athlete profile not found.")
        st.session_state.viewing_athlete_id = None
        st.rerun()
        return

    col1, col2, col3 = st.columns([1, 7, 3])
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.viewing_athlete_id = None
            st.rerun()
    with col2:
        st.title(f"🏊 {profile.full_name}")
    with col3:
        st.write("") # Spacing
        history_service = AnalysisHistoryService()
        history = history_service.get_sessions_by_athlete(athlete_id)
        
        # Generate PDF on the fly
        try:
            pdf_service = PDFReportService()
            pdf_path = pdf_service.generate_athlete_summary(profile, history)
            with open(pdf_path, "rb") as pdf_file:
                PDFbyte = pdf_file.read()
            st.download_button(
                label="📄 Download PDF Report",
                data=PDFbyte,
                file_name=os.path.basename(pdf_path),
                mime='application/pdf',
                type="primary",
                width="stretch"
            )
        except Exception as e:
            st.error(f"PDF Error: {e}")
    
    st.markdown(f"**Level:** {profile.swimming_level} | **Preferred Stroke:** {profile.preferred_stroke}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Age", f"{profile.age} yrs")
    c2.metric("Gender", profile.gender)
    c3.metric("Height", f"{profile.height_cm} cm")
    c4.metric("Weight", f"{profile.weight_kg} kg")
    
    st.markdown("---")
    st.subheader("🎯 Coach Notes & Goals")
    
    with st.expander("📝 Edit Notes & Goals", expanded=False):
        with st.form("edit_notes_form"):
            new_notes = st.text_area("Coach Notes", value=profile.notes, height=100)
            new_goals = st.text_area("Training Goals (Short/Long term)", value=profile.training_goals, height=100)
            
            if st.form_submit_button("Save Notes", type="primary"):
                profile.notes = new_notes
                profile.training_goals = new_goals
                if athlete_service.save_profile(profile):
                    st.success("Notes and goals updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save. Check logs.")
                    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if profile.notes:
            st.info(f"**Notes:**\n\n{profile.notes}")
        else:
            st.caption("No notes recorded.")
    with col_n2:
        if profile.training_goals:
            st.success(f"**Training Goals:**\n\n{profile.training_goals}")
        else:
            st.caption("No training goals set.")
        
    st.markdown("---")
    st.subheader("📊 Analysis History")
    
    history_service = AnalysisHistoryService()
    history = history_service.get_sessions_by_athlete(athlete_id)
    
    if not history:
        st.info("No analyses recorded for this athlete yet.")
    else:
        history_data = []
        for s in history:
            history_data.append({
                "Date": s.analysis_timestamp.split("T")[0],
                "Time": s.analysis_timestamp.split("T")[1][:5],
                "Score": round(s.performance_score, 1),
                "Confidence": s.scientific_confidence,
                "Stroke": s.stroke_type,
                "Cycles": s.completed_cycles,
                "Proc. Time (s)": round(s.processing_time_seconds, 1)
            })
        
        if len(history) >= 2:
            st.markdown("### 📈 Performance Progression")
            df = pd.DataFrame(history_data)
            
            c_trend1, c_trend2 = st.columns(2)
            with c_trend1:
                st.plotly_chart(create_performance_trend_chart(df), width="stretch")
            with c_trend2:
                st.plotly_chart(create_cycles_trend_chart(df), width="stretch")
            st.markdown("---")
            
        st.dataframe(history_data, width="stretch")
        
        # --- PHASE 7: Session Comparison ---
        if len(history) >= 2:
            st.markdown("---")
            st.subheader("⚖️ Compare Sessions")
            st.markdown("Select two sessions below to visualize technique changes and performance progression.")
            
            # Create a dictionary to map a friendly display string to the session object
            session_options = {}
            for i, s in enumerate(history):
                # Using index to ensure uniqueness if timestamp is identical
                date_str = s.analysis_timestamp.split("T")[0]
                time_str = s.analysis_timestamp.split("T")[1][:5]
                label = f"{date_str} {time_str} | Score: {s.performance_score:.1f} | {s.stroke_type} ({i})"
                session_options[label] = s
                
            col_sel_a, col_sel_b = st.columns(2)
            options_list = list(session_options.keys())
            
            with col_sel_a:
                sel_a_label = st.selectbox("Select Session A (Baseline)", options=options_list, index=len(options_list)-1)
            with col_sel_b:
                sel_b_label = st.selectbox("Select Session B (Recent)", options=options_list, index=0)
                
            if st.button("Generate Comparison Report", type="primary"):
                sess_a = session_options[sel_a_label]
                sess_b = session_options[sel_b_label]
                
                comp_service = ComparisonService()
                report = comp_service.compare_sessions(sess_a, sess_b)
                
                st.markdown("### Comparison Results")
                
                # Render Coach Summary if present
                if report.coach_summary:
                    st.info(f"**Coach Summary:** {report.coach_summary}")
                
                # Render Metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                if report.overall_score_delta:
                    col_m1.metric("Overall Score", 
                                  f"{report.overall_score_delta.new_value:.1f}", 
                                  f"{report.overall_score_delta.delta:.1f}")
                                  
                if report.confidence_delta:
                    color = "normal" if report.confidence_delta.is_improvement else "inverse"
                    if report.confidence_delta.delta == 0: color = "off"
                    col_m2.metric("Scientific Confidence", 
                                  report.confidence_delta.new_label, 
                                  f"{report.confidence_delta.delta} levels", delta_color=color)
                                  
                if report.cycles_delta:
                    col_m3.metric("Completed Cycles", 
                                  f"{int(report.cycles_delta.new_value)}", 
                                  f"{int(report.cycles_delta.delta)}")
                                  
                if report.cycle_duration_delta:
                    # Note: for duration, negative is usually better, which is_improvement handles conceptually,
                    # but Streamlit native metric interprets negative delta as red by default unless inverse.
                    # We'll let Streamlit default behavior work: negative time = red (bad) wait, inverse is better.
                    col_m4.metric("Avg Cycle Duration", 
                                  f"{report.cycle_duration_delta.new_value:.0f} ms", 
                                  f"{report.cycle_duration_delta.delta:.0f} ms", delta_color="inverse")
                                  
                # Technique Deltas
                if report.technique_deltas:
                    st.markdown("#### Technique Metrics")
                    tech_cols = st.columns(len(report.technique_deltas))
                    for i, t_delta in enumerate(report.technique_deltas):
                        with tech_cols[i]:
                            st.metric(t_delta.metric_name, 
                                      f"{t_delta.new_value:.2f} {t_delta.unit}".strip(), 
                                      f"{t_delta.delta:.2f} {t_delta.unit}".strip())
                                      
                # Movement Errors
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    st.markdown("🟢 **Resolved Errors**")
                    if report.resolved_errors:
                        for e in report.resolved_errors: st.markdown(f"- {e}")
                    else: st.caption("None")
                with col_e2:
                    st.markdown("🔴 **New Errors**")
                    if report.new_errors:
                        for e in report.new_errors: st.markdown(f"- {e}")
                    else: st.caption("None")
                with col_e3:
                    st.markdown("🟡 **Persistent Errors**")
                    if report.persistent_errors:
                        for e in report.persistent_errors: st.markdown(f"- {e}")
                    else: st.caption("None")
                    
                # Video Side-by-Side
                if report.video_path_a and report.video_path_b:
                    st.markdown("#### Video Comparison 🔗")
                    vid_col1, vid_col2 = st.columns(2)
                    try:
                        # Construct absolute paths
                        video_a_full = config.output_dir / report.video_path_a
                        video_b_full = config.output_dir / report.video_path_b
                        
                        with vid_col1:
                            st.markdown(f"**Session A:** {sel_a_label}")
                            if video_a_full.exists():
                                with open(video_a_full, 'rb') as f1: st.video(f1.read())
                            else:
                                st.warning("Video file missing.")
                        with vid_col2:
                            st.markdown(f"**Session B:** {sel_b_label}")
                            if video_b_full.exists():
                                with open(video_b_full, 'rb') as f2: st.video(f2.read())
                            else:
                                st.warning("Video file missing.")
                    except Exception as e:
                        st.warning(f"Could not load comparison videos: {e}")
        
    st.markdown("---")
    # Quick Actions
    with st.expander("⚙️ Advanced Settings"):
        if st.button("Delete Athlete", type="primary", key="del_from_profile"):
            athlete_service.delete_profile(athlete_id)
            st.session_state.viewing_athlete_id = None
            st.rerun()


def render_history_page():
    st.title("📊 Analysis History")
    st.markdown("Review historical analysis sessions across all athletes.")

    history_service = AnalysisHistoryService()
    athlete_service = AthleteService()
    
    all_sessions = history_service.get_all_sessions()
    
    if not all_sessions:
        st.info("No analysis history recorded yet.")
        return

    # Fetch athletes to map names
    profiles = athlete_service.get_all_profiles()
    athlete_map = {p.athlete_id: p.full_name for p in profiles}

    history_data = []
    for s in all_sessions:
        athlete_name = athlete_map.get(s.athlete_id, "Guest Session") if s.athlete_id else "Guest Session"
        history_data.append({
            "Date": s.analysis_timestamp.split("T")[0],
            "Time": s.analysis_timestamp.split("T")[1][:5],
            "Athlete": athlete_name,
            "Score": round(s.performance_score, 1),
            "Confidence": s.scientific_confidence,
            "Stroke": s.stroke_type,
            "Cycles": s.completed_cycles,
            "Proc. Time (s)": round(s.processing_time_seconds, 1)
        })
        
    st.dataframe(history_data, width="stretch")


def main():
    safe_log("STREAMLIT APP RERUN")
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "viewing_athlete_id" not in st.session_state:
        st.session_state.viewing_athlete_id = None

    # --- Navigation ---
    st.sidebar.markdown("### Navigation")
    app_mode = st.sidebar.radio("Go to:", ["📊 Coach Dashboard", "🏊‍♂️ Analysis Dashboard", "👥 Athletes", "📉 Analysis History"], label_visibility="collapsed")
    st.sidebar.markdown("---")
    
    if app_mode == "📊 Coach Dashboard":
        render_dashboard_page()
        return
    elif app_mode == "👥 Athletes":
        if st.session_state.viewing_athlete_id:
            render_athlete_profile_page()
        else:
            render_athletes_page()
        return
    elif app_mode == "📉 Analysis History":
        render_history_page()
        return

    st.title(f"🏊‍♂️ {APP_TITLE}")
    st.markdown("### Professional Swimming Performance Analysis Platform")
    st.markdown("Upload a recorded swimming video to generate a biomechanical analysis overlay.")

    # Sidebar: Current Athlete
    st.sidebar.markdown("### Current Athlete")
    athlete_service = AthleteService()
    profiles = athlete_service.get_all_profiles()
    
    athlete_options = {"None": "Guest Session"}
    for p in profiles:
        athlete_options[p.athlete_id] = f"{p.full_name} ({p.swimming_level})"
        
    selected_athlete_id = st.sidebar.selectbox(
        "Select Profile", 
        options=list(athlete_options.keys()), 
        format_func=lambda x: athlete_options[x],
        label_visibility="collapsed"
    )
    st.sidebar.markdown("---")

    # Main UI: Athlete Summary Card
    if selected_athlete_id == "None":
        st.info("ℹ️ **Guest Session:** Analysis will not be linked to an athlete profile.")
    else:
        # Find the selected profile
        selected_profile = next((p for p in profiles if p.athlete_id == selected_athlete_id), None)
        if selected_profile:
            with st.container(border=True):
                st.markdown(f"#### 👤 Active Athlete: {selected_profile.full_name}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Age", selected_profile.age)
                col2.metric("Height", f"{selected_profile.height_cm} cm")
                col3.metric("Level", selected_profile.swimming_level)
                col4.metric("Preferred Stroke", selected_profile.preferred_stroke)

    # Sidebar: Video Upload
    st.sidebar.markdown("### Video Upload")
    uploaded_file = st.sidebar.file_uploader(
            "Upload Swimming Video", 
        type=["mp4", "mov", "avi"],
        label_visibility="collapsed"
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
            import time
            st.session_state["_processing_start_time"] = time.time()
            st.session_state.stroke_result = None
            st.session_state.completed_analysis = None
            st.rerun()

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
                        stroke_detection=st.session_state.stroke_result,
                        athlete_id=selected_athlete_id if selected_athlete_id != "None" else None
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

                    # Automatically save Analysis History session
                    try:
                        import time
                        from datetime import datetime
                        history_service = AnalysisHistoryService()
                        session = AnalysisSession(
                            athlete_id=selected_athlete_id if selected_athlete_id != "None" else None,
                            analysis_timestamp=datetime.now().isoformat(),
                            original_video_filename=uploaded_file.name,
                            processed_video_filename=Path(output_video_path).name if output_video_path else "",
                            metadata_json_path=str(metadata_path),
                            report_json_path=str(json_report_path),
                            performance_score=analysis_result.report.overall_score if analysis_result.report else 0.0,
                            scientific_confidence=analysis_result.consistency.scientific_confidence if getattr(analysis_result, 'consistency', None) else "Low",
                            completed_cycles=analysis_result.stroke_statistics.completed_cycles if analysis_result.stroke_statistics else 0,
                            stroke_type=st.session_state.stroke_result.selected_stroke.value,
                            processing_time_seconds=st.session_state.get("_processing_end_time", time.time()) - st.session_state.get("_processing_start_time", time.time())
                        )
                        history_service.save_session(session)
                    except Exception as e:
                        safe_log(f"ERROR: Failed to save analysis history: {e}")

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
