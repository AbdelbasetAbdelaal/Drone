import math
import sys
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BG, COLOR_HUD
)
from src.player import Player
from src.target import Spawner

# Procedural Sound Effect Generator
def create_sound_effect(freq: float = 440.0, duration: float = 0.1, volume: float = 0.3) -> pygame.mixer.Sound | None:
    try:
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            decay = 1.0 - (i / num_samples)
            sample = int(128 + 127 * volume * decay * math.sin(2 * math.pi * freq * t))
            buf.append(max(0, min(255, sample)))
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None

def main():
    # 1. Initialize Pygame & Subsystems
    pygame.init()
    pygame.font.init()
    try:
        pygame.mixer.init(frequency=22050, size=-8, channels=1, buffer=512)
    except Exception:
        pass

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Create Fonts
    font_hud = pygame.font.SysFont("Arial", 24, bold=True)
    font_banner = pygame.font.SysFont("Arial", 42, bold=True)
    font_gameover = pygame.font.SysFont("Arial", 48, bold=True)

    # Sound Effects
    hit_sound = create_sound_effect(freq=600.0, duration=0.08, volume=0.4)
    levelup_sound = create_sound_effect(freq=880.0, duration=0.3, volume=0.5)
    gameover_sound = create_sound_effect(freq=180.0, duration=0.4, volume=0.5)

    # 2. Sprite Groups Setup
    player_group = pygame.sprite.GroupSingle()
    bullet_group = pygame.sprite.Group()
    target_group = pygame.sprite.Group()

    # Instantiate Player Drone & Spawner
    drone = Player((200, SCREEN_HEIGHT // 2))
    player_group.add(drone)
    spawner = Spawner(base_min_interval=1.5, base_max_interval=3.0)

    # Game State Variables
    current_level = 1
    level_score = 0      # Points in current level (0 to 100)
    total_score = 0      # Cumulative score across all levels
    points_per_level = 100
    
    level_up_timer = 0.0  # Duration to display "LEVEL UP!" message on screen
    game_over = False

    # Main Game Loop
    running = True
    while running:
        # Compute Frame Delta Time
        dt = clock.tick(FPS) / 1000.0

        # Update Level Up Announcement Timer
        if level_up_timer > 0:
            level_up_timer = max(0.0, level_up_timer - dt)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and game_over:
                    # Reset Game State on 'R'
                    current_level = 1
                    level_score = 0
                    total_score = 0
                    level_up_timer = 0.0
                    game_over = False
                    spawner.set_level(current_level)
                    bullet_group.empty()
                    target_group.empty()
                    drone = Player((200, SCREEN_HEIGHT // 2))
                    player_group.add(drone)

            # Manual single click shooting event
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
                bullet = drone.shoot(pygame.mouse.get_pos())
                if bullet:
                    bullet_group.add(bullet)

        if not game_over:
            # Automatic continuous shooting while holding left mouse
            if pygame.mouse.get_pressed()[0]:
                bullet = drone.shoot(pygame.mouse.get_pos())
                if bullet:
                    bullet_group.add(bullet)

            # --- Game State Update ---
            player_group.update(dt)
            bullet_group.update(dt)
            target_group.update(dt)
            spawner.update(dt, target_group)

            # --- Collision Detection ---
            # 1. Check collisions between bullet_group and target_group
            hits = pygame.sprite.groupcollide(bullet_group, target_group, True, True, pygame.sprite.collide_circle)
            if hits:
                for _ in hits:
                    level_score += 10
                    total_score += 10
                if hit_sound:
                    hit_sound.play()

                # --- Level Advancement Logic (Every 100 points) ---
                if level_score >= points_per_level:
                    current_level += 1
                    level_score %= points_per_level
                    level_up_timer = 2.0  # Show banner for 2 seconds
                    spawner.set_level(current_level)
                    target_group.empty()  # Clear screen targets on level clear
                    if levelup_sound:
                        levelup_sound.play()

            # 2. Check Game Over Conditions: Drone hits ground OR collides with target
            drone_hit_target = pygame.sprite.spritecollide(drone, target_group, False, pygame.sprite.collide_circle)
            drone_hit_ground = drone.is_touching_ground()

            if drone_hit_target or drone_hit_ground:
                game_over = True
                if gameover_sound:
                    gameover_sound.play()

        # --- Rendering Pipeline ---
        screen.fill(COLOR_BG)

        # Draw Game Entities
        player_group.draw(screen)
        bullet_group.draw(screen)
        target_group.draw(screen)

        # --- Render HUD Overlay ---
        current_fps = int(clock.get_fps())
        
        level_surface = font_hud.render(f"LEVEL {current_level}", True, (250, 204, 21))   # Yellow
        progress_surface = font_hud.render(f"Level Progress: {level_score} / {points_per_level} pts", True, COLOR_HUD)
        total_surface = font_hud.render(f"Total Score: {total_score}", True, COLOR_HUD)
        fps_surface = font_hud.render(f"FPS: {current_fps}", True, (52, 211, 153))         # Mint Green
        controls_surface = font_hud.render("Space: Thrust | A/D: Move | Left Click: Aim & Shoot", True, (148, 163, 184))

        screen.blit(level_surface, (20, 15))
        screen.blit(progress_surface, (160, 15))
        screen.blit(total_surface, (450, 15))
        screen.blit(fps_surface, (SCREEN_WIDTH - 130, 15))
        screen.blit(controls_surface, (20, SCREEN_HEIGHT - 35))

        # --- Render Level Up Banner Overlay ---
        if level_up_timer > 0 and not game_over:
            banner_surf = font_banner.render(f"🎉 LEVEL {current_level} UNLOCKED! 🎉", True, (56, 189, 248))
            banner_rect = banner_surf.get_rect(center=(SCREEN_WIDTH // 2, 140))
            screen.blit(banner_surf, banner_rect)

        # --- Render Game Over Screen ---
        if game_over:
            over_surface = font_gameover.render("GAME OVER", True, (239, 68, 68))
            stats_surface = font_hud.render(f"Final Level: {current_level}  |  Total Score: {total_score}", True, (226, 232, 240))
            restart_surface = font_hud.render("Press 'R' to Restart", True, (56, 189, 248))
            
            rect_over = over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            rect_stats = stats_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            rect_restart = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            
            screen.blit(over_surface, rect_over)
            screen.blit(stats_surface, rect_stats)
            screen.blit(restart_surface, rect_restart)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
