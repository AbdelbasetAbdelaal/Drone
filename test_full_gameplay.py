import sys
import os
import pygame

os.environ["SDL_AUDIODRIVER"] = "dummy"

print("--- RUNNING 1200-FRAME MULTI-STAGE CYCLE STRESS TEST ON drone_hunter_mobile/main.py ---")

real_event_get = pygame.event.get
step_count = 0
max_steps = 1200

def simulated_event_get(eventtype=None):
    global step_count
    step_count += 1
    events = real_event_get()
    
    if step_count == 10:
        print("[TEST EVENT] Frame 10: Menu -> Sector Select")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (640, 360), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (640, 360), 'button': 1}))

    elif step_count == 30:
        print("[TEST EVENT] Frame 30: Launch Sector 1 Stage 1 -> PLAYING")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (100, 200), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (100, 200), 'button': 1}))

    elif 50 <= step_count <= 1100:
        if step_count % 30 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Continuous Virtual Joystick & Weapon Stream")
            events.append(pygame.event.Event(pygame.FINGERDOWN, {'x': 0.15, 'y': 0.70}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1200, 640), 'button': 1}))
        elif step_count % 150 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Triggering EMP Blast")
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1045, 625), 'button': 1}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1045, 625), 'button': 1}))
        elif step_count % 200 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Triggering Barrel Roll")
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1155, 490), 'button': 1}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1155, 490), 'button': 1}))

    elif step_count >= max_steps:
        print(f"[TEST EVENT] Frame {step_count}: 1200 Frames Reached! Sending QUIT.")
        events.append(pygame.event.Event(pygame.QUIT))

    return events

pygame.event.get = simulated_event_get

try:
    from drone_hunter_mobile.main import main
    main()
    print("✅ 1200-FRAME STRESS TEST PASSED PERFECTLY WITH ZERO CRASHES!")
except Exception as e:
    import traceback
    print(f"❌ CRASH DETECTED AT FRAME {step_count}: {e}")
    traceback.print_exc()
    with open("crash_log_mobile.txt", "w") as f:
        f.write(f"{e}\n")
        traceback.print_exc(file=f)
