import sys
import os

# Redirect traceback to console
try:
    from drone_hunter_mobile.main import main
    print("Successfully imported main from drone_hunter_mobile!")
except Exception as e:
    import traceback
    print(f"Import failed: {e}")
    traceback.print_exc()
