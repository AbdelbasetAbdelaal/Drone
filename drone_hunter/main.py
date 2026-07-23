import os
import sys
import random
import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BG, COLOR_HUD,
    STATE_MENU, STATE_PLAYING, STATE_GAME_OVER, STATE_LEVEL_CLEAR,
    COLOR_CYAN, COLOR_EMERALD, COLOR_GOLD
)
from src.player import Player
from src.target import Spawner
from src.powerup import BatteryCharge
from src.particles import ParticleManager
from src.background import ParallaxBackground
from src.audio import AudioManager

HIGHSCORE_FILE = "highscore.txt"

def load_highscore() -> int:
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0

def save_highscore(score: int):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        pass

def main():
    # Initialize Pygame & Subsystems
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Systems
    background = ParallaxBackground()
    particle_manager = ParticleManager()
    audio_manager = AudioManager()

    # Fonts
    font_title = pygame.font.SysFont("Arial", 64, bold=True)
    font_hud = pygame.font.SysFont("Arial", 22, bold=True)
    font_banner = pygame.font.SysFont("Arial", 40, bold=True)
    font_gameover = pygame.font.SysFont("Arial", 52, bold=True)

    # Sprite Groups
    player_group = pygame.sprite.GroupSingle()
    bullet_group = pygame.sprite.Group()
    target_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()

    # Game State Variables
    game_state = STATE_MENU
    highscore = load_highscore()
    
    current_level = 1
    level_score = 0
    total_score = 0
    battery_timer = 0.0

    drone = None
    spawner = None

    def reset_game():
        nonlocal drone, spawner, current_level, level_score, total_score, battery_timer
        current_level = 1
        level_score = 0
        total_score = 0
        battery_timer = 0.0
        
        bullet_group.empty()
        target_group.empty()
        powerup_group.empty()
        particle_manager.particles.empty()

        
        drone = Player((200, SCREEN_HEIGHT // 2))
        player_group.add(drone)
        spawner = Spawner(base_min_interval=1.5, base_max_interval=3.0)
        spawner.set_level(current_level)

    def start_next_level():
        nonlocal current_level, level_score, game_state, battery_timer
        current_level += 1
        level_score = 0
        battery_timer = 0.0
        bullet_group.empty()
        target_group.empty()
        powerup_group.empty()
        particle_manager.particles.empty()

        spawner.set_level(current_level)
        game_state = STATE_PLAYING

    reset_game()

    # Main Loop
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        background.update(dt)

        # Always update particle animation during Level Clear celebration
        if game_state == STATE_LEVEL_CLEAR:
            particle_manager.update(dt)

        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # State Transitions
                if game_state == STATE_MENU:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        reset_game()
                        game_state = STATE_PLAYING

                elif game_state == STATE_LEVEL_CLEAR:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_s):
                        start_next_level()

                elif game_state == STATE_GAME_OVER:
                    if event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_s):
                        reset_game()
                        game_state = STATE_PLAYING

        # Shooting Event
            if game_state == STATE_PLAYING and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                new_bullets = drone.shoot(pygame.mouse.get_pos(), level=current_level)
                if new_bullets:
                    for b in new_bullets:
                        bullet_group.add(b)
                    audio_manager.play_laser()

        # Update Logic per State
        if game_state == STATE_PLAYING:
            points_per_level = 200 + (current_level - 1) * 100

            # Continuous automatic fire when holding left click
            if pygame.mouse.get_pressed()[0]:
                new_bullets = drone.shoot(pygame.mouse.get_pos(), level=current_level)
                if new_bullets:
                    for b in new_bullets:
                        bullet_group.add(b)
                    audio_manager.play_laser()

            # Periodic Battery Powerup Spawner (Every 7.0 seconds)
            battery_timer += dt
            if battery_timer >= 7.0:
                battery_timer = 0.0
                powerup_group.add(BatteryCharge())

            # Update Entities
            drone.update(dt, particle_manager, audio_manager)
            bullet_group.update(dt)
            target_group.update(dt)
            powerup_group.update(dt)
            particle_manager.update(dt)
            spawner.update(dt, target_group)

            # Bullet vs Target Collisions
            hits = pygame.sprite.groupcollide(bullet_group, target_group, True, False, pygame.sprite.collide_circle)
            for bullet, targets_hit in hits.items():
                for target in targets_hit:
                    # Apply damage to target
                    destroyed = target.take_damage(1)
                    particle_manager.spawn_explosion(target.rect.center, count=15, color=target.color_outer)
                    audio_manager.play_explosion()

                    if destroyed:
                        target.kill()
                        level_score += target.points
                        total_score += target.points

                        # 35% Chance of dropping Battery Charge when destroying targets
                        if random.random() < 0.35:
                            powerup_group.add(BatteryCharge(pos=target.rect.center))

                        # High Score Check
                        if total_score > highscore:
                            highscore = total_score
                            save_highscore(highscore)

                        # Level Completion Check
                        if level_score >= points_per_level:
                            game_state = STATE_LEVEL_CLEAR
                            bullet_group.empty()
                            target_group.empty()
                            powerup_group.empty()
                            particle_manager.spawn_celebration(SCREEN_WIDTH, SCREEN_HEIGHT)
                            audio_manager.play_celebration_fanfare()
                            break

            # Drone vs Battery Powerup Collection
            if game_state == STATE_PLAYING:
                powerup_hits = pygame.sprite.spritecollide(drone, powerup_group, True, pygame.sprite.collide_circle)
                for _ in powerup_hits:
                    drone.recharge_battery(30) # +30% Battery Recharge
                    audio_manager.play_recharge()
                    particle_manager.spawn_explosion(drone.rect.center, count=20, color=(52, 211, 153))

            # Drone vs Target Collisions (Health / Battery System)
            if game_state == STATE_PLAYING:
                drone_hits = pygame.sprite.spritecollide(drone, target_group, True, pygame.sprite.collide_circle)
                for target in drone_hits:
                    particle_manager.spawn_explosion(target.rect.center, count=25, color=(239, 68, 68))
                    audio_manager.play_explosion()
                    dead = drone.take_damage(25) # 25% health damage
                    if dead:
                        game_state = STATE_GAME_OVER
                        audio_manager.play_gameover()

        # Rendering
        screen.fill(COLOR_BG)
        background.draw(screen)

        if game_state in (STATE_PLAYING, STATE_LEVEL_CLEAR, STATE_GAME_OVER):
            player_group.draw(screen)
            bullet_group.draw(screen)
            target_group.draw(screen)
            powerup_group.draw(screen)
            particle_manager.draw(screen)

            # --- HUD Overlay ---
            current_fps = int(clock.get_fps())
            points_per_level = 200 + (current_level - 1) * 100
            
            lvl_surf = font_hud.render(f"LEVEL {current_level}", True, COLOR_GOLD)
            prog_surf = font_hud.render(f"Progress: {level_score}/{points_per_level} pts", True, COLOR_HUD)
            score_surf = font_hud.render(f"Score: {total_score}", True, COLOR_HUD)
            high_surf = font_hud.render(f"HI-SCORE: {highscore}", True, COLOR_CYAN)
            fps_surf = font_hud.render(f"FPS: {current_fps}", True, COLOR_EMERALD)

            screen.blit(lvl_surf, (20, 15))
            screen.blit(prog_surf, (150, 15))
            screen.blit(score_surf, (420, 15))
            screen.blit(high_surf, (600, 15))
            screen.blit(fps_surf, (SCREEN_WIDTH - 120, 15))

            # Drone Health / Battery Bar
            bar_w, bar_h = 200, 16
            bar_x, bar_y = 20, 48
            pygame.draw.rect(screen, (30, 41, 59), (bar_x, bar_y, bar_w, bar_h))
            health_pct = max(0.0, drone.health / drone.max_health)
            health_color = COLOR_EMERALD if health_pct > 0.4 else (239, 68, 68)
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, int(bar_w * health_pct), bar_h))
            pygame.draw.rect(screen, COLOR_HUD, (bar_x, bar_y, bar_w, bar_h), 2)
            
            hp_txt = font_hud.render(f"BATTERY: {int(drone.health)}%", True, COLOR_HUD)
            screen.blit(hp_txt, (bar_x + bar_w + 12, bar_y - 2))

        # --- Celebration Screen (Level Clear) ---
        if game_state == STATE_LEVEL_CLEAR:
            points_per_level = 200 + (current_level - 1) * 100
            clear_surf = font_banner.render(f"🎉 LEVEL {current_level} CLEARED! 🎉", True, COLOR_CYAN)
            detail_surf = font_hud.render(f"Level Goal Achieved: {points_per_level} / {points_per_level} pts  |  Total Score: {total_score}", True, COLOR_GOLD)
            start_next_surf = font_banner.render(f"Press SPACE or 'S' to Start Level {current_level + 1}", True, COLOR_EMERALD)

            screen.blit(clear_surf, clear_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
            screen.blit(detail_surf, detail_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))
            screen.blit(start_next_surf, start_next_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)))

        # --- Menu Screens ---
        elif game_state == STATE_MENU:
            title_surf = font_title.render("DRONE HUNTER", True, COLOR_CYAN)
            subtitle_surf = font_hud.render("Sci-Fi 2D Arcade Side-Scroller", True, (148, 163, 184))
            high_surf = font_banner.render(f"HIGH SCORE: {highscore}", True, COLOR_GOLD)
            start_surf = font_banner.render("Press SPACE to Play", True, COLOR_EMERALD)
            controls_surf = font_hud.render("Arrows / WASD / Space: Flight | Mouse: Aim & Left Click: Shoot", True, COLOR_HUD)

            screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 200)))
            screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 270)))
            screen.blit(high_surf, high_surf.get_rect(center=(SCREEN_WIDTH // 2, 350)))
            screen.blit(start_surf, start_surf.get_rect(center=(SCREEN_WIDTH // 2, 450)))
            screen.blit(controls_surf, controls_surf.get_rect(center=(SCREEN_WIDTH // 2, 560)))

        elif game_state == STATE_GAME_OVER:
            over_surf = font_gameover.render("GAME OVER", True, (239, 68, 68))
            stats_surf = font_hud.render(f"Final Level: {current_level}  |  Total Score: {total_score}  |  High Score: {highscore}", True, COLOR_HUD)
            restart_surf = font_banner.render("Press R or SPACE to Restart", True, COLOR_CYAN)

            screen.blit(over_surf, over_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
            screen.blit(stats_surf, stats_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))
            screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 65)))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
