import math
import random
import pygame

class AudioManager:
    """
    Manages realistic audio synthesis for gunfire/shooting, deep explosive booms,
    celebration fanfare/cheer, and thrusters using multi-harmonic waveform synthesis.
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
        self.recharge_sfx = self._create_recharge_sound()
        self.celebration_sfx = self._create_celebration_cheer_sound()
        self.gameover_sfx = self._create_gameover_sound()

    def _create_recharge_sound(self) -> pygame.mixer.Sound | None:
        """Synthesizes an uplifting high-tech battery recharge chime."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.28
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Frequency sweeps up from 400Hz to 1200Hz
                freq = 400.0 + (800.0 * (i / num_samples))
                decay = 1.0 - (i / num_samples) * 0.4
                sample_val = int(128 + 127 * 0.35 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_laser_sound(self) -> pygame.mixer.Sound | None:

        """Realistic punchy gunfire / plasma laser shot."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.14
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # Muzzle burst transient (first 8ms noise crackle)
                noise = random.randint(-60, 60) if progress < 0.08 else 0
                
                # Exponential pitch drop from 1400Hz to 160Hz
                freq = 1400.0 * math.exp(-18.0 * progress) + 160.0
                decay = math.exp(-12.0 * progress)
                
                # Main pulse + sub-bass punch
                tone = math.sin(2 * math.pi * freq * t)
                sub_bass = math.sin(2 * math.pi * 90.0 * t) * 0.4
                
                sample_val = int(128 + 127 * (0.6 * tone + sub_bass) * decay + noise * (1.0 - progress))
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_explosion_sound(self) -> pygame.mixer.Sound | None:
        """Realistic deep explosion boom with sub-bass rumble and shockwave crackle."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.48
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # Low-pass rumble noise
                noise = random.randint(-110, 110)
                # Deep sub-bass pulse (60Hz decaying to 30Hz)
                bass_freq = 60.0 * (1.0 - progress) + 30.0
                bass_tone = math.sin(2 * math.pi * bass_freq * t)
                
                # Exponential decay envelope
                decay = math.exp(-4.5 * progress)
                
                # Initial shockwave crackle (first 25ms)
                shockwave = random.randint(-80, 80) if progress < 0.05 else 0
                
                combined = (noise * 0.45 + bass_tone * 90.0 + shockwave) * decay
                sample_val = int(128 + combined)
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_thrust_sound(self) -> pygame.mixer.Sound | None:
        """Realistic engine jet thruster hum."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.09
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                noise = random.randint(-35, 35)
                freq = 110.0 + 25.0 * math.sin(2 * math.pi * 14 * t)
                tone = math.sin(2 * math.pi * freq * t)
                sample_val = int(128 + (tone * 40.0 + noise) * 0.8)
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_levelup_sound(self) -> pygame.mixer.Sound | None:
        """Realistic victory fanfare sound."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.6
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                if t < 0.1:
                    freq = 523.25
                elif t < 0.2:
                    freq = 659.25
                elif t < 0.3:
                    freq = 783.99
                elif t < 0.4:
                    freq = 1046.50
                else:
                    freq = 1318.51
                decay = 1.0 - (i / num_samples)
                sample = int(128 + 127 * 0.45 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_celebration_cheer_sound(self) -> pygame.mixer.Sound | None:
        """Realistic celebration fanfare with crowd cheer applause swell."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.85
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # Multi-harmonic victory chord (C5 + E5 + G5 -> C6 + E6 + G6)
                if t < 0.2:
                    f1, f2 = 523.25, 659.25  # C5 + E5
                elif t < 0.4:
                    f1, f2 = 659.25, 783.99  # E5 + G5
                elif t < 0.6:
                    f1, f2 = 783.99, 1046.50 # G5 + C6
                else:
                    f1, f2 = 1046.50, 1318.51 # C6 + E6
                
                # Crowd cheer applause noise swell
                cheer_swell = math.sin(math.pi * progress) * random.randint(-40, 40)
                
                decay = 1.0 - progress
                s1 = math.sin(2 * math.pi * f1 * t)
                s2 = math.sin(2 * math.pi * f2 * t)
                
                sample_val = int(128 + (127 * 0.35 * (s1 + s2) + cheer_swell) * decay)
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_gameover_sound(self) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.55
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                freq = 240.0 - (170.0 * (i / num_samples))
                decay = 1.0 - (i / num_samples)
                sample = int(128 + 127 * 0.45 * decay * math.sin(2 * math.pi * freq * t))
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

    def play_celebration_fanfare(self):
        if self.celebration_sfx:
            self.celebration_sfx.play()
        elif self.levelup_sfx:
            self.levelup_sfx.play()

    def play_recharge(self):
        if self.recharge_sfx:
            self.recharge_sfx.play()

    def play_gameover(self):
        if self.gameover_sfx:
            self.gameover_sfx.play()

