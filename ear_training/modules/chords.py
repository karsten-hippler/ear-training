"""Chord recognition training module."""

from typing import List, Tuple
from enum import Enum
import random


class ChordType(Enum):
    """Common chord types."""
    MAJOR = [0, 4, 7]
    MINOR = [0, 3, 7]
    DIMINISHED = [0, 3, 6]
    AUGMENTED = [0, 4, 8]
    MAJOR_SEVENTH = [0, 4, 7, 11]
    MINOR_SEVENTH = [0, 3, 7, 10]
    DOMINANT_SEVENTH = [0, 4, 7, 10]
    MINOR_MAJOR_SEVENTH = [0, 3, 7, 11]


class ChordTrainer:
    """Trains users on chord recognition."""
    
    def __init__(self, base_freq: float = 440.0):
        """Initialize chord trainer.
        
        Args:
            base_freq: Base frequency in Hz (default: A4 = 440 Hz)
        """
        self.base_freq = base_freq
        self.chord_types = list(ChordType)
        self.current_chord: ChordType | None = None
        self.user_answer: ChordType | None = None
    
    def generate_chord(self, 
                      chord_types: List[ChordType] | None = None) -> ChordType:
        """Generate a random chord for training.
        
        Args:
            chord_types: List of chord types to choose from.
                       If None, uses all available chord types.
        
        Returns:
            Selected chord type
        """
        if chord_types is None:
            chord_types = self.chord_types
        
        self.current_chord = random.choice(chord_types)
        return self.current_chord
    
    def get_frequencies(self) -> List[float]:
        """Get the frequencies for current chord.
        
        Returns:
            List of frequencies for chord notes
        """
        if self.current_chord is None:
            raise ValueError("No chord generated yet")
        
        intervals = self.current_chord.value
        frequencies = [
            self.base_freq * (2 ** (semitone / 12)) 
            for semitone in intervals
        ]
        return frequencies
    
    def submit_answer(self, chord_type: ChordType) -> bool:
        """Submit user's chord guess.
        
        Args:
            chord_type: User's guessed chord type
        
        Returns:
            True if correct, False otherwise
        """
        self.user_answer = chord_type
        return chord_type == self.current_chord
    
    def get_current_chord(self) -> ChordType | None:
        """Get current chord being trained."""
        return self.current_chord
