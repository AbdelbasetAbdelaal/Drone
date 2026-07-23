import math
import pygame

class AudioManager:
    """
    Manages game audio, including sound effects (SFX) and synthesized 8-bit / Synthwave background music (BGM).
    """
    def __init__(self):
        self.audio_enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-8, channels=2, buffer=512)
            self.audio_enabled = True
        except Exception:
            self.audio_enabled = False

        # Generate Procedural Sound Effects
        self.laser_sfx = self._create_laser_sound()
        self.explosion_sfx = self._create_explosion_sound()
        self.thrust_sfx = self._create_thrust_sound()
        self.levelup_sfx = self._create_levelup_sound()
        self.gameover_sfx = self._create_gameover_sound()

    def _create_laser_sound(self) -> pygame.mixer.Sound | None:

        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.12
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Frequency sweep down from 800Hz to 200Hz
                freq = 800.0 - (600.0 * (i / num_samples))
                decay = 1.0 - (i / num_samples)
                sample = int(128 + 127 * 0.3 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_explosion_sound(self) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.25
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            import random
            for i in range(num_samples):
                decay = (1.0 - (i / num_samples)) ** 2
                noise = random.randint(-127, 127)
                sample = int(128 + noise * 0.4 * decay)
                buf.append(max(0, min(255, sample)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_thrust_sound(self) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.08
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                freq = 120.0 + 30.0 * math.sin(2 * math.pi * 15 * t)
                sample = int(128 + 90 * 0.2 * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_levelup_sound(self) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.35
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Arpeggio frequencies: C5 (523Hz) -> E5 (659Hz) -> G5 (784Hz)
                if t < 0.1:
                    freq = 523.25
                elif t < 0.2:
                    freq = 659.25
                else:
                    freq = 783.99
                decay = 1.0 - (i / num_samples)
                sample = int(128 + 127 * 0.35 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_gameover_sound(self) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.5
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                freq = 250.0 - (180.0 * (i / num_samples))
                decay = 1.0 - (i / num_samples)
                sample = int(128 + 127 * 0.4 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def play_laser(self):
        if self.laser_sfx:
            self.laser_sfx.play()

    def play_explosion(self):
        if self.explosion_sfx:
            self.explosion_sfx.play()

    def play_thrust(self):
        if self.thrust_sfx:
            self.thrust_sfx.play()

    def play_levelup(self):
        if self.levelup_sfx:
            self.levelup_sfx.play()

    def play_gameover(self):
        if self.gameover_sfx:
            self.gameover_sfx.play()
