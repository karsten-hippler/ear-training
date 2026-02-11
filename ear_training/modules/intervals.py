"""Interval recognition training module."""

from typing import List, Tuple
from enum import Enum
import random
import numpy as np


class Interval(Enum):
    """Musical intervals."""
    UNISON = 0
    MINOR_SECOND = 1
    MAJOR_SECOND = 2
    MINOR_THIRD = 3
    MAJOR_THIRD = 4
    PERFECT_FOURTH = 5
    AUGMENTED_FOURTH = 6
    PERFECT_FIFTH = 7
    MINOR_SIXTH = 8
    MAJOR_SIXTH = 9
    MINOR_SEVENTH = 10
    MAJOR_SEVENTH = 11
    OCTAVE = 12
    MINOR_NINTH = 13
    MAJOR_NINTH = 14
    MINOR_TENTH = 15
    MAJOR_TENTH = 16
    PERFECT_ELEVENTH = 17
    AUGMENTED_ELEVENTH = 18
    PERFECT_TWELFTH = 19
    MINOR_THIRTEENTH = 20
    MAJOR_THIRTEENTH = 21
    MINOR_FOURTEENTH = 22
    MAJOR_FOURTEENTH = 23
    TWO_OCTAVES = 24
    MINOR_SIXTEENTH = 25
    MAJOR_SIXTEENTH = 26
    PERFECT_SEVENTEENTH = 27
    MINOR_EIGHTEENTH = 28
    MAJOR_EIGHTEENTH = 29
    MINOR_NINETEENTH = 30
    MAJOR_NINETEENTH = 31
    PERFECT_TWENTIETH = 32
    MINOR_TWENTY_FIRST = 33
    MAJOR_TWENTY_FIRST = 34
    MINOR_TWENTY_SECOND = 35
    THREE_OCTAVES = 36


class IntervalTrainer:
    """Trains users on interval recognition."""
    
    def __init__(self, base_freq: float = 440.0):
        """Initialize interval trainer.
        
        Args:
            base_freq: Base frequency in Hz (default: A4 = 440 Hz)
        """
        self.base_freq = base_freq
        self.intervals = list(Interval)
        self.current_interval: Interval | None = None
        self.current_direction: str = "ascending"  # "ascending" or "descending"
        self.user_answer: Interval | None = None
    
    def generate_interval(self, 
                         interval_range: Tuple[int, int] | None = None) -> Interval:
        """Generate a random interval for training.
        
        Args:
            interval_range: Tuple of (min_semitones, max_semitones). 
                          If None, uses available Interval values.
        
        Returns:
            Selected interval
        """
        # Limit random pick to the intervals we actually support to avoid ValueError
        if interval_range is None:
            choices = self.intervals
        else:
            low, high = interval_range
            choices = [iv for iv in self.intervals if low <= iv.value <= high]
            if not choices:
                raise ValueError("No intervals available in requested range")
        
        self.current_interval = random.choice(choices)
        # Randomly choose direction (50% ascending, 50% descending)
        self.current_direction = random.choice(["ascending", "descending"])
        return self.current_interval
    
    def get_frequencies(self) -> Tuple[float, float]:
        """Get the two frequencies for current interval.
        
        Returns:
            Tuple of (base_frequency, interval_frequency)
        """
        if self.current_interval is None:
            raise ValueError("No interval generated yet")
        
        semitones = self.current_interval.value
        freq2 = self.base_freq * (2 ** (semitones / 12))
        return self.base_freq, freq2
    
    def submit_answer(self, interval: Interval) -> bool:
        """Submit user's interval guess.
        
        Args:
            interval: User's guessed interval
        
        Returns:
            True if correct, False otherwise
        """
        self.user_answer = interval
        return interval == self.current_interval
    
    def get_current_interval(self) -> Interval | None:
        """Get current interval being trained."""
        return self.current_interval
