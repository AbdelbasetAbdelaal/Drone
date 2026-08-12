import os

PATTERNS = ["0.25", "0.40", "15.0", "0.15", "defaulted candidate to Freestyle", "defaulted to Freestyle", "FALLBACK_DEFAULT"]

root_dir = r"d:\AI_Projects\Swim_Analyzer_AI"
results = []

for root, dirs, files in os.walk(root_dir):
    if "venv" in root or ".git" in root or ".pytest_cache" in root:
        continue
    for f in files:
        if f.endswith(".py") or f.endswith(".md"):
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
                for idx, line in enumerate(lines, 1):
                    for p in PATTERNS:
                        if p in line:
                            results.append((p, os.path.relpath(filepath, root_dir), idx, line.strip()))

print(f"Total forbidden pattern occurrences found: {len(results)}\n")
for p, f, idx, line in results:
    print(f"[{p}] {f}:{idx} -> {line}")
