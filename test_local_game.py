import sys
import os
import pygame

# Set dummy audio driver to avoid audio output issues in headless test
os.environ["SDL_AUDIODRIVER"] = "dummy"

try:
    print("Executing drone_hunter_mobile main()...")
    from drone_hunter_mobile.main import main
    # Run main()
    main()
    print("Finished main() execution cleanly!")
except Exception as e:
    import traceback
    print(f"CRASH DETECTED: {e}")
    traceback.print_exc()
    with open("crash_log_mobile.txt", "w") as f:
        f.write(f"{e}\n")
        traceback.print_exc(file=f)
