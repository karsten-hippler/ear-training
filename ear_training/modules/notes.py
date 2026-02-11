"""Note recognition training module."""

from typing import List
from enum import Enum
import random


class Note(Enum):
    """Musical notes (chromatic scale)."""
    C = 0
    C_SHARP = 1
    D = 2
    D_SHARP = 3
    E = 4
    F = 5
    F_SHARP = 6
    G = 7
    G_SHARP = 8
    A = 9
    A_SHARP = 10
    B = 11
    
    @property
    def display_name(self) -> str:
        """Get display name with proper sharp symbol."""
        name_map = {
            "C": "C",
            "C_SHARP": "C♯",
            "D": "D",
            "D_SHARP": "D♯",
            "E": "E",
            "F": "F",
            "F_SHARP": "F♯",
            "G": "G",
            "G_SHARP": "G♯",
            "A": "A",
            "A_SHARP": "A♯",
            "B": "B"
        }
        return name_map.get(self.name, self.name)


class NoteTrainer:
    """Trains users on absolute pitch / note recognition."""
    
    def __init__(self, base_freq: float = 440.0, octave: int = 4, octave_range: tuple[int, int] | None = None):
        """Initialize note trainer.
        
        Args:
            base_freq: Frequency of A4 in Hz (default: 440 Hz)
            octave: Which octave to use (default: 4)
            octave_range: Tuple of (min_octave, max_octave) for random generation (default: single octave)
        """
        self.base_freq = base_freq
        self.octave = octave
        self.octave_range = octave_range if octave_range else (octave, octave)
        self.notes = list(Note)
        self.reference_note: Note = Note.A  # Always start with A as reference
        self.current_note: Note | None = None
        self.current_octave: int | None = None
        self.user_answer: Note | None = None
    
    def get_note_frequency(self, note: Note, octave: int | None = None) -> float:
        """Calculate frequency for a given note.
        
        Args:
            note: The note to calculate frequency for
            octave: The octave (if None, uses self.octave)
        
        Returns:
            Frequency in Hz
        """
        if octave is None:
            octave = self.octave
        # A4 = 440 Hz is at index 9 (Note.A)
        # Calculate semitones from A4
        semitones_from_a4 = note.value - Note.A.value + (octave - 4) * 12
        frequency = self.base_freq * (2 ** (semitones_from_a4 / 12))
        return frequency
    
    def get_reference_note(self) -> tuple[Note, float]:
        """Get the reference note and its frequency.
        
        Returns:
            Tuple of (note, frequency)
        """
        return self.reference_note, self.get_note_frequency(self.reference_note)
    
    def generate_note(self, allowed_notes: list[Note] | None = None, max_interval: int | None = None) -> tuple[Note, int]:
        """Generate a random note for the user to guess.
        
        Args:
            allowed_notes: List of notes to choose from. If None, uses all notes.
            max_interval: Maximum interval in semitones from the previous note. If None, no limit.
        
        Returns:
            Tuple of (note, octave)
        """
        notes_to_choose = allowed_notes if allowed_notes else self.notes
        
        # If max_interval is specified and we have a previous note, constrain choices
        if max_interval is not None and self.current_note is not None and self.current_octave is not None:
            # Calculate valid octave range based on max_interval
            valid_octaves = []
            valid_notes = []
            
            for octave in range(self.octave_range[0], self.octave_range[1] + 1):
                for note in notes_to_choose:
                    # Calculate semitone distance
                    prev_semitone = self.current_note.value + (self.current_octave - 4) * 12
                    curr_semitone = note.value + (octave - 4) * 12
                    interval = abs(curr_semitone - prev_semitone)
                    
                    # Check if within max interval
                    if interval <= max_interval:
                        valid_notes.append((note, octave))
            
            if valid_notes:
                self.current_note, self.current_octave = random.choice(valid_notes)
            else:
                # If no valid notes, fall back to default behavior
                self.current_note = random.choice(notes_to_choose)
                self.current_octave = random.randint(self.octave_range[0], self.octave_range[1])
        else:
            # No constraint, random selection
            self.current_note = random.choice(notes_to_choose)
            self.current_octave = random.randint(self.octave_range[0], self.octave_range[1])
        return self.current_note, self.current_octave
    
    def get_current_frequency(self) -> float:
        """Get the frequency of the current note.
        
        Returns:
            Frequency in Hz
        """
        if self.current_note is None or self.current_octave is None:
            raise ValueError("No note generated yet")
        return self.get_note_frequency(self.current_note, self.current_octave)
    
    def submit_answer(self, note: Note, octave: int | None = None) -> bool:
        """Submit user's note guess.
        
        Args:
            note: User's guessed note
            octave: User's guessed octave (if None, only note is checked)
        
        Returns:
            True if correct, False otherwise
        """
        self.user_answer = note
        if octave is not None:
            return note == self.current_note and octave == self.current_octave
        else:
            return note == self.current_note
    
    def get_current_note(self) -> Note | None:
        """Get current note being trained."""
        return self.current_note
