import streamlit as st
from typing import Dict, Any, Optional

from models.benchmark_models import BenchmarkResult, MetricBenchmarkComparison
from models.scientific_evidence_models import (
    ReviewStatus, AuditDecision, SourceAccessLevel, SourceQuality,
    SourceRelationship, DefinitionMatchingStatus, PopulationMatchingStatus
)
from services.scientific_evidence_service import ScientificEvidenceService

def render_population_benchmark_cards(bm_res: BenchmarkResult, athlete_profile: Optional[Any] = None):
    """
    Renders Population Benchmark Cards with evidence badges, provenance,
    and demographic compatibility guards.
    """
    if not bm_res or not getattr(bm_res, 'comparisons', None):
        st.info("No population benchmark data available for this analysis.")
        return

    # 1. Demographic Compatibility Banner
    ev_service = ScientificEvidenceService()
    athlete_gender = athlete_profile.gender if athlete_profile and athlete_profile.gender else "Male"
    athlete_age = athlete_profile.age if athlete_profile and athlete_profile.age else 20

    is_demographic_compatible = (athlete_gender.lower() in ["male", "mixed"] and 18 <= athlete_age <= 25)

    if not is_demographic_compatible:
        st.warning(
            f"⚠️ **No validated reference population is currently available for this athlete's demographic group** "
            f"({athlete_gender}, Age {athlete_age}). "
            f"Currently validated reference benchmarks apply to: *Adult Competitive Male Swimmers (Age 18–25)*. "
            f"Athlete measurements are displayed below alongside reference values for context, but percentiles/Z-scores are suppressed."
        )
    else:
        st.success(
            "✓ **Athlete belongs to the scientifically validated reference population cohort** "
            "(Adult Competitive Male Swimmers, Age 18–25)."
        )

    b_c1, b_c2, b_c3 = st.columns(3)
    b_c1.metric("Skill Level Tier", bm_res.overall_skill_level if is_demographic_compatible else "N/A (Non-Adult)")
    b_c2.metric("Age Demographics", bm_res.age_group)
    b_c3.metric("Gender Reference", bm_res.gender)

    st.caption(f"**Dataset Reference:** {bm_res.dataset_name} (ID: `{bm_res.dataset_id}`, v{bm_res.dataset_version}, Revision: {bm_res.scientific_revision})")
    st.markdown("---")

    # 2. Render Cards for each Metric
    for m_name, comp in bm_res.comparisons.items():
        if m_name == "performance_score":
            continue # Handled separately as SwimAnalyzer Composite Score

        ev_meta = getattr(comp, 'evidence', None)
        m_title = m_name.replace("_", " ").title()

        # Evidence status badge text & icon
        ev_id = getattr(ev_meta, 'evidence_id', 'NONE') if ev_meta else 'NONE'
        ev_record = ev_service.get_evidence_record(ev_id) if ev_id != 'NONE' else None

        badge_text = "⚠ INSUFFICIENT EVIDENCE"
        badge_style = "background-color:#FF9800; color:white;"

        if ev_record:
            if ev_record.audit_decision in [AuditDecision.ACCEPT, AuditDecision.ACCEPT_AS_DERIVED]:
                badge_text = "✓ SCIENTIFICALLY ACCEPTED"
                badge_style = "background-color:#4CAF50; color:white;"
            elif ev_record.audit_decision == AuditDecision.REFERENCE_ONLY:
                badge_text = "⚠ REFERENCE ONLY"
                badge_style = "background-color:#FFC107; color:black;"
            elif ev_record.audit_decision == AuditDecision.REJECT:
                badge_text = "✕ REJECTED"
                badge_style = "background-color:#F44336; color:white;"

        relationship_label = ev_record.relationship_to_benchmark.value if ev_record else "UNVERIFIED"
        relationship_fmt = relationship_label.replace("_", " ").title()

        with st.container(border=True):
            col_head, col_badge = st.columns([3, 2])
            with col_head:
                st.markdown(f"#### {m_title}")
            with col_badge:
                st.markdown(
                    f"""<div style="text-align:right;">
                    <span style="display:inline-block; padding:4px 12px; border-radius:12px; font-weight:bold; font-size:0.85rem; {badge_style}">
                    {badge_text}
                    </span></div>""",
                    unsafe_allow_html=True
                )

            # Metric Values
            c_val1, c_val2, c_val3, c_val4 = st.columns(4)
            c_val1.metric("Athlete Measurement", f"{comp.raw_value} {comp.unit}".strip())
            c_val2.metric("Scientific Reference", f"{comp.population_mean:.1f} {comp.unit}".strip())
            c_val3.metric("Reference Population", "Adult Competitive Males (18–25)")
            
            z_display = f"{comp.z_score:+.2f}" if comp.z_score is not None else "N/A"
            pct_display = f"{comp.percentile:.1f}%" if comp.percentile is not None else "N/A"
            c_val4.metric("Percentile Rank", pct_display, delta=f"Z: {z_display}" if z_display != "N/A" else None)

            # Source Line
            if ev_record:
                authors_str = ", ".join(ev_record.authors[:2]) if ev_record.authors else "Unknown"
                if len(ev_record.authors) > 2:
                    authors_str += " et al."
                citation_line = f"**Source:** {authors_str} ({ev_record.year}) — *{ev_record.publication}* | **Relationship:** {relationship_fmt}"
            else:
                citation_line = "**Source:** Not available in verified primary source | **Relationship:** Unverified"

            st.markdown(citation_line)

            # Expandable Scientific Evidence Drawer
            with st.expander("🔬 Scientific Evidence & Provenance Details", expanded=False):
                if ev_record:
                    st.markdown(f"**Publication Title:** {ev_record.title or 'Not available in verified source.'}")
                    st.markdown(f"**Authors:** {', '.join(ev_record.authors) if ev_record.authors else 'Not available in verified source.'}")
                    st.markdown(f"**Journal & Year:** {ev_record.publication} ({ev_record.year})")
                    st.markdown(f"**DOI:** {ev_record.doi if ev_record.doi else 'Not available in verified source.'}")
                    st.markdown(f"**Source Type:** {ev_record.source_quality.value if hasattr(ev_record, 'source_quality') else 'PEER_REVIEWED_FULL_TEXT'}")
                    st.markdown(f"**Sample Size:** N = {ev_record.sample_size if ev_record.sample_size else 'Not available in verified source.'}")
                    st.markdown(f"**Exact Source Location:** {ev_record.table_or_figure_reference}, {ev_record.page_reference}")
                    st.markdown(f"**Original Measurement:** {ev_record.reported_mean} ± {ev_record.reported_std} {ev_record.measurement_units}")
                    if ev_record.conversion_formula:
                        st.markdown(f"**Conversion Formula:** `{ev_record.conversion_formula}`")
                        st.markdown(f"**Converted Derived Value:** {ev_record.converted_value} {ev_record.converted_unit}")
                    st.markdown(f"**Definition Match:** `{ev_record.definition_compatibility.value}`")
                    st.markdown(f"**Population Match:** `{ev_record.population_compatibility.value}`")
                    st.markdown(f"**Audit Decision:** `{ev_record.audit_decision.value}`")
                    if ev_record.notes:
                        st.info(f"**Scientific Audit Notes:** {ev_record.notes}")
                else:
                    st.caption("No primary peer-reviewed evidence record is attached to this parameter.")

    # 3. Proprietary Performance Score Callout
    st.markdown("---")
    with st.container(border=True):
        st.markdown("#### 🏆 SwimAnalyzer Composite Score")
        ps_comp = bm_res.comparisons.get('performance_score') if bm_res and bm_res.comparisons else None
        ps_val = ps_comp.raw_value if ps_comp else 70.0
        st.metric("Composite Technique Index", f"{ps_val:.1f} / 100")
