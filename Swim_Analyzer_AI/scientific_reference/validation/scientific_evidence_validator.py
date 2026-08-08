from typing import Dict, Any, Tuple, Optional
from models.scientific_evidence_models import (
    DefinitionMatchingStatus, PopulationMatchingStatus, SourceRelationship
)
from core.logger import setup_logger

logger = setup_logger(__name__)

class ScientificEvidenceValidator:
    """
    Validation engine enforcing unit conversions, measurement definition alignment,
    and demographic population compatibility rules.
    """
    
    @staticmethod
    def convert_unit(value: float, original_unit: str, target_unit: str) -> Tuple[float, str, str]:
        """
        Scientifically auditable unit conversion layer.
        Returns (converted_value, target_unit, conversion_formula).
        """
        orig = original_unit.lower().strip()
        targ = target_unit.lower().strip()

        if orig == targ:
            return (value, target_unit, "1:1 Exact Match (No conversion required)")

        # Frequency conversions: Hz to spm / cycles per minute
        if orig in ["hz", "cycles/sec", "strokes/sec"] and targ in ["spm", "cycles/min", "strokes/min"]:
            converted = value * 60.0
            formula = f"{value} {original_unit} * 60 = {converted} {target_unit}"
            return (round(converted, 2), target_unit, formula)

        if orig in ["spm", "cycles/min", "strokes/min"] and targ in ["hz", "cycles/sec"]:
            converted = value / 60.0
            formula = f"{value} {original_unit} / 60 = {converted:.4f} {target_unit}"
            return (round(converted, 4), target_unit, formula)

        # Distance conversions: meters
        if orig == "m" and targ == "m":
            return (value, target_unit, "1:1 Exact Match")

        # Angle conversions: degrees
        if orig in ["deg", "degrees", "°"] and targ in ["deg", "degrees"]:
            return (value, target_unit, "1:1 Exact Match")

        logger.warning(f"Unsupported or complex unit conversion from {original_unit} to {target_unit}")
        return (value, original_unit, "Direct Pass-through (Unconverted)")

    @staticmethod
    def evaluate_definition_match(source_def: str, swimanalyzer_def: str) -> DefinitionMatchingStatus:
        """
        Compares scientific publication measurement definition against SwimAnalyzer definition.
        Prevents treating related but distinct measurements as identical.
        """
        src = source_def.lower().strip()
        sa = swimanalyzer_def.lower().strip()

        if src == sa or (("stroke rate" in src or "cycle frequency" in src) and ("stroke rate" in sa or "stroke_rate" in sa)):
            return DefinitionMatchingStatus.EXACT_MATCH
        elif ("distance per stroke" in src or "stroke length" in src) and ("stroke_length" in sa or "stroke length" in sa):
            return DefinitionMatchingStatus.EXACT_MATCH
        elif "shoulder roll" in src and "torso normal vector" in sa:
            return DefinitionMatchingStatus.DEFINITION_MISMATCH
        elif "hip roll" in src and "torso normal vector" in sa:
            return DefinitionMatchingStatus.DEFINITION_MISMATCH
        elif "symmetry" in src and "symmetry" in sa:
            return DefinitionMatchingStatus.COMPATIBLE_DEFINITION
        elif "kick frequency" in src and "kick_frequency" in sa:
            return DefinitionMatchingStatus.COMPATIBLE_DEFINITION
        else:
            return DefinitionMatchingStatus.UNKNOWN_DEFINITION

    @staticmethod
    def evaluate_population_match(study_pop: str, target_pop: str,
                                 study_age_range: Tuple[Optional[int], Optional[int]],
                                 target_age_range: Tuple[Optional[int], Optional[int]]) -> PopulationMatchingStatus:
        """
        Compares study demographic cohort against target benchmark population.
        Strictly flags POPULATION_MISMATCH if adult data is extrapolated to youth or masters.
        """
        spop = study_pop.lower()
        tpop = target_pop.lower()

        # Check age range compatibility
        s_min, s_max = study_age_range
        t_min, t_max = target_age_range

        if t_min is not None and s_min is not None:
            if t_min < 14 and s_min >= 18:
                return PopulationMatchingStatus.POPULATION_MISMATCH # Adult to Junior extrapolation guard!
            if t_min >= 35 and s_max is not None and s_max <= 25:
                return PopulationMatchingStatus.POPULATION_MISMATCH # Adult to Masters extrapolation guard!

        if spop == tpop:
            return PopulationMatchingStatus.EXACT_MATCH
        elif "competitive" in spop and "competitive" in tpop:
            return PopulationMatchingStatus.COMPATIBLE
        elif "elite" in spop and "national" in tpop:
            return PopulationMatchingStatus.PARTIAL_MATCH
        else:
            return PopulationMatchingStatus.POPULATION_MISMATCH
