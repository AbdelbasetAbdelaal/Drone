import os
import math
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from models.benchmark_models import (
    AgeGroup, GenderCategory, SkillLevel, PopulationStats,
    MetricBenchmarkComparison, BenchmarkResult, BenchmarkConfidence
)
from models.data_models import AnalysisResult
from models.athlete_profile import AthleteProfile
from core.logger import setup_logger

logger = setup_logger(__name__)

class BenchmarkEngine:
    """
    Scientific Population Benchmark Engine.
    Calculates Z-scores, normal distribution percentiles, elite deltas,
    and skill level classifications using YAML population datasets.
    """
    def __init__(self, benchmark_dir: Optional[Path] = None):
        if benchmark_dir is None:
            benchmark_dir = Path(__file__).resolve().parent.parent.parent / "config" / "benchmarks"
        self.benchmark_dir = benchmark_dir
        self._datasets: Dict[str, dict] = {}
        self.reload_datasets()

    def reload_datasets(self):
        """Loads all YAML benchmark dataset configuration files."""
        self._datasets.clear()
        if not self.benchmark_dir.exists():
            logger.warning(f"Benchmark directory {self.benchmark_dir} does not exist.")
            return

        for yaml_file in self.benchmark_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    stroke = data.get("stroke", yaml_file.stem.capitalize())
                    self._datasets[stroke.lower()] = data
                    logger.info(f"Loaded benchmark dataset for {stroke} (v{data.get('version', '1.0.0')})")
            except Exception as e:
                logger.error(f"Failed to load benchmark YAML {yaml_file}: {e}")

    def _get_dataset(self, stroke_type: str) -> Optional[dict]:
        return self._datasets.get(stroke_type.lower()) or self._datasets.get("freestyle")

    def _get_population_stats(self, stroke_type: str, age_group: str, gender: str, metric_name: str) -> PopulationStats:
        ds = self._get_dataset(stroke_type)
        if not ds:
            # Safe scientific fallbacks
            return PopulationStats(mean=70.0, std=10.0, elite_mean=95.0, unit="")

        pops = ds.get("populations", {})
        age_pop = pops.get(age_group) or pops.get("18-25") or pops.get("default", {})
        gender_pop = age_pop.get(gender) or age_pop.get("Mixed") or ds.get("populations", {}).get("default", {})
        
        metric_cfg = gender_pop.get(metric_name) or ds.get("populations", {}).get("default", {}).get(metric_name)

        if not metric_cfg:
            return PopulationStats(mean=70.0, std=10.0, elite_mean=95.0, unit="")

        return PopulationStats(
            mean=float(metric_cfg.get("mean", 70.0)),
            std=float(metric_cfg.get("std", 10.0)),
            elite_mean=float(metric_cfg.get("elite_mean", 95.0)),
            unit=str(metric_cfg.get("unit", "")),
            higher_is_better=bool(metric_cfg.get("higher_is_better", True))
        )

    @staticmethod
    def calculate_z_score(raw_value: float, mean: float, std: float) -> float:
        """Calculates statistical Z-score: Z = (x - mu) / sigma."""
        if std <= 0:
            return 0.0
        return (raw_value - mean) / std

    @staticmethod
    def calculate_percentile(z_score: float, higher_is_better: bool = True) -> float:
        """
        Calculates cumulative distribution function (CDF) percentile from Z-score.
        P = 0.5 * (1 + erf(z / sqrt(2))) * 100%
        """
        cdf = 0.5 * (1.0 + math.erf(z_score / math.sqrt(2.0))) * 100.0
        percentile = cdf if higher_is_better else (100.0 - cdf)
        return float(min(99.9, max(0.1, percentile)))

    def get_skill_level(self, performance_score: float, stroke_type: str = "Freestyle") -> str:
        """Classifies performance score into skill level tiers."""
        ds = self._get_dataset(stroke_type)
        thresholds = ds.get("skill_level_thresholds", {}).get("performance_score", {}) if ds else {}

        if performance_score >= thresholds.get("Olympic", 97.0):
            return SkillLevel.OLYMPIC.value
        elif performance_score >= thresholds.get("Elite", 93.0):
            return SkillLevel.ELITE.value
        elif performance_score >= thresholds.get("National", 86.0):
            return SkillLevel.NATIONAL.value
        elif performance_score >= thresholds.get("Advanced", 78.0):
            return SkillLevel.ADVANCED.value
        elif performance_score >= thresholds.get("Intermediate", 65.0):
            return SkillLevel.INTERMEDIATE.value
        else:
            return SkillLevel.BEGINNER.value

    # --- Clean Public APIs for Future AI Coach Compatibility ---

    def get_percentile(self, metric_name: str, raw_value: float, stroke_type: str = "Freestyle",
                       age_group: str = "18-25", gender: str = "Male") -> float:
        stats = self._get_population_stats(stroke_type, age_group, gender, metric_name)
        z = self.calculate_z_score(raw_value, stats.mean, stats.std)
        return self.calculate_percentile(z, stats.higher_is_better)

    def compare_with_elite(self, metric_name: str, raw_value: float, stroke_type: str = "Freestyle",
                           age_group: str = "18-25", gender: str = "Male") -> Dict[str, float]:
        stats = self._get_population_stats(stroke_type, age_group, gender, metric_name)
        delta = raw_value - stats.elite_mean
        pct_of_elite = (raw_value / stats.elite_mean * 100.0) if stats.elite_mean > 0 else 0.0
        return {"raw_value": raw_value, "elite_mean": stats.elite_mean, "delta": delta, "pct_of_elite": pct_of_elite}

    def compare_with_population(self, metric_name: str, raw_value: float, stroke_type: str = "Freestyle",
                                age_group: str = "18-25", gender: str = "Male") -> Dict[str, Any]:
        stats = self._get_population_stats(stroke_type, age_group, gender, metric_name)
        z = self.calculate_z_score(raw_value, stats.mean, stats.std)
        pct = self.calculate_percentile(z, stats.higher_is_better)
        return {
            "metric_name": metric_name,
            "raw_value": raw_value,
            "population_mean": stats.mean,
            "population_std": stats.std,
            "z_score": round(z, 2),
            "percentile": round(pct, 1),
            "unit": stats.unit
        }

    def get_expected_range(self, metric_name: str, stroke_type: str = "Freestyle",
                           age_group: str = "18-25", gender: str = "Male") -> Tuple[float, float]:
        stats = self._get_population_stats(stroke_type, age_group, gender, metric_name)
        low = stats.mean - 2.0 * stats.std
        high = stats.mean + 2.0 * stats.std
        return (low, high)

    def evaluate_full_analysis(self, analysis_result: AnalysisResult,
                               athlete_profile: Optional[AthleteProfile] = None) -> BenchmarkResult:
        """
        Main orchestration method: Evaluates all biomechanical metrics against population benchmarks.
        Returns a complete BenchmarkResult dataclass.
        """
        stroke_type = getattr(analysis_result, 'stroke_type', 'Freestyle')
        if not stroke_type or stroke_type == "Unknown":
            stroke_type = "Freestyle"

        age_group = AgeGroup.from_age(athlete_profile.age).value if (athlete_profile and athlete_profile.age) else "18-25"
        gender = athlete_profile.gender if (athlete_profile and athlete_profile.gender in ["Male", "Female"]) else "Mixed"

        ds = self._get_dataset(stroke_type)
        ds_version = ds.get("version", "1.0.0") if ds else "1.0.0"
        ds_name = ds.get("dataset_name", "Population Reference Dataset") if ds else "Population Reference Dataset"

        report = getattr(analysis_result, 'report', None)
        overall_score = report.overall_score if report else 70.0
        overall_skill = self.get_skill_level(overall_score, stroke_type)

        # Extract metric values to benchmark
        metrics_to_eval = {}
        if report:
            if getattr(report, 'stroke_rate', None) and report.stroke_rate.value > 0:
                metrics_to_eval["stroke_rate"] = report.stroke_rate.value
            if getattr(report, 'stroke_length', None) and report.stroke_length.value > 0:
                metrics_to_eval["stroke_length"] = report.stroke_length.value
            if getattr(report, 'kick_frequency', None) and report.kick_frequency.value > 0:
                metrics_to_eval["kick_frequency"] = report.kick_frequency.value
            if getattr(report, 'stroke_symmetry', None) and report.stroke_symmetry.value > 0:
                metrics_to_eval["stroke_symmetry"] = report.stroke_symmetry.value
            metrics_to_eval["performance_score"] = report.overall_score

        # 3D metrics from frames if available
        if analysis_result.frames:
            rolls = [f.angles.body_roll_3d.value for f in analysis_result.frames if f.is_valid and f.angles and f.angles.body_roll_3d and f.angles.body_roll_3d.value > 0]
            if rolls:
                metrics_to_eval["body_roll"] = sum(rolls) / len(rolls)

        comparisons = {}
        for m_name, val in metrics_to_eval.items():
            stats = self._get_population_stats(stroke_type, age_group, gender, m_name)
            z = self.calculate_z_score(val, stats.mean, stats.std)
            pct = self.calculate_percentile(z, stats.higher_is_better)
            delta = val - stats.elite_mean
            m_skill = self.get_skill_level(val if m_name == "performance_score" else (val/stats.elite_mean*100.0), stroke_type)

            comparisons[m_name] = MetricBenchmarkComparison(
                metric_name=m_name,
                raw_value=round(val, 2),
                population_mean=stats.mean,
                population_std=stats.std,
                z_score=round(z, 2),
                percentile=round(pct, 1),
                elite_mean=stats.elite_mean,
                elite_delta=round(delta, 2),
                skill_level=m_skill,
                unit=stats.unit,
                measurement_confidence=1.0,
                population_confidence=0.95,
                benchmark_confidence=0.95
            )

        conf = BenchmarkConfidence(measurement_confidence=1.0, population_confidence=0.95, benchmark_confidence=0.95, overall_confidence=0.95)

        return BenchmarkResult(
            stroke_type=stroke_type,
            age_group=age_group,
            gender=gender,
            overall_skill_level=overall_skill,
            dataset_version=ds_version,
            dataset_name=ds_name,
            confidence=conf,
            comparisons=comparisons
        )
