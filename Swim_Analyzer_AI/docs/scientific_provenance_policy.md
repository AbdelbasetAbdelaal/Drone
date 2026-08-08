# Scientific Provenance Policy

**Date:** 2026-08-08

## 1. Traceability Standard
Every empirical benchmark in SwimAnalyzer AI must have a complete lineage chain. If a link in the chain breaks, the benchmark is automatically voided and treated as `INSUFFICIENT_EVIDENCE`.

**The Chain:**
`Benchmark YAML` → `Evidence ID` → `Source ID` (with validated PMCID/DOI) → `Target Population/Sex/Age`

## 2. Demographic Leakage Prevention
Scaling and leakage are prohibited:
* Youth populations must be supported by Youth evidence. You cannot take Adult Elite benchmarks and apply an arbitrary `-10%` reduction. 
* Male vs Female metrics must be explicitly isolated.
* Each stroke requires its own empirical foundation.

## 3. Ambiguity & Missing Evidence
If the literature database lacks empirical records for a specific cohort (e.g., U10 Backstroke):
1. The population cell receives a status of `INSUFFICIENT_EVIDENCE`.
2. The benchmark metrics return `None`.
3. The UI gracefully reports a lack of comparative data.
**We do not fill missing evidence grids with fake, calculated, or borrowed values.**
