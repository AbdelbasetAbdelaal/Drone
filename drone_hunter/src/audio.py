import math
import random
import pygame

class AudioManager:
    """
    Manages realistic audio synthesis for gunfire/shooting, deep explosive booms,
    EMP blasts, forcefield shields, celebration fanfare, and thrusters.
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
        self.emp_sfx = self._create_emp_sound()
        self.shield_sfx = self._create_shield_sound()
        self.celebration_sfx = self._create_celebration_cheer_sound()
        self.gameover_sfx = self._create_gameover_sound()

    def _create_laser_sound(self) -> pygame.mixer.Sound | None:
        """Thunderous Heavy Bomb Blast sound effect."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.38
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                
                # 1. Initial Bomb Detonation Shockwave (First 35ms explosive blast noise)
                bomb_detonation = random.randint(-127, 127) if progress < 0.10 else random.randint(-40, 40)
                
                # 2. Thunderous 35Hz Sub-Bass Bomb Boom
                sub_bomb_boom = math.sin(2 * math.pi * 35.0 * t) * 120.0
                
                # 3. Explosive Shockwave Frequency Pitch Drop (350Hz down to 45Hz)
                freq = 350.0 * math.exp(-15.0 * progress) + 45.0
                shockwave_pulse = math.sin(2 * math.pi * freq * t) * 75.0
                
                # 4. Heavy Bomb Reverb & Decay Envelope
                decay = math.exp(-5.5 * progress)
                
                # Combined Heavy Bomb Blast
                combined = (bomb_detonation * (1.0 - progress * 0.5) + sub_bomb_boom + shockwave_pulse) * decay
                sample_val = int(128 + max(-127, min(127, combined)))
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
                
                noise = random.randint(-110, 110)
                bass_freq = 60.0 * (1.0 - progress) + 30.0
                bass_tone = math.sin(2 * math.pi * bass_freq * t)
                decay = math.exp(-4.5 * progress)
                shockwave = random.randint(-80, 80) if progress < 0.05 else 0
                
                combined = (noise * 0.45 + bass_tone * 90.0 + shockwave) * decay
                sample_val = int(128 + combined)
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_thrust_sound(self) -> pygame.mixer.Sound | None:
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
                freq = 400.0 + (800.0 * (i / num_samples))
                decay = 1.0 - (i / num_samples) * 0.4
                sample_val = int(128 + 127 * 0.35 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_emp_sound(self) -> pygame.mixer.Sound | None:
        """Synthesizes a blinding electric EMP shockwave discharge blast."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.5
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                progress = i / num_samples
                freq = 1200.0 * math.exp(-12.0 * progress) + 80.0
                zap_noise = random.randint(-120, 120)
                decay = math.exp(-4.0 * progress)
                sample_val = int(128 + (127 * 0.4 * math.sin(2 * math.pi * freq * t) + zap_noise * 0.5) * decay)
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_shield_sound(self) -> pygame.mixer.Sound | None:
        """Synthesizes a forcefield shield activation chime."""
        if not self.audio_enabled:
            return None
        try:
            sample_rate = 22050
            duration = 0.35
            num_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                freq = 600.0 + (600.0 * (i / num_samples))
                decay = 1.0 - (i / num_samples) * 0.3
                sample_val = int(128 + 127 * 0.35 * decay * math.sin(2 * math.pi * freq * t))
                buf.append(max(0, min(255, sample_val)))
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _create_levelup_sound(self) -> pygame.mixer.Sound | None:
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
                if t < 0.2:
                    f1, f2 = 523.25, 659.25
                elif t < 0.4:
                    f1, f2 = 659.25, 783.99
                elif t < 0.6:
                    f1, f2 = 783.99, 1046.50
                else:
                    f1, f2 = 1046.50, 1318.51
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

    def play_emp(self):
        if self.emp_sfx:
            self.emp_sfx.play()

    def play_shield(self):
        if self.shield_sfx:
            self.shield_sfx.play()

    def play_recharge(self):
        if self.recharge_sfx:
            self.recharge_sfx.play()

    def play_gameover(self):
        if self.gameover_sfx:
            self.gameover_sfx.play()
