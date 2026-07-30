"""
Streamlit Web Application entry point.
Acts purely as the presentation layer.
"""
import sys
import os
from pathlib import Path

# Add the root directory to PYTHONPATH so that absolute imports work from within streamlit
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from core.config import config
from core.constants import APP_TITLE
from services.analysis_service import AnalysisService

def main():
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
        st.subheader("Original Video")
        
        # Save the uploaded file to disk so OpenCV can process it
        # Streamlit provides the file in memory, but cv2.VideoCapture requires a path.
        temp_input_path = config.input_dir / uploaded_file.name
        with open(temp_input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.video(str(temp_input_path))
        
        if st.button("Analyze Swimming Technique", type="primary"):
            st.markdown("---")
            st.subheader("Analysis Results")
            
            with st.spinner("Analyzing video frame-by-frame using MediaPipe Pose..."):
                try:
                    analysis_service = AnalysisService()
                    # We pass the absolute path of the temporarily saved file to the service
                    output_path, analysis_result = analysis_service.process_video(str(temp_input_path))
                    
                    st.success("Analysis complete!")
                    
                    # Layout: video on left, stats/charts on right
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("#### Annotated Video")
                        st.video(output_path)
                        
                        # Provide download button for the processed video
                        with open(output_path, "rb") as file:
                            st.download_button(
                                label="Download Processed Video",
                                data=file,
                                file_name=f"analyzed_{uploaded_file.name}",
                                mime="video/mp4"
                            )
                            
                    with col2:
                        st.markdown("#### Biomechanical Insights")
                        
                        # Use tabs for different insights
                        tab1, tab2 = st.tabs(["Performance Report", "Raw Data Charts"])
                        
                        with tab1:
                            if analysis_result.report:
                                score = analysis_result.report.overall_score
                                
                                # Score styling based on value
                                color = "normal"
                                if score >= 90:
                                    color = "inverse"
                                elif score < 70:
                                    color = "off"
                                    
                                st.metric(label="Overall Technique Score", value=f"{score:.1f}/100", delta_color=color)
                                st.markdown(f"**Feedback:** {analysis_result.report.feedback_summary}")
                                
                                st.markdown("##### Detected Errors")
                                if not analysis_result.report.errors:
                                    st.success("No significant technique errors detected!")
                                else:
                                    for error in analysis_result.report.errors:
                                        with st.expander(f"{error.error_type} - {error.severity} Severity"):
                                            st.write(error.description)
                                            st.caption(f"Occurred at {error.timestamp_ms / 1000.0:.2f} seconds")
                            else:
                                st.info("Performance report not available.")
                                
                        with tab2:
                            import pandas as pd
                            
                            # Process timeseries data
                            ts_data = analysis_result.get_angles_timeseries()
                            df = pd.DataFrame(ts_data)
                            
                            if not df.empty:
                                df.set_index('timestamp_ms', inplace=True)
                                
                                st.markdown("##### Elbow Joint Angles Over Time")
                                st.line_chart(df[['left_elbow', 'right_elbow']])
                                
                                st.markdown("##### Knee Joint Angles Over Time")
                                st.line_chart(df[['left_knee', 'right_knee']])
                                
                                st.markdown("##### Stroke Phase Summary")
                                # Simple count of phases for this generic implementation
                                phases = [f.stroke_phase for f in analysis_result.frames]
                                phase_df = pd.Series(phases).value_counts().reset_index()
                                phase_df.columns = ['Phase', 'Frame Count']
                                st.dataframe(phase_df, use_container_width=True)
                                
                            else:
                                st.info("No biomechanical data was successfully extracted.")
                            
                except Exception as e:
                    import traceback
                    err_msg = traceback.format_exc()
                    st.error(f"An error occurred during analysis: {str(e)}\n\n```python\n{err_msg}\n```")

if __name__ == "__main__":
    main()
