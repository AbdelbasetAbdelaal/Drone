from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class AgeGroup(str, Enum):
    U10 = "8-10"
    U13 = "11-13"
    U17 = "14-17"
    ADULT = "18-25"
    SENIOR = "26-35"
    MASTERS = "Masters"

    @classmethod
    def from_age(cls, age: int) -> "AgeGroup":
        if age <= 10:
            return cls.U10
        elif age <= 13:
            return cls.U13
        elif age <= 17:
            return cls.U17
        elif age <= 25:
            return cls.ADULT
        elif age <= 35:
            return cls.SENIOR
        else:
            return cls.MASTERS

class GenderCategory(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    MIXED = "Mixed"

class SkillLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    NATIONAL = "National"
    ELITE = "Elite"
    OLYMPIC = "Olympic"

@dataclass
class PopulationStats:
    """Scientific reference population statistics for a specific metric."""
    mean: float
    std: float
    elite_mean: float
    unit: str = ""
    higher_is_better: bool = True

@dataclass
class MetricBenchmarkComparison:
    """Detailed scientific population comparison for a single metric."""
    metric_name: str
    raw_value: float
    population_mean: float
    population_std: float
    z_score: float
    percentile: float
    elite_mean: float
    elite_delta: float
    skill_level: str
    unit: str = ""
    measurement_confidence: float = 1.0
    population_confidence: float = 0.95
    benchmark_confidence: float = 0.95

@dataclass
class BenchmarkConfidence:
    """Decoupled confidence scores for measurement, population, and benchmark model."""
    measurement_confidence: float = 1.0
    population_confidence: float = 0.95
    benchmark_confidence: float = 0.95
    overall_confidence: float = 0.95

@dataclass
class BenchmarkResult:
    """Aggregates population comparisons across all biomechanical metrics."""
    stroke_type: str = "Freestyle"
    age_group: str = "18-25"
    gender: str = "Male"
    overall_skill_level: str = "Intermediate"
    dataset_version: str = "1.0.0"
    dataset_name: str = ""
    confidence: BenchmarkConfidence = field(default_factory=BenchmarkConfidence)
    comparisons: Dict[str, MetricBenchmarkComparison] = field(default_factory=dict)
