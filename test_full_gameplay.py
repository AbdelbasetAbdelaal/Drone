import sys
import os
import pygame

# Set dummy audio driver for headless stress testing
os.environ["SDL_AUDIODRIVER"] = "dummy"

print("--- STARTING EXTENSIVE FULL-GAMEPLAY STRESS TEST (600 FRAMES, ALL STATES & CONTROLS) ---")

real_event_get = pygame.event.get
step_count = 0
max_steps = 600

def simulated_event_get(eventtype=None):
    global step_count
    step_count += 1
    events = real_event_get()
    
    # 1. Frame 10: Tap Menu -> Sector Select
    if step_count == 10:
        print("[TEST EVENT] Frame 10: Tap Main Menu -> SECTOR SELECT")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (640, 360), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (640, 360), 'button': 1}))

    # 2. Frame 30: Press SPACE to enter Hangar Shop
    elif step_count == 30:
        print("[TEST EVENT] Frame 30: Press [SPACE] -> HANGAR SHOP")
        events.append(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE}))

    # 3. Frame 50: Buy Upgrades in Hangar
    elif step_count == 50:
        print("[TEST EVENT] Frame 50: Tap Battery Upgrade Rect -> Buy Battery Upgrade")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (100, 150), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (100, 150), 'button': 1}))

    # 4. Frame 70: Tap Start Mission in Hangar -> PLAYING
    elif step_count == 70:
        print("[TEST EVENT] Frame 70: Tap Start Mission -> PLAYING")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (300, 655), 'button': 1}))
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (300, 655), 'button': 1}))

    # 5. Frame 100-300: Test Action Buttons (EMP, Roll, Cloak, Weapon Cycle)
    elif step_count == 100:
        print("[TEST EVENT] Frame 100: Tap EMP Blast Button")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1045, 625), 'button': 1})) # EMP rect
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1045, 625), 'button': 1}))

    elif step_count == 120:
        print("[TEST EVENT] Frame 120: Tap Barrel Roll Button")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1155, 490), 'button': 1})) # Roll rect
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1155, 490), 'button': 1}))

    elif step_count == 140:
        print("[TEST EVENT] Frame 140: Tap Cloak Button")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1045, 525), 'button': 1})) # Cloak rect
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1045, 525), 'button': 1}))

    elif step_count == 160:
        print("[TEST EVENT] Frame 160: Tap Weapon Cycle Button")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (1200, 35), 'button': 1})) # Weapon rect
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (1200, 35), 'button': 1}))

    # 6. Frame 200: Tap Pause Button -> STATE_PAUSED
    elif step_count == 200:
        print("[TEST EVENT] Frame 200: Tap Pause Button -> PAUSE SETTINGS MENU")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (40, 35), 'button': 1})) # Pause rect
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (40, 35), 'button': 1}))

    # 7. Frame 250: Tap Resume Button -> STATE_PLAYING
    elif step_count == 250:
        print("[TEST EVENT] Frame 250: Tap Resume Button in Pause Menu -> PLAYING")
        events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (300, 490), 'button': 1})) # Resume rect
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (300, 490), 'button': 1}))

    # 8. Frame 590: Send QUIT cleanly
    elif step_count >= max_steps:
        print(f"[TEST EVENT] Frame {step_count}: 600 Frames Reached! Sending QUIT.")
        events.append(pygame.event.Event(pygame.QUIT))

    return events

pygame.event.get = simulated_event_get

try:
    from drone_hunter_mobile.main import main
    main()
    print(f"🎉 600-FRAME FULL STATE STRESS TEST PASSED WITH ZERO CRASHES!")
except Exception as e:
    import traceback
    print(f"❌ CRASH DETECTED AT FRAME {step_count}: {e}")
    traceback.print_exc()
    with open("crash_log_mobile.txt", "w") as f:
        f.write(f"{e}\n")
        traceback.print_exc(file=f)
