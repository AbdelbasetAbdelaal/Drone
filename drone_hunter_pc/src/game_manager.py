import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_HUD,
)
from src.player import Player
from src.target import Spawner

class GameManager:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.score = 0
        self.health = 100
        self.game_over = False

        # Sprite Groups
        self.player_group = pygame.sprite.GroupSingle()
        self.bullets = pygame.sprite.Group()
        self.targets = pygame.sprite.Group()

        # Initialize Player Drone
        self.player = Player((200, SCREEN_HEIGHT // 2))
        self.player_group.add(self.player)

        # Target Spawner (spawns targets every 1.5 to 3.0 seconds)
        self.spawner = Spawner(min_interval=1.5, max_interval=3.0)

    def handle_input(self, event: pygame.Event):
        if self.game_over:
            return

        # Firing weapon on Left Mouse Click event
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._try_shoot()

        # Handle Pygame event-based spawner if configured
        self.spawner.handle_event(event, self.targets)

    def update(self, dt: float):
        if self.game_over:
            return

        # Continuous automatic fire when holding Left Mouse Button
        if pygame.mouse.get_pressed()[0]:
            self._try_shoot()

        # Update all sprite groups using delta time
        self.player_group.update(dt)
        self.bullets.update(dt)
        self.targets.update(dt)

        # Update Spawner (spawns target at dynamic 1.5s - 3s intervals)
        self.spawner.update(dt, self.targets)

        # Check Collisions
        self._check_collisions()

    def _try_shoot(self):
        mouse_pos = pygame.mouse.get_pos()
        bullet = self.player.shoot(mouse_pos)
        if bullet:
            self.bullets.add(bullet)

    def _check_collisions(self):
        # 1. Bullets hitting Targets
        hits = pygame.sprite.groupcollide(self.bullets, self.targets, True, True, pygame.sprite.collide_circle)
        for _ in hits:
            self.score += 100

        # 2. Targets colliding with Player Drone
        player_hits = pygame.sprite.spritecollide(self.player, self.targets, True, pygame.sprite.collide_circle)
        for _ in player_hits:
            self.health -= 25
            if self.health <= 0:
                self.health = 0
                self.game_over = True

    def draw(self, surface: pygame.Surface):
        # Draw game entities
        self.player_group.draw(surface)
        self.bullets.draw(surface)
        self.targets.draw(surface)

        # Draw HUD Overlay
        self._draw_hud(surface)

    def _draw_hud(self, surface: pygame.Surface):
        score_surf = self.font.render(f"Score: {self.score}", True, COLOR_HUD)
        health_surf = self.font.render(f"Health: {self.health}%", True, COLOR_HUD)
        controls_surf = self.font.render("Space: Thrust | A/D: Move | Left Click: Aim & Shoot", True, (148, 163, 184))

        surface.blit(score_surf, (20, 20))
        surface.blit(health_surf, (20, 50))
        surface.blit(controls_surf, (20, SCREEN_HEIGHT - 40))

        if self.game_over:
            over_surf = self.font.render("GAME OVER - Press R to Restart", True, (239, 68, 68))
            rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(over_surf, rect)
