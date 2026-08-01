import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from fpdf import FPDF

from models.athlete_profile import AthleteProfile
from models.analysis_session import AnalysisSession
from core.config import config

class PDFReportService:
    """
    Generates professional PDF reports for an athlete's profile and analysis history.
    """
    def __init__(self):
        self.output_dir = config.data_dir / "pdf_reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_athlete_summary(self, profile: AthleteProfile, history: List[AnalysisSession]) -> str:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        
        # Fonts
        pdf.set_font("Helvetica", style="B", size=24)
        
        # Header
        pdf.set_text_color(31, 119, 180) # Plotly Blue
        pdf.cell(0, 15, "SwimAnalyzer AI - Performance Report", ln=True, align="C")
        
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        
        # Athlete Profile
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(0, 10, "Athlete Profile", ln=True, border="B")
        pdf.ln(5)
        
        pdf.set_font("Helvetica", size=12)
        info_lines = [
            f"Name: {profile.full_name}",
            f"Age: {profile.age} | Gender: {profile.gender}",
            f"Height: {profile.height_cm} cm | Weight: {profile.weight_kg} kg",
            f"Level: {profile.swimming_level} | Stroke: {profile.preferred_stroke}"
        ]
        for line in info_lines:
            pdf.cell(0, 8, line, ln=True)
            
        pdf.ln(10)
        
        # Coach Notes
        if profile.notes:
            pdf.set_font("Helvetica", style="B", size=14)
            pdf.set_text_color(31, 119, 180)
            pdf.cell(0, 10, "Coach Notes", ln=True)
            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 8, profile.notes)
            pdf.ln(5)
            
        # Training Goals
        if profile.training_goals:
            pdf.set_font("Helvetica", style="B", size=14)
            pdf.set_text_color(44, 160, 44) # Green
            pdf.cell(0, 10, "Training Goals", ln=True)
            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 8, profile.training_goals)
            pdf.ln(10)
            
        # History Table
        if history:
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, "Recent Sessions Summary", ln=True, border="B")
            pdf.ln(5)
            
            # Table Header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Helvetica", style="B", size=11)
            col_widths = [45, 45, 30, 40] # 160 total
            # Center the table horizontally (A4 width is 210, margins are 10 on each side)
            start_x = (210 - sum(col_widths)) / 2
            pdf.set_x(start_x)
            
            headers = ["Date", "Stroke", "Score", "Cycles"]
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, border=1, align="C", fill=True)
            pdf.ln()
            
            # Table Data (top 10 sessions)
            pdf.set_font("Helvetica", size=11)
            for s in history[:10]:
                pdf.set_x(start_x)
                date_str = s.analysis_timestamp.replace("T", " ")[:16]
                pdf.cell(col_widths[0], 10, date_str, border=1, align="C")
                pdf.cell(col_widths[1], 10, str(s.stroke_type), border=1, align="C")
                pdf.cell(col_widths[2], 10, f"{s.performance_score:.1f}", border=1, align="C")
                pdf.cell(col_widths[3], 10, str(s.completed_cycles), border=1, align="C")
                pdf.ln()

        # Save PDF
        filename = f"{profile.full_name.replace(' ', '_')}_Report_{uuid.uuid4().hex[:6]}.pdf"
        filepath = self.output_dir / filename
        pdf.output(str(filepath))
        return str(filepath)
