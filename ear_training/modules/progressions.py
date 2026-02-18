"""Harmonic progression training module."""

from typing import List, Tuple
from enum import Enum
import random


class ChordNumber(Enum):
    """Roman numeral chord numbers for progressions."""
    I = (0, "major")      # Tonic
    IMAJ7 = (0, "maj7")   # Major 7th on I
    II = (2, "minor")     # Supertonic
    IIM7 = (2, "m7")      # Minor 7th on II
    III = (4, "minor")    # Mediant
    IIIM7 = (4, "m7")     # Minor 7th on III
    IIIAUG = (4, "augmented")  # Augmented mediant
    III7 = (4, "dominant7")  # Dominant seventh on III
    IV = (5, "major")     # Subdominant
    IVMAJ7 = (5, "maj7")  # Major 7th on IV
    V = (7, "major")      # Dominant
    V7 = (7, "dominant7") # Dominant seventh on V
    VI = (9, "minor")     # Submediant
    VIM7 = (9, "m7")      # Minor 7th on VI
    VII = (11, "diminished")  # Leading tone
    VIIM7B5 = (11, "m7b5")  # Half-diminished 7th on VII


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
            [ChordNumber.I, ChordNumber.IIIAUG, ChordNumber.VI, ChordNumber.IV, ChordNumber.V],
            [ChordNumber.I, ChordNumber.II, ChordNumber.V],
            [ChordNumber.I, ChordNumber.V, ChordNumber.I],
            # Diatonic 7th chord progressions
            [ChordNumber.IMAJ7, ChordNumber.VI, ChordNumber.IIM7, ChordNumber.V7],
            [ChordNumber.IMAJ7, ChordNumber.IV, ChordNumber.V7],
            [ChordNumber.I, ChordNumber.VIM7, ChordNumber.IIM7, ChordNumber.V7],
            [ChordNumber.IMAJ7, ChordNumber.IVMAJ7, ChordNumber.V7, ChordNumber.IMAJ7],
            [ChordNumber.I, ChordNumber.VI, ChordNumber.IIM7, ChordNumber.V7],
            [ChordNumber.IMAJ7, ChordNumber.VI, ChordNumber.IV, ChordNumber.V7],
            # Minor key progressions (vi as minor tonic)
            [ChordNumber.VI, ChordNumber.IV, ChordNumber.V, ChordNumber.VI],
            [ChordNumber.VI, ChordNumber.VII, ChordNumber.VI],
            [ChordNumber.VI, ChordNumber.III, ChordNumber.VII, ChordNumber.VI],
            [ChordNumber.VI, ChordNumber.IV, ChordNumber.VII],
            [ChordNumber.VI, ChordNumber.I, ChordNumber.V],
            [ChordNumber.VI, ChordNumber.II, ChordNumber.V],
            [ChordNumber.VI, ChordNumber.IV, ChordNumber.I],
            [ChordNumber.VI, ChordNumber.IV, ChordNumber.V, ChordNumber.VII],
            [ChordNumber.VI, ChordNumber.II, ChordNumber.VII, ChordNumber.VI],
            # Minor key progressions with 7th chords (vi as minor tonic)
            [ChordNumber.VIM7, ChordNumber.IV, ChordNumber.V7, ChordNumber.VIM7],
            [ChordNumber.VI, ChordNumber.IIM7, ChordNumber.V7, ChordNumber.VI],
            [ChordNumber.VIM7, ChordNumber.IIM7, ChordNumber.V7],
            [ChordNumber.VI, ChordNumber.IVMAJ7, ChordNumber.V7, ChordNumber.VI],
            [ChordNumber.VIM7, ChordNumber.III, ChordNumber.V7, ChordNumber.VI],
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
            ChordNumber.I: [ChordNumber.IV, ChordNumber.V, ChordNumber.V7, ChordNumber.VI, ChordNumber.II, ChordNumber.III, ChordNumber.IIIAUG, ChordNumber.III7, ChordNumber.VII, ChordNumber.IMAJ7, ChordNumber.IIM7, ChordNumber.IIIM7, ChordNumber.IVMAJ7, ChordNumber.VIM7, ChordNumber.VIIM7B5],
            ChordNumber.IMAJ7: [ChordNumber.IV, ChordNumber.IVMAJ7, ChordNumber.V, ChordNumber.V7, ChordNumber.VI, ChordNumber.VIM7, ChordNumber.II, ChordNumber.IIM7],
            ChordNumber.II: [ChordNumber.V, ChordNumber.V7, ChordNumber.IV, ChordNumber.VII, ChordNumber.VIIM7B5],
            ChordNumber.IIM7: [ChordNumber.V, ChordNumber.V7, ChordNumber.IV, ChordNumber.IVMAJ7, ChordNumber.VII, ChordNumber.VIIM7B5],
            ChordNumber.III: [ChordNumber.VI, ChordNumber.IIIAUG, ChordNumber.III7, ChordNumber.IV, ChordNumber.I, ChordNumber.VIM7],
            ChordNumber.IIIM7: [ChordNumber.VI, ChordNumber.VIM7, ChordNumber.IV, ChordNumber.IVMAJ7, ChordNumber.I],
            ChordNumber.IIIAUG: [ChordNumber.VI, ChordNumber.III, ChordNumber.III7, ChordNumber.IV, ChordNumber.I],
            ChordNumber.III7: [ChordNumber.VI, ChordNumber.IV, ChordNumber.I],
            ChordNumber.IV: [ChordNumber.I, ChordNumber.V, ChordNumber.V7, ChordNumber.II, ChordNumber.IMAJ7, ChordNumber.VII],
            ChordNumber.IVMAJ7: [ChordNumber.I, ChordNumber.IMAJ7, ChordNumber.V, ChordNumber.V7, ChordNumber.II, ChordNumber.IIM7],
            ChordNumber.V: [ChordNumber.I, ChordNumber.VI, ChordNumber.IV, ChordNumber.VII, ChordNumber.IMAJ7, ChordNumber.VIM7],
            ChordNumber.V7: [ChordNumber.I, ChordNumber.IMAJ7, ChordNumber.VI, ChordNumber.VIM7, ChordNumber.IV, ChordNumber.VII],
            ChordNumber.VI: [ChordNumber.IV, ChordNumber.IVMAJ7, ChordNumber.I, ChordNumber.IMAJ7, ChordNumber.II, ChordNumber.IIM7, ChordNumber.III, ChordNumber.IIIM7, ChordNumber.IIIAUG, ChordNumber.III7, ChordNumber.VII, ChordNumber.V, ChordNumber.VIM7],
            ChordNumber.VIM7: [ChordNumber.IV, ChordNumber.IVMAJ7, ChordNumber.I, ChordNumber.IMAJ7, ChordNumber.II, ChordNumber.IIM7, ChordNumber.III, ChordNumber.IIIM7],
            ChordNumber.VII: [ChordNumber.I, ChordNumber.IMAJ7, ChordNumber.VI, ChordNumber.VIM7],
            ChordNumber.VIIM7B5: [ChordNumber.I, ChordNumber.IMAJ7, ChordNumber.VI, ChordNumber.VIM7],
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
            "augmented": [0, 4, 8],
            "dominant7": [0, 4, 7, 10],
            "maj7": [0, 4, 7, 11],
            "m7": [0, 3, 7, 10],
            "m7b5": [0, 3, 6, 10],
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
                                   use_inversions: bool = True,
                                   include_bass_line: bool = False) -> List[List[float]]:
        """Get frequencies for all chords in current progression with voice leading.
        
        Args:
            base_octave: Octave for tonic note
            use_inversions: If True, use inversions for smoother voice leading
            include_bass_line: If True, add the root note an octave lower as an additional bass note
        
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
            
            # Don't sort frequencies - maintain voice leading relationships
            # Each voice should move to the nearest note in the next chord
            
            # Add bass line if requested: add the root note an octave lower
            if include_bass_line:
                root_semitone = self.get_chord_notes(chord, 0)[0]
                # Calculate bass frequency (root lowered by one octave)
                bass_octave = base_octave - 1
                octave = bass_octave + (root_semitone // 12)
                note_in_octave = root_semitone % 12
                semitones_from_a4 = (octave - 4) * 12 + note_in_octave - 9
                bass_frequency = self.base_freq * (2 ** (semitones_from_a4 / 12))
                frequencies.insert(0, bass_frequency)  # Add bass as lowest note
            
            all_frequencies.append(frequencies)
            previous_notes = chord_notes  # Track for voice leading on next chord
        
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
        Uses optimal voice assignment: each voice moves to its nearest note in the next chord.
        
        Args:
            chord: Current chord
            previous_notes: Semitone values of previous chord notes
            base_octave: Base octave for reference
        
        Returns:
            Best inversion (0, 1, or 2)
        """
        base_notes = self.get_chord_notes(chord, 0)
        num_inversions = len(base_notes)
        
        best_inversion = 0
        best_total_distance = float('inf')
        
        # Try each inversion and calculate optimal voice leading distances
        for inversion in range(num_inversions):
            chord_notes = self.get_chord_notes(chord, inversion)
            
            # Calculate total voice leading distance using optimal assignment
            # Each voice finds its nearest note in the next chord
            total_distance = self._calculate_optimal_voice_distance(previous_notes, chord_notes)
            
            if total_distance < best_total_distance:
                best_total_distance = total_distance
                best_inversion = inversion
        
        return best_inversion
    
    def _calculate_optimal_voice_distance(self, previous_notes: List[int], next_notes: List[int]) -> float:
        """Calculate optimal voice leading distance by assigning each voice to its nearest target.
        
        For each current note, find the closest next note (considering octave equivalence).
        This ensures A4 moves to B4 (9+2=11 semitones, i.e. +2), not B5 or B3.
        
        Args:
            previous_notes: Semitone intervals of current chord
            next_notes: Semitone intervals of next chord
        
        Returns:
            Total voice leading distance
        """
        total_distance = 0
        assigned_indices = set()
        
        # For each voice in the previous chord, find the nearest available note in the next chord
        for prev_note in previous_notes:
            best_next_idx = -1
            best_distance = float('inf')
            
            # For each voice in the next chord
            for next_idx, next_note in enumerate(next_notes):
                if next_idx in assigned_indices:
                    continue  # This voice is already assigned
                
                # Calculate distance considering octave equivalence
                # Find distance to next_note's class in nearby octaves
                note_class = next_note % 12
                prev_class = prev_note % 12
                
                # Try different octaves for the next note
                for octave_offset in range(-2, 3):  # Check octaves -2 to +2
                    target_note = next_note + (octave_offset * 12)
                    distance = abs(target_note - prev_note)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_next_idx = next_idx
            
            if best_next_idx >= 0:
                assigned_indices.add(best_next_idx)
                total_distance += best_distance
        
        return total_distance
    
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
        name_map = {
            ChordNumber.IIIAUG: "III+",
            ChordNumber.IMAJ7: "Imaj7",
            ChordNumber.IIM7: "ii7",
            ChordNumber.IIIM7: "iii7",
            ChordNumber.IVMAJ7: "IVmaj7",
            ChordNumber.VIM7: "vi7",
            ChordNumber.VIIM7B5: "viiø7",
            # Also maintain case conversions for basic chords
            ChordNumber.II: "ii",
            ChordNumber.III: "iii",
            ChordNumber.VI: "vi",
            ChordNumber.VII: "vii°",
        }
        return " - ".join([name_map.get(chord, chord.name) for chord in progression])
