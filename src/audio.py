"""
================================================================================
                    DRONE HUNTER - PROCEDURAL AUDIO MODULE
================================================================================
Zero-dependency procedural sound synthesizer & synthwave background music sequencer.
Supports both 2D and 3D engine interfaces + Environmental Ambient Audio.
"""

import math
import random
import pygame

bgm_beat_timer = 0.0
bgm_step = 0
BASS_FREQS = [110, 110, 146, 130, 110, 110, 164, 146]

ambient_timer = 0.0

def play_synth_laser():
    try:
        sample_rate = 44100
        dur = 0.12
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 900 - 650 * (t / dur)
            val = int(math.sin(2 * math.pi * freq * t) * 12000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.25)
        snd.play()
    except Exception: pass

def play_synth_explosion():
    try:
        sample_rate = 44100
        dur = 0.35
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            val = int((random.random() * 2 - 1) * 18000 * (1.0 - t/dur)**1.8)
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.4)
        snd.play()
    except Exception: pass

def play_synth_mine_explosion():
    try:
        sample_rate = 44100
        dur = 0.55
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            val = int((random.random() * 2 - 1) * 24000 * (1.0 - t/dur)**1.5)
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.55)
        snd.play()
    except Exception: pass

def play_synth_roll():
    try:
        sample_rate = 44100
        dur = 0.25
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 300 + 500 * math.sin(t * 20.0)
            val = int(math.sin(2 * math.pi * freq * t) * 14000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.3)
        snd.play()
    except Exception: pass

def play_synth_powerup():
    try:
        sample_rate = 44100
        dur = 0.20
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 500 + 700 * (t / dur)
            val = int(math.sin(2 * math.pi * freq * t) * 13000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.35)
        snd.play()
    except Exception: pass

def play_synth_emp():
    try:
        sample_rate = 44100
        dur = 0.45
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 1200 - 950 * (t / dur)
            val = int((math.sin(2 * math.pi * freq * t) + (random.random() * 0.3)) * 15000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.4)
        snd.play()
    except Exception: pass

def play_synth_thrust():
    try:
        sample_rate = 44100
        dur = 0.08
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            val = int((random.random() * 2 - 1) * 8000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.15)
        snd.play()
    except Exception: pass

def play_synth_buy():
    try:
        sample_rate = 44100
        dur = 0.18
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 587 if t < dur / 2 else 880
            val = int(math.sin(2 * math.pi * freq * t) * 12000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.3)
        snd.play()
    except Exception: pass

def play_synth_fanfare():
    try:
        sample_rate = 44100
        dur = 0.50
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        notes = [523.25, 659.25, 783.99, 1046.50]
        for i in range(n_samples):
            t = i / sample_rate
            note_idx = min(3, int((t / dur) * 4))
            freq = notes[note_idx]
            val = int(math.sin(2 * math.pi * freq * t) * 14000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.35)
        snd.play()
    except Exception: pass

def play_synth_gameover():
    try:
        sample_rate = 44100
        dur = 0.60
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 400 - 300 * (t / dur)
            val = int((math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * (freq * 0.5) * t)) * 16000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.4)
        snd.play()
    except Exception: pass

def play_synth_shield():
    try:
        sample_rate = 44100
        dur = 0.25
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 600 + 600 * (t / dur)
            val = int(math.sin(2 * math.pi * freq * t) * 12000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.3)
        snd.play()
    except Exception: pass

def play_synth_recharge():
    try:
        sample_rate = 44100
        dur = 0.15
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 700 + 300 * math.sin(t * 40.0)
            val = int(math.sin(2 * math.pi * freq * t) * 10000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.25)
        snd.play()
    except Exception: pass

def play_synth_missile():
    try:
        sample_rate = 44100
        dur = 0.22
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 250 + 650 * (t / dur)
            val = int((math.sin(2 * math.pi * freq * t) + random.random()*0.2) * 14000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.35)
        snd.play()
    except Exception: pass

def play_synth_beam():
    try:
        sample_rate = 44100
        dur = 0.06
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 1100 + 200 * math.sin(t * 80.0)
            val = int(math.sin(2 * math.pi * freq * t) * 9000)
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.20)
        snd.play()
    except Exception: pass

def play_synth_cloak():
    try:
        sample_rate = 44100
        dur = 0.35
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 950 - 550 * (t / dur)
            val = int(math.sin(2 * math.pi * freq * t) * 10000 * (1.0 - t/dur))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.30)
        snd.play()
    except Exception: pass

def play_synth_ocean_wave():
    """Ambient ocean storm wave roaring sound."""
    try:
        sample_rate = 44100
        dur = 0.40
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            val = int((random.random() * 2 - 1) * 7000 * math.sin(math.pi * (t / dur)))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.18)
        snd.play()
    except Exception: pass

def play_synth_desert_wind():
    """Ambient desert sand wind howl sound."""
    try:
        sample_rate = 44100
        dur = 0.45
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            freq = 140 + 80 * math.sin(t * 12.0)
            val = int((math.sin(2 * math.pi * freq * t) + random.random() * 0.4) * 6000 * math.sin(math.pi * (t / dur)))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.16)
        snd.play()
    except Exception: pass

def play_synth_factory_hum():
    """Ambient industrial factory mechanical hum sound."""
    try:
        sample_rate = 44100
        dur = 0.30
        n_samples = int(sample_rate * dur)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            val = int((math.sin(2 * math.pi * 60.0 * t) * 5000 + math.sin(2 * math.pi * 120.0 * t) * 3000))
            val = max(-32768, min(32767, val))
            buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.15)
        snd.play()
    except Exception: pass

def play_synthwave_bgm_tick(dt):
    global bgm_beat_timer, bgm_step
    bgm_beat_timer += dt
    if bgm_beat_timer >= 0.16:
        bgm_beat_timer = 0.0
        bgm_step = (bgm_step + 1) % 8
        try:
            sample_rate = 44100
            dur = 0.12
            n_samples = int(sample_rate * dur)
            buf = bytearray(n_samples * 2)
            freq = BASS_FREQS[bgm_step]
            for i in range(n_samples):
                t = i / sample_rate
                val = int((math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * (freq*2) * t)) * 4500 * (1.0 - t/dur))
                val = max(-32768, min(32767, val))
                buf[i*2:i*2+2] = val.to_bytes(2, byteorder='little', signed=True)
            snd = pygame.mixer.Sound(buffer=bytes(buf))
            snd.set_volume(0.12)
            snd.play()
        except Exception: pass

class AudioManager:
    """Audio Manager wrapping procedural sound synthesizer for Drone Hunter 2D & 3D."""
    def __init__(self):
        self.sound_enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except Exception:
            self.sound_enabled = False

    def play_laser(self):
        if self.sound_enabled: play_synth_laser()
    def play_explosion(self):
        if self.sound_enabled: play_synth_explosion()
    def play_mine_explosion(self):
        if self.sound_enabled: play_synth_mine_explosion()
    def play_roll(self):
        if self.sound_enabled: play_synth_roll()
    def play_powerup(self):
        if self.sound_enabled: play_synth_powerup()
    def play_emp(self):
        if self.sound_enabled: play_synth_emp()
    def play_thrust(self):
        if self.sound_enabled: play_synth_thrust()
    def play_buy(self):
        if self.sound_enabled: play_synth_buy()
    def play_celebration_fanfare(self):
        if self.sound_enabled: play_synth_fanfare()
    def play_gameover(self):
        if self.sound_enabled: play_synth_gameover()
    def play_shield(self):
        if self.sound_enabled: play_synth_shield()
    def play_recharge(self):
        if self.sound_enabled: play_synth_recharge()
    def play_missile(self):
        if self.sound_enabled: play_synth_missile()
    def play_beam(self):
        if self.sound_enabled: play_synth_beam()
    def play_cloak(self):
        if self.sound_enabled: play_synth_cloak()
    def play_hit(self):
        if self.sound_enabled: play_synth_laser()
    def play_impact(self):
        if self.sound_enabled: play_synth_laser()

    def play_sector_ambient(self, sector_idx: int):
        if not self.sound_enabled: return
        if sector_idx == 3: play_synth_ocean_wave()
        elif sector_idx == 4: play_synth_desert_wind()
        elif sector_idx == 1: play_synth_factory_hum()

    def update_bgm(self, dt: float = 0.016):
        if self.sound_enabled:
            play_synthwave_bgm_tick(dt)
