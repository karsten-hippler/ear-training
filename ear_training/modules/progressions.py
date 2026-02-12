"""Harmonic progression training module."""

from typing import List, Tuple
from enum import Enum
import random


class ChordNumber(Enum):
    """Roman numeral chord numbers for progressions."""
    I = (0, "major")      # Tonic
    II = (2, "minor")     # Supertonic
    III = (4, "minor")    # Mediant
    III7 = (4, "dominant7")  # Dominant seventh on III
    IV = (5, "major")     # Subdominant
    V = (7, "major")      # Dominant
    V7 = (7, "dominant7") # Dominant seventh on V
    VI = (9, "minor")     # Submediant
    VII = (11, "diminished")  # Leading tone


class ProgressionTrainer:
    """Trains users on harmonic chord progressions with proper voice leading."""
    
    def __init__(self, base_freq: float = 440.0):
        """Initialize progression trainer.
        
        Args:
            base_freq: Base frequency in Hz (default: A4 = 440 Hz)
        """
        self.base_freq = base_freq
        self.current_progression: List[ChordNumber] | None = None
        self.user_answer: List[ChordNumber] | None = None
        self.last_progression: List[ChordNumber] | None = None
        self.last_tonic_inversion: int | None = None
        
        # Common progressions for training
        self.common_progressions = [
            [ChordNumber.I, ChordNumber.IV],
            [ChordNumber.I, ChordNumber.II],


            [ChordNumber.I, ChordNumber.IV, ChordNumber.V],
            [ChordNumber.I, ChordNumber.V, ChordNumber.IV],
            [ChordNumber.I, ChordNumber.VI, ChordNumber.IV, ChordNumber.V],
            [ChordNumber.I, ChordNumber.IV, ChordNumber.I, ChordNumber.V],
            [ChordNumber.I, ChordNumber.IV, ChordNumber.V, ChordNumber.I],
            [ChordNumber.VI, ChordNumber.IV, ChordNumber.I, ChordNumber.V],
            [ChordNumber.I, ChordNumber.V, ChordNumber.VI, ChordNumber.IV],
            [ChordNumber.I, ChordNumber.III, ChordNumber.VI, ChordNumber.IV, ChordNumber.V],
            [ChordNumber.I, ChordNumber.II, ChordNumber.V],
            [ChordNumber.I, ChordNumber.V, ChordNumber.I],
        ]
    
    def generate_progression(self, num_chords: int | None = None, start_on_tonic: bool = True, use_common_only: bool = False) -> List[ChordNumber]:
        """Generate a random chord progression.
        
        Args:
            num_chords: Number of chords in progression.
                       If None, randomly selects from 2-5 chords.
            start_on_tonic: If True, progression always starts with I (tonic).
                           If False, progression can start on any chord.
            use_common_only: If True, select from predefined common progressions.
                            If False, generate progressions probabilistically.
        
        Returns:
            List of ChordNumber enums representing the progression
        """
        if use_common_only:
            # Select a random common progression that differs from the last one
            progression = random.choice(self.common_progressions)
            while progression == self.last_progression:
                progression = random.choice(self.common_progressions)
            self.last_progression = progression
            self.current_progression = progression
            return progression
        
        if num_chords is None:
            num_chords = random.randint(2, 5)
        
        # Generate progression, ensuring it differs from the last one
        while True:
            # Start with tonic or random chord based on parameter
            if start_on_tonic:
                progression = [ChordNumber.I]
            else:
                progression = [random.choice(list(ChordNumber))]
            
            # Generate remaining chords with voice leading constraints
            while len(progression) < num_chords:
                last_chord = progression[-1]
                # Choose next chord based on voice leading principles
                next_chord = self._choose_next_chord(last_chord)
                progression.append(next_chord)
            
            # Check if this progression is different from the last one
            if progression != self.last_progression:
                break
        
        self.last_progression = progression
        self.current_progression = progression
        return progression
    
    def _choose_next_chord(self, current_chord: ChordNumber) -> ChordNumber:
        """Choose the next chord with proper voice leading.
        
        Voice leading principles:
        - Prefer smooth transitions (smallest root movement)
        - Prefer authentic/plagal cadences
        - Avoid tritone and large leaps when possible
        
        Args:
            current_chord: Current chord number
        
        Returns:
            Next chord number
        """
        current_root = current_chord.value[0]
        
        # Voice leading preferences based on current chord
        voice_leading_preferences = {
            ChordNumber.I: [ChordNumber.IV, ChordNumber.V, ChordNumber.V7, ChordNumber.VI, ChordNumber.II, ChordNumber.III, ChordNumber.III7, ChordNumber.VII],
            ChordNumber.II: [ChordNumber.V, ChordNumber.V7, ChordNumber.IV, ChordNumber.VII],
            ChordNumber.III: [ChordNumber.VI, ChordNumber.III7, ChordNumber.IV, ChordNumber.I],
            ChordNumber.III7: [ChordNumber.VI, ChordNumber.IV, ChordNumber.I],
            ChordNumber.IV: [ChordNumber.I, ChordNumber.V, ChordNumber.V7, ChordNumber.II],
            ChordNumber.V: [ChordNumber.I, ChordNumber.VI, ChordNumber.IV, ChordNumber.VII],
            ChordNumber.V7: [ChordNumber.I, ChordNumber.VI, ChordNumber.IV, ChordNumber.VII],
            ChordNumber.VI: [ChordNumber.IV, ChordNumber.I, ChordNumber.II, ChordNumber.III, ChordNumber.III7],
            ChordNumber.VII: [ChordNumber.I],
        }
        
        preferred_chords = voice_leading_preferences.get(current_chord, list(ChordNumber))
        return random.choice(preferred_chords)
    
    def get_chord_notes(self, chord: ChordNumber, inversion: int = 0) -> List[int]:
        """Get the semitone intervals for a chord.
        
        Args:
            chord: ChordNumber enum
            inversion: 0 for root position, 1 for first inversion, 2 for second inversion
        
        Returns:
            List of semitone intervals from root
        """
        root = chord.value[0]
        chord_type = chord.value[1]
        
        # Define intervals for each chord type
        intervals = {
            "major": [0, 4, 7],
            "minor": [0, 3, 7],
            "diminished": [0, 3, 6],
            "dominant7": [0, 4, 7, 10],
        }

        chord_intervals = intervals.get(chord_type, [0, 4, 7])

        # Apply inversion. For triads (3 notes) we support root, 1st, 2nd inversion.
        # For seventh chords (4 notes) we support root through 3rd inversion.
        n = len(chord_intervals)
        inversion = inversion % n  # safety guard

        if inversion > 0:
            rotated = chord_intervals[inversion:] + [i + 12 for i in chord_intervals[:inversion]]
            chord_intervals = rotated

        return [root + interval for interval in chord_intervals]
    
    def get_progression_frequencies(self, 
                                   base_octave: int = 4,
                                   use_inversions: bool = True) -> List[List[float]]:
        """Get frequencies for all chords in current progression with voice leading.
        
        Args:
            base_octave: Octave for tonic note
            use_inversions: If True, use inversions for smoother voice leading
        
        Returns:
            List of frequency lists, one per chord in progression
        """
        if self.current_progression is None:
            raise ValueError("No progression generated yet")
        
        all_frequencies = []
        previous_notes = None
        
        for i, chord in enumerate(self.current_progression):
            inversion = 0
            
            # For the first chord (tonic), select an inversion based on the second chord
            if i == 0 and len(self.current_progression) > 1:
                next_chord = self.current_progression[1]
                inversion = self._select_best_inversion_for_next(chord, next_chord, base_octave)
            # For subsequent chords, determine best inversion for voice leading if enabled
            elif use_inversions and previous_notes is not None:
                inversion = self._select_best_inversion(chord, previous_notes, base_octave)
            
            chord_notes = self.get_chord_notes(chord, inversion)
            
            # Convert semitone intervals to frequencies
            frequencies = []
            for note_semitone in chord_notes:
                # Adjust octave for higher notes
                octave = base_octave + (note_semitone // 12)
                note_in_octave = note_semitone % 12
                
                # Calculate frequency from A4 (440 Hz)
                semitones_from_a4 = (octave - 4) * 12 + note_in_octave - 9  # A=9 semitones from C
                frequency = self.base_freq * (2 ** (semitones_from_a4 / 12))
                frequencies.append(frequency)
            
            frequencies.sort()  # Sort for proper chord voicing
            all_frequencies.append(frequencies)
            previous_notes = chord_notes
        
        return all_frequencies
    
    def _select_best_inversion_for_next(self, 
                                        chord: ChordNumber,
                                        next_chord: ChordNumber,
                                        base_octave: int) -> int:
        """Select the inversion of current chord that best leads to next chord.
        Avoids using the same inversion as the last progression's tonic.
        
        Args:
            chord: Current chord
            next_chord: Next chord
            base_octave: Base octave for reference
        
        Returns:
            Best inversion (0, 1, or 2)
        """
        best_inversion = 0
        best_distance = float('inf')
        
        # Get average note of next chord in root position
        next_chord_notes = self.get_chord_notes(next_chord, 0)
        next_avg = sum(next_chord_notes) / len(next_chord_notes)

        # Determine how many inversions this chord supports (triad vs seventh)
        base_notes = self.get_chord_notes(chord, 0)
        num_inversions = len(base_notes)  # 3 for triads, 4 for sevenths

        # Collect all inversions with their distances
        inversions_with_distance = []
        for inversion in range(num_inversions):
            chord_notes = self.get_chord_notes(chord, inversion)
            current_avg = sum(chord_notes) / len(chord_notes)
            
            # Calculate distance
            distance = abs(current_avg - next_avg)
            inversions_with_distance.append((inversion, distance))
        
        # Sort by distance
        inversions_with_distance.sort(key=lambda x: x[1])
        
        # Pick the best inversion that's different from the last one
        for inversion, distance in inversions_with_distance:
            if inversion != self.last_tonic_inversion:
                best_inversion = inversion
                break
        else:
            # If all inversions are the same as last time (shouldn't happen with 3 options),
            # just use the best one
            best_inversion = inversions_with_distance[0][0]
        
        # Remember this tonic inversion for next time
        self.last_tonic_inversion = best_inversion
        return best_inversion
    
    def _select_best_inversion(self, 
                               chord: ChordNumber,
                               previous_notes: List[int],
                               base_octave: int) -> int:
        """Select the inversion that minimizes voice leading distance.
        
        Args:
            chord: Current chord
            previous_notes: Semitone values of previous chord notes
            base_octave: Base octave for reference
        
        Returns:
            Best inversion (0, 1, or 2)
        """
        best_inversion = 0
        best_distance = float('inf')
        
        previous_avg = sum(previous_notes) / len(previous_notes)

        base_notes = self.get_chord_notes(chord, 0)
        num_inversions = len(base_notes)

        for inversion in range(num_inversions):
            chord_notes = self.get_chord_notes(chord, inversion)
            current_avg = sum(chord_notes) / len(chord_notes)
            
            # Calculate distance
            distance = abs(current_avg - previous_avg)
            
            if distance < best_distance:
                best_distance = distance
                best_inversion = inversion
        
        return best_inversion
    
    def submit_answer(self, user_progression: List[ChordNumber]) -> bool:
        """Submit user's progression guess.
        
        Args:
            user_progression: User's guessed progression
        
        Returns:
            True if correct, False otherwise
        """
        self.user_answer = user_progression
        return user_progression == self.current_progression
    
    def get_current_progression(self) -> List[ChordNumber] | None:
        """Get current progression being trained."""
        return self.current_progression
    
    def get_progression_string(self, progression: List[ChordNumber]) -> str:
        """Get string representation of progression (Roman numerals).
        
        Args:
            progression: List of ChordNumbers
        
        Returns:
            String like "I - IV - V - I"
        """
        return " - ".join([chord.name for chord in progression])
