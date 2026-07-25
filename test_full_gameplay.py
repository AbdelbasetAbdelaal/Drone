import sys
import os
import pygame

os.environ["SDL_AUDIODRIVER"] = "dummy"

print("--- RUNNING 2000-FRAME ALL-INCLUSIVE SYSTEM STRESS TEST ON drone_hunter_mobile/main.py ---")

real_event_get = pygame.event.get
step_count = 0
max_steps = 2000

def simulated_event_get(eventtype=None):
    global step_count
    step_count += 1
    events = real_event_get()
    
    # 1. Frame 10: Menu -> Sector Select
    if step_count == 10:
        print("[TEST EVENT] Frame 10: Menu -> Sector Select")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (640, 360), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (640, 360), 'button': 1}))

    # 2. Frame 30: Launch Sector 1 Stage 1
    elif step_count == 30:
        print("[TEST EVENT] Frame 30: Launch Sector 1 Stage 1 -> PLAYING")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (100, 200), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (100, 200), 'button': 1}))

    # 3. Frame 50 to 1950: Intensive loop
    elif 50 <= step_count <= 1950:
        if step_count % 50 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Joystick movement & Weapon Stream")
            events.append(pygame.event.Event(pygame.FINGERDOWN, {'x': 0.15, 'y': 0.70}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1200, 640), 'button': 1}))
        elif step_count % 120 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Cycle Weapon (Pulse -> Scatter -> Missile -> Beam)")
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1200, 35), 'button': 1}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1200, 35), 'button': 1}))
        elif step_count % 180 == 0:
            print(f"[TEST EVENT] Frame {step_count}: EMP Blast")
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1045, 625), 'button': 1}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1045, 625), 'button': 1}))
        elif step_count % 220 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Barrel Roll")
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1155, 490), 'button': 1}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1155, 490), 'button': 1}))
        elif step_count % 260 == 0:
            print(f"[TEST EVENT] Frame {step_count}: Tactical Cloak")
            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1045, 525), 'button': 1}))
            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1045, 525), 'button': 1}))

    # 4. Frame 2000: Quit cleanly
    elif step_count >= max_steps:
        print(f"[TEST EVENT] Frame {step_count}: 2000 Frames Reached! Sending QUIT.")
        events.append(pygame.event.Event(pygame.QUIT))

    return events

pygame.event.get = simulated_event_get

try:
    from drone_hunter_mobile.main import main
    main()
    print("✅ 2000-FRAME ALL-INCLUSIVE SYSTEM STRESS TEST PASSED PERFECTLY!")
except Exception as e:
    import traceback
    print(f"❌ CRASH DETECTED AT FRAME {step_count}: {e}")
    traceback.print_exc()
    with open("crash_log_mobile.txt", "w") as f:
        f.write(f"{e}\n")
        traceback.print_exc(file=f)
