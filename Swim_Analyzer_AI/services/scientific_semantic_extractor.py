"""
Scientific Semantic Extractor.
Isolated wrapper for the Gemini model to parse scientific literature structurally.
Treats all LLM output as untrusted candidate claims that require deterministic validation.
"""
import os
import json
import logging
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

logger = logging.getLogger(__name__)

class ScientificSemanticExtractor:
    """
    Wraps the Gemini LLM for structural interpretation of scientific texts.
    Implements a strict boundary:
    1. Returns structured JSON claims.
    2. Has no authority to accept evidence itself.
    3. Gracefully degrades if no API key is available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.degraded_mode = False
        
        # Load key from argument, or environment
        key_to_use = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not HAS_GEMINI or not key_to_use:
            logger.warning("ScientificSemanticExtractor initialized in DEGRADED_MODE. Missing google-generativeai or GEMINI_API_KEY.")
            self.degraded_mode = True
            self.model = None
        else:
            try:
                genai.configure(api_key=key_to_use)
                # Use a reliable stable model for extraction, preferably pro if available
                self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                self.degraded_mode = True
                self.model = None

    def is_degraded(self) -> bool:
        """Returns True if the semantic extractor is offline or missing credentials."""
        return self.degraded_mode

    def extract_evidence_candidates(self, text_context: str) -> Optional[Dict[str, Any]]:
        """
        Sends a structurally parsed text context (e.g. a table or section) to Gemini
        and demands strict JSON candidate extraction.
        
        If in degraded mode, returns None.
        """
        if self.is_degraded() or not self.model:
            return None
            
        prompt = """
You are a Scientific Biomechanics Extraction Assistant.
Your job is to read the provided scientific text/table context and extract kinematic evidence candidates as strict JSON.

CRITICAL SCIENTIFIC SAFETY RULES:
1. Do NOT infer missing information.
2. Do NOT estimate or guess numerical values.
3. Do NOT infer age from competition level, or sex, or stroke.
4. Do NOT infer metric definitions or units.
5. Only report information explicitly supported by the supplied source text.
6. If a value is ambiguous or mixed, return null for it.

Expected JSON output format:
{
  "candidates": [
    {
      "stroke": "Freestyle|Backstroke|Breaststroke|Butterfly|Unknown",
      "population_sex": "Male|Female|Mixed|Unknown",
      "population_age": "string descriptor or null",
      "metric": "string metric name",
      "mean": float or null,
      "sd": float or null,
      "unit": "string unit or null",
      "table_or_figure": "string if explicitly mentioned or null"
    }
  ]
}

Return ONLY the raw JSON block without markdown formatting or backticks.
If no valid evidence can be extracted, return {"candidates": []}.

CONTEXT TO ANALYZE:
---
"""
        full_prompt = prompt + text_context + "\n---"
        
        try:
            response = self.model.generate_content(full_prompt)
            raw_text = response.text.strip()
            # Clean up potential markdown formatting if the model disobeys
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "", 1)
            if raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            data = json.loads(raw_text.strip())
            return data
        except json.JSONDecodeError as e:
            logger.error(f"SemanticExtractor returned invalid JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"SemanticExtractor generation failed: {e}")
            return None
