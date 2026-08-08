# Scientific Database Update Policy

**Date:** 2026-08-08

## 1. Overview
The "One-Click Scientific Database Update" system is a strict, atomic, and idempotent engine that queries PubMed and PMC to maintain an evidence-backed biomechanics benchmark registry.

## 2. Transaction Safety & Atomicity
Updates are entirely isolated from production data until validation completes.
1. **Staging Environment:** All parsing and validation happens in a temporary staging directory.
2. **Commit Gate:** Staging is only moved to production if 100% of the integrity tests pass.
3. **Rollback:** If ANY network error, parsing error, or validation failure occurs (e.g. SSL failure, timeout, mismatched populations), staging is destroyed, and production remains completely untouched.
4. **No UI Rerun Triggers:** Streamlit caching blocks repeated ingestion attempts on component rerenders. Updates require explicit user action.

## 3. Strict Source Ingestion
1. **Legitimate Search Only:** Literature is retrieved dynamically via NCBI APIs.
2. **Semantic Verification:** An abstract or paper MUST match the target context (e.g., swimming, specific stroke). Extraneous or unrelated PMIDs are dropped.
3. **Never Fabricate:** The system NEVER guesses or interpolates missing means, sample sizes, or demographic dimensions. 

## 4. Internet Failure Protocol
In the event of an API failure, timeout, or lack of internet connectivity, the system will explicitly alert the user and cleanly abort. **It will never silently load fallback mock data.**
