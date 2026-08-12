import os
import re

files_to_check = [
    r"d:\AI_Projects\Swim_Analyzer_AI\app\streamlit_app.py",
    r"d:\AI_Projects\Swim_Analyzer_AI\app\ui\charts.py",
    r"d:\AI_Projects\Swim_Analyzer_AI\analysis\consistency_validator.py"
]

ui_dir = r"d:\AI_Projects\Swim_Analyzer_AI\app\ui"
if os.path.exists(ui_dir):
    for f in os.listdir(ui_dir):
        if f.endswith(".py"):
            fp = os.path.join(ui_dir, f)
            if fp not in files_to_check:
                files_to_check.append(fp)

patterns = [
    (r"(\w+)\s*>\s*(\d+(\.\d+)?)", "> comparison with literal"),
    (r"(\w+)\s*<\s*(\d+(\.\d+)?)", "< comparison with literal"),
    (r"(\w+)\s*>=\s*(\d+(\.\d+)?)", ">= comparison with literal"),
    (r"(\w+)\s*<=\s*(\d+(\.\d+)?)", "<= comparison with literal"),
    (r"(\w+)\s*>\s*(\w+)", "> comparison between variables"),
    (r"(\w+)\s*<\s*(\w+)", "< comparison between variables"),
    (r"min\(", "min function"),
    (r"max\(", "max function"),
    (r"round\(", "round function"),
    (r"float\(", "float function"),
    (r"st\.progress\(", "st.progress call"),
]

for filepath in files_to_check:
    if not os.path.exists(filepath):
        continue
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            # check for potential unsafe operators
            for pat, desc in patterns:
                if re.search(pat, line_str) and not line_str.startswith("#"):
                    # check if guarded by is not None
                    if "is not None" not in line_str and " if " not in line_str and "getattr" not in line_str and "def " not in line_str:
                        print(f"[{desc}] {os.path.basename(filepath)}:{idx} -> {line_str}")
