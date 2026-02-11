"""Rhythm recognition training module."""

from typing import List, Tuple
from enum import Enum
import random
from dataclasses import dataclass


class NoteValue(Enum):
    """Musical note durations."""
    WHOLE = 4.0
    HALF = 2.0
    QUARTER = 1.0
    EIGHTH = 0.5
    SIXTEENTH = 0.25
    TRIPLET_QUARTER = 1.0 / 3
    TRIPLET_EIGHTH = 1.0 / 6


@dataclass
class RhythmPattern:
    """Represents a rhythm pattern."""
    notes: List[NoteValue]
    tempo: int  # BPM
    time_signature: Tuple[int, int]  # (numerator, denominator)
    
    def duration_in_seconds(self) -> float:
        """Calculate total duration in seconds."""
        beat_duration = 60 / self.tempo  # seconds per beat
        total_beats = sum(note.value for note in self.notes)
        return total_beats * beat_duration


class RhythmTrainer:
    """Trains users on rhythm recognition."""
    
    def __init__(self, tempo: int = 120):
        """Initialize rhythm trainer.
        
        Args:
            tempo: Default tempo in BPM
        """
        self.tempo = tempo
        self.current_pattern: RhythmPattern | None = None
        self.user_answer: List[NoteValue] | None = None
        self.note_values = list(NoteValue)
    
    def generate_pattern(self, 
                        length: int = 4,
                        time_signature: Tuple[int, int] = (4, 4),
                        allowed_notes: List[NoteValue] | None = None) -> RhythmPattern:
        """Generate a random rhythm pattern.
        
        Args:
            length: Number of beats in pattern
            time_signature: Musical time signature
            allowed_notes: List of allowed note values. If None, uses all.
        
        Returns:
            Generated rhythm pattern
        """
        if allowed_notes is None:
            allowed_notes = [NoteValue.QUARTER, NoteValue.EIGHTH, NoteValue.HALF]
        
        notes = []
        remaining_beats = length
        
        while remaining_beats > 0:
            note = random.choice(allowed_notes)
            if note.value <= remaining_beats:
                notes.append(note)
                remaining_beats -= note.value
            else:
                # Try to fit remaining beats
                allowed_notes_filtered = [n for n in allowed_notes if n.value <= remaining_beats]
                if not allowed_notes_filtered:
                    break
                note = random.choice(allowed_notes_filtered)
                notes.append(note)
                remaining_beats -= note.value
        
        self.current_pattern = RhythmPattern(
            notes=notes,
            tempo=self.tempo,
            time_signature=time_signature
        )
        return self.current_pattern
    
    def submit_answer(self, pattern: List[NoteValue]) -> bool:
        """Submit user's rhythm guess.
        
        Args:
            pattern: User's guessed rhythm pattern
        
        Returns:
            True if correct, False otherwise
        """
        if self.current_pattern is None:
            raise ValueError("No pattern generated yet")
        
        self.user_answer = pattern
        return pattern == self.current_pattern.notes
    
    def get_current_pattern(self) -> RhythmPattern | None:
        """Get current pattern being trained."""
        return self.current_pattern
