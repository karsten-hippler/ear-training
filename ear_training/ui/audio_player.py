"""Audio playback utilities using pygame."""

from typing import List
import numpy as np
import pygame


class AudioPlayer:
    """Handles audio synthesis and playback with instrument-like sounds."""
    
    def __init__(self, sample_rate: int = 44100, duration: float = 0.5):
        """Initialize audio player.
        
        Args:
            sample_rate: Audio sample rate in Hz
            duration: Default duration of tones in seconds
        """
        self.sample_rate = sample_rate
        self.duration = duration
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2)
    
    def generate_sine_wave(self, frequency: float, 
                          duration: float | None = None) -> np.ndarray:
        """Generate a sine wave at given frequency.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds (default: self.duration)
        
        Returns:
            Numpy array of audio samples
        """
        if duration is None:
            duration = self.duration
        
        samples = np.arange(int(self.sample_rate * duration))
        waveform = np.sin(2 * np.pi * frequency * samples / self.sample_rate)
        return waveform * 0.3  # Scale to prevent clipping
    
    def generate_rich_tone(self, frequency: float, 
                          duration: float | None = None,
                          instrument: str = "piano") -> np.ndarray:
        """Generate a richer, more instrument-like tone with harmonics and envelope.
        
        Args:
            frequency: Fundamental frequency in Hz
            duration: Duration in seconds
            instrument: Instrument type - "piano", "bell", "violin", "flute"
        
        Returns:
            Numpy array of audio samples
        """
        if duration is None:
            duration = self.duration
        
        num_samples = int(self.sample_rate * duration)
        samples = np.arange(num_samples)
        t = samples / self.sample_rate
        
        # Start with fundamental
        waveform = np.zeros(num_samples)
        
        if instrument == "piano":
            # Piano: rich harmonics that decay
            harmonics = [
                (1.0, 1.0),      # Fundamental
                (2.0, 0.6),      # Octave
                (3.0, 0.3),      # Twelfth
                (4.0, 0.2),      # Double octave
            ]
            # Piano envelope: quick attack, long decay
            envelope = self._adsr_envelope(t, attack=0.01, decay=0.3, sustain=0.2, release=0.2)
        
        elif instrument == "bell":
            # Bell: inharmonic partials, long sustain, very different sound
            harmonics = [
                (0.9, 0.5),      # Slightly lower fundamental
                (1.2, 0.7),      # Inharmonic partial
                (2.1, 0.6),      # Different harmonic
                (3.5, 0.4),      # More inharmonic
            ]
            envelope = self._adsr_envelope(t, attack=0.15, decay=0.1, sustain=0.8, release=0.3)
        
        elif instrument == "violin":
            # Violin: bright, sustained, many harmonics
            harmonics = [
                (1.0, 1.0),
                (2.0, 0.9),      # Strong 2nd harmonic
                (3.0, 0.7),      # Strong 3rd
                (4.0, 0.5),
                (5.0, 0.3),
                (6.0, 0.2),
            ]
            envelope = self._adsr_envelope(t, attack=0.03, decay=0.05, sustain=0.9, release=0.1)
        
        elif instrument == "flute":
            # Flute: mellow, mostly fundamental, soft attack
            harmonics = [
                (1.0, 1.0),
                (2.0, 0.2),
                (3.0, 0.05),
            ]
            envelope = self._adsr_envelope(t, attack=0.15, decay=0.02, sustain=0.85, release=0.08)
        
        else:
            # Default: simple sine
            harmonics = [(1.0, 1.0)]
            envelope = np.ones(num_samples)
        
        # Combine harmonics
        for harmonic_ratio, amplitude in harmonics:
            freq = frequency * harmonic_ratio
            harmonic = np.sin(2 * np.pi * freq * t) * amplitude
            waveform += harmonic
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(waveform))
        if max_val > 0:
            waveform = waveform / max_val
        
        # Apply envelope and scale (reduced to 0.6 for less aggressive synthesis)
        waveform = waveform * envelope * 0.6
        
        return waveform
    
    def _adsr_envelope(self, t: np.ndarray, attack: float, decay: float, 
                      sustain: float, release: float) -> np.ndarray:
        """Generate ADSR (Attack, Decay, Sustain, Release) envelope.
        
        Args:
            t: Time array
            attack: Attack time in seconds
            decay: Decay time in seconds
            sustain: Sustain level (0-1)
            release: Release time in seconds
        
        Returns:
            Envelope array
        """
        envelope = np.ones_like(t)
        total_duration = t[-1]
        
        # Attack phase
        attack_mask = t <= attack
        if attack > 0:
            envelope[attack_mask] = t[attack_mask] / attack
        
        # Decay phase
        decay_start = attack
        decay_end = attack + decay
        decay_mask = (t > decay_start) & (t <= decay_end)
        if decay > 0:
            decay_t = t[decay_mask] - decay_start
            envelope[decay_mask] = 1.0 - (1.0 - sustain) * (decay_t / decay)
        
        # Sustain phase
        sustain_start = decay_end
        release_start = total_duration - release
        sustain_mask = (t > sustain_start) & (t <= release_start)
        envelope[sustain_mask] = sustain
        
        # Release phase
        release_mask = t > release_start
        if release > 0:
            release_t = t[release_mask] - release_start
            envelope[release_mask] = sustain * np.maximum(0, 1.0 - (release_t / release))
        
        return envelope
    
    def play_tone(self, frequency: float, duration: float | None = None,
                 instrument: str = "piano") -> None:
        """Play a single tone with instrument sound.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            instrument: Instrument type - "piano", "bell", "violin", "flute"
        """
        waveform = self.generate_rich_tone(frequency, duration, instrument)
        self._play_audio(waveform)
    
    def play_frequencies(self, frequencies: List[float], 
                        duration: float | None = None,
                        simultaneous: bool = True,
                        instrument: str = "piano") -> None:
        """Play multiple frequencies.
        
        Args:
            frequencies: List of frequencies in Hz
            duration: Duration in seconds
            simultaneous: If True, play frequencies simultaneously (chord).
                        If False, play sequentially.
            instrument: Instrument type
        """
        if simultaneous:
            waveform = np.zeros(int(self.sample_rate * (duration or self.duration)))
            for freq in frequencies:
                waveform += self.generate_rich_tone(freq, duration, instrument)
            self._play_audio(waveform)
        else:
            for freq in frequencies:
                self.play_tone(freq, duration, instrument)
    
    def _play_audio(self, waveform: np.ndarray) -> None:
        """Internal method to play audio from numpy array.
        
        Args:
            waveform: Numpy array of audio samples
        """
        # Convert to 16-bit PCM and normalize
        waveform = np.clip(waveform, -1.0, 1.0)
        waveform = np.int16(waveform * 32767)
        
        # Create stereo by duplicating mono channel
        stereo = np.zeros((len(waveform), 2), dtype=np.int16)
        stereo[:, 0] = waveform
        stereo[:, 1] = waveform
        
        sound = pygame.sndarray.make_sound(stereo)
        sound.play()

