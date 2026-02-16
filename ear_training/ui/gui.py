"""GUI for ear training application using PyQt5."""

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QMessageBox, QComboBox, QSlider, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pygame

from ear_training.modules import IntervalTrainer, Interval, ChordTrainer, ChordType, NoteTrainer, Note, ProgressionTrainer, ChordNumber
from ear_training.ui.audio_player import AudioPlayer


class IntervalTrainingWindow(QMainWindow):
    """GUI window for interval training."""
    
    def __init__(self):
        super().__init__()
        self.trainer = IntervalTrainer()
        self.player = AudioPlayer(sample_rate=44100, duration=0.5)
        self.score = 0
        self.total = 0
        self.current_interval = None
        self.selected_instrument = "piano"  # Set BEFORE init_ui
        self.instrument_combo = None
        self.max_interval_combo = None
        self.max_interval_semitones = 12  # Default to Octave
        self.available_intervals = list(Interval)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Ear Training - Interval Recognition")
        self.setGeometry(100, 100, 1000, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Interval Recognition Training")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Score
        self.score_label = QLabel(f"Score: {self.score}/{self.total}")
        self.score_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.score_label)
        
        # Instrument selection
        instrument_layout = QHBoxLayout()
        instrument_label = QLabel("Instrument:")
        instrument_label.setFont(QFont("Arial", 12))
        self.instrument_combo = QComboBox()
        self.instrument_combo.setFont(QFont("Arial", 11))
        self.instrument_combo.addItems(["Piano", "Bell", "Violin", "Flute"])
        self.instrument_combo.activated.connect(self.on_instrument_changed)
        self.selected_instrument = "piano"  # Initialize default
        instrument_layout.addWidget(instrument_label)
        instrument_layout.addWidget(self.instrument_combo)
        instrument_layout.addSpacing(20)
        
        # Max interval selection
        max_interval_label = QLabel("Max Interval:")
        max_interval_label.setFont(QFont("Arial", 12))
        self.max_interval_combo = QComboBox()
        self.max_interval_combo.setFont(QFont("Arial", 11))
        self.max_interval_combo.addItems([
            "Minor 3rd",
            "Major 3rd",
            "Perfect 4th",
            "Perfect 5th",
            "Minor 6th",
            "Major 6th",
            "Octave",
            "All Intervals"
        ])
        self.max_interval_combo.setCurrentIndex(6)  # Default to Octave
        self.max_interval_combo.activated.connect(self.on_max_interval_changed)
        instrument_layout.addWidget(max_interval_label)
        instrument_layout.addWidget(self.max_interval_combo)
        instrument_layout.addStretch()
        layout.addLayout(instrument_layout)
        
        # Instructions
        instructions = QLabel("Listen to the interval, then click the correct answer")
        instructions.setFont(QFont("Arial", 12))
        layout.addWidget(instructions)
        
        # Play button
        self.play_button = QPushButton("▶ Play Interval")
        self.play_button.setFont(QFont("Arial", 12))
        self.play_button.clicked.connect(lambda: self.on_play_clicked())
        layout.addWidget(self.play_button)
        
        # Result label
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 12))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Interval buttons grid (will be populated dynamically)
        self.interval_grid = QGridLayout()
        self.interval_buttons = {}
        
        # Initialize available intervals based on default max interval setting
        all_intervals = list(Interval)
        self.available_intervals = [iv for iv in all_intervals if iv.value <= self.max_interval_semitones]
        
        self.rebuild_interval_buttons()
        layout.addLayout(self.interval_grid)
        
        # Exit button
        exit_button = QPushButton("Exit")
        exit_button.setFont(QFont("Arial", 12))
        exit_button.clicked.connect(self.exit_training)
        layout.addWidget(exit_button)
        
        # Generate first interval
        self.new_interval()
        
        # Manually trigger on_max_interval_changed to properly initialize
        # (activated signal won't fire during setCurrentIndex)
        self.on_max_interval_changed()
    
    def new_interval(self):
        """Generate a new interval."""
        self.current_interval = self.trainer.generate_interval(interval_range=(0, self.max_interval_semitones))
        self.result_label.setText("")
        self.disable_interval_buttons(False)
    
    def on_play_clicked(self):
        """Handle play button click."""
        self.play_interval()

    def play_interval(self):
        """Play the current interval."""
        if self.current_interval:
            freq1, freq2 = self.trainer.get_frequencies()
            # Play in ascending or descending order based on current direction
            if self.trainer.current_direction == "descending":
                freq1, freq2 = freq2, freq1  # Swap for descending
            
            self.player.play_tone(freq1, duration=0.5, instrument=self.selected_instrument)
            # Use QTimer instead of time.sleep to avoid blocking GUI
            QTimer.singleShot(600, lambda: self.player.play_tone(freq2, duration=0.5, instrument=self.selected_instrument))
    
    def guess_interval(self, interval: Interval):
        """Handle interval guess."""
        is_correct = self.trainer.submit_answer(interval)
        self.total += 1
        
        if is_correct:
            self.score += 1
            self.result_label.setText(f"✓ Correct! It was {self.current_interval.name}")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.result_label.setText(
                f"✗ Wrong. Correct answer: {self.current_interval.name}, "
                f"You said: {interval.name}"
            )
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.score_label.setText(f"Score: {self.score}/{self.total}")
        self.disable_interval_buttons(True)
        
        # Generate and schedule the next interval
        QTimer.singleShot(2000, self.new_interval)
    
    def disable_interval_buttons(self, disabled: bool):
        """Disable/enable interval buttons."""
        for btn in self.interval_buttons.values():
            btn.setEnabled(not disabled)
    
    def rebuild_interval_buttons(self):
        """Rebuild interval buttons based on available intervals."""
        # Clear existing buttons
        for btn in self.interval_buttons.values():
            btn.deleteLater()
        self.interval_buttons.clear()
        
        # Clear grid layout
        while self.interval_grid.count():
            item = self.interval_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create buttons for available intervals
        for i, interval in enumerate(self.available_intervals):
            row = i // 4
            col = i % 4
            btn = QPushButton(interval.name.replace("_", " ").title())
            btn.setFont(QFont("Arial", 10))
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda checked, iv=interval: self.guess_interval(iv))
            self.interval_grid.addWidget(btn, row, col)
            self.interval_buttons[interval] = btn
    
    def on_max_interval_changed(self):
        """Handle max interval selection change."""
        index = self.max_interval_combo.currentIndex()
        
        # Map selection to semitones
        max_semitones_map = {
            0: 3,   # Minor 3rd
            1: 4,   # Major 3rd
            2: 5,   # Perfect 4th
            3: 7,   # Perfect 5th
            4: 8,   # Minor 6th
            5: 9,   # Major 6th
            6: 12,  # Octave
            7: 36   # All Intervals (up to 3 octaves)
        }
        
        self.max_interval_semitones = max_semitones_map[index]
        
        # Update available intervals
        all_intervals = list(Interval)
        self.available_intervals = [iv for iv in all_intervals if iv.value <= self.max_interval_semitones]
        
        # Rebuild buttons
        self.rebuild_interval_buttons()
        
        # Generate new interval
        self.new_interval()
    
    def on_instrument_changed(self):
        """Handle instrument selection change."""
        text = self.instrument_combo.currentText()
        self.selected_instrument = text.lower()
    
    def exit_training(self):
        """Exit training and show final score."""
        if self.total > 0:
            percentage = (self.score / self.total) * 100
            QMessageBox.information(
                self, 
                "Training Complete",
                f"Final Score: {self.score}/{self.total} ({percentage:.1f}%)"
            )
        self.close()
    
    def closeEvent(self, event):
        """Handle window close event and clean up resources."""
        # Stop pygame mixer to prevent crashes
        pygame.mixer.quit()
        event.accept()


class ChordTrainingWindow(QMainWindow):
    """GUI window for chord training."""
    
    def __init__(self):
        super().__init__()
        self.trainer = ChordTrainer()
        self.player = AudioPlayer(sample_rate=44100, duration=0.8)
        self.score = 0
        self.total = 0
        self.current_chord = None
        self.selected_instrument = "piano"
        self.instrument_combo = None
        self.chord_buttons = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Ear Training - Chord Recognition")
        self.setGeometry(120, 120, 900, 520)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title = QLabel("Chord Recognition Training")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        self.score_label = QLabel(f"Score: {self.score}/{self.total}")
        self.score_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.score_label)
        
        instrument_layout = QHBoxLayout()
        instrument_label = QLabel("Instrument:")
        instrument_label.setFont(QFont("Arial", 12))
        self.instrument_combo = QComboBox()
        self.instrument_combo.setFont(QFont("Arial", 11))
        self.instrument_combo.addItems(["Piano", "Bell", "Violin", "Flute"])
        self.instrument_combo.activated.connect(self.on_instrument_changed)
        self.selected_instrument = "piano"
        instrument_layout.addWidget(instrument_label)
        instrument_layout.addWidget(self.instrument_combo)
        instrument_layout.addStretch()
        layout.addLayout(instrument_layout)
        
        instructions = QLabel("Listen to the chord, then click the correct chord type")
        instructions.setFont(QFont("Arial", 12))
        layout.addWidget(instructions)
        
        self.play_button = QPushButton("▶ Play Chord")
        self.play_button.setFont(QFont("Arial", 12))
        self.play_button.clicked.connect(self.on_play_clicked)
        layout.addWidget(self.play_button)
        
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 12))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        grid = QGridLayout()
        chord_types = list(ChordType)
        for i, chord in enumerate(chord_types):
            row = i // 3
            col = i % 3
            btn = QPushButton(chord.name.replace("_", " "))
            btn.setFont(QFont("Arial", 11))
            btn.setMinimumHeight(48)
            btn.clicked.connect(lambda checked, ct=chord: self.guess_chord(ct))
            grid.addWidget(btn, row, col)
            self.chord_buttons[chord] = btn
        layout.addLayout(grid)
        
        exit_button = QPushButton("Exit")
        exit_button.setFont(QFont("Arial", 12))
        exit_button.clicked.connect(self.exit_training)
        layout.addWidget(exit_button)
        
        self.new_chord()
    
    def new_chord(self):
        """Generate a new chord."""
        self.current_chord = self.trainer.generate_chord()
        self.result_label.setText("")
        self.disable_chord_buttons(False)
    
    def on_play_clicked(self):
        """Handle play button click."""
        self.play_chord()
    
    def play_chord(self):
        """Play the current chord."""
        if self.current_chord:
            freqs = self.trainer.get_frequencies()
            self.player.play_frequencies(freqs, duration=0.9, instrument=self.selected_instrument)
    
    def guess_chord(self, chord: ChordType):
        """Handle chord guess."""
        is_correct = self.trainer.submit_answer(chord)
        self.total += 1
        
        if is_correct:
            self.score += 1
            self.result_label.setText(f"✓ Correct! It was {self.current_chord.name}")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.result_label.setText(
                f"✗ Wrong. Correct answer: {self.current_chord.name}, You said: {chord.name}"
            )
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.score_label.setText(f"Score: {self.score}/{self.total}")
        self.disable_chord_buttons(True)
        self.current_chord = self.trainer.generate_chord()
        QTimer.singleShot(2000, self.advance_to_next)
    
    def disable_chord_buttons(self, disabled: bool):
        """Disable/enable chord buttons."""
        for btn in self.chord_buttons.values():
            btn.setEnabled(not disabled)
    
    def advance_to_next(self):
        """Prepare UI for next chord."""
        self.result_label.setText("")
        self.disable_chord_buttons(False)
    
    def on_instrument_changed(self):
        """Handle instrument selection change."""
        text = self.instrument_combo.currentText()
        self.selected_instrument = text.lower()
    
    def exit_training(self):
        """Exit training and show final score."""
        if self.total > 0:
            percentage = (self.score / self.total) * 100
            QMessageBox.information(
                self,
                "Training Complete",
                f"Final Score: {self.score}/{self.total} ({percentage:.1f}%)"
            )
        self.close()
    
    def closeEvent(self, event):
        """Handle window close event and clean up resources."""
        pygame.mixer.quit()
        event.accept()


class ProgressionTrainingWindow(QMainWindow):
    """GUI window for harmonic progression training."""
    
    def __init__(self):
        super().__init__()
        self.trainer = ProgressionTrainer()
        self.player = AudioPlayer(sample_rate=44100, duration=0.8)
        self.score = 0
        self.total = 0
        self.current_progression = None
        self.current_frequencies = None
        self.selected_instrument = "piano"
        self.instrument_combo = None
        self.num_chords_combo = None
        self.chord_buttons = {}
        self.user_progression = []
        self.guessing_index = 0
        self.start_on_tonic = True
        self.playback_speed = 1.0  # Speed multiplier for playback
        self.use_common_only = False  # Use only predefined common progressions
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Ear Training - Harmonic Progression")
        self.setGeometry(100, 100, 1000, 650)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title = QLabel("Harmonic Progression Training")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        self.score_label = QLabel(f"Score: {self.score}/{self.total}")
        self.score_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.score_label)
        
        instrument_layout = QHBoxLayout()
        instrument_label = QLabel("Instrument:")
        instrument_label.setFont(QFont("Arial", 12))
        self.instrument_combo = QComboBox()
        self.instrument_combo.setFont(QFont("Arial", 11))
        self.instrument_combo.addItems(["Piano", "Bell", "Violin", "Flute"])
        self.instrument_combo.activated.connect(self.on_instrument_changed)
        self.selected_instrument = "piano"
        instrument_layout.addWidget(instrument_label)
        instrument_layout.addWidget(self.instrument_combo)
        instrument_layout.addSpacing(20)
        
        num_chords_label = QLabel("Number of Chords:")
        num_chords_label.setFont(QFont("Arial", 12))
        self.num_chords_combo = QComboBox()
        self.num_chords_combo.setFont(QFont("Arial", 11))
        self.num_chords_combo.addItems(["2", "3", "4", "5", "Random"])
        self.num_chords_combo.setCurrentIndex(4)  # Default to Random
        self.num_chords_combo.activated.connect(self.on_num_chords_changed)
        instrument_layout.addWidget(num_chords_label)
        instrument_layout.addWidget(self.num_chords_combo)
        instrument_layout.addStretch()
        layout.addLayout(instrument_layout)
        
        # Options layout - Root note volume slider
        from PyQt5.QtWidgets import QSlider
        options_layout = QHBoxLayout()
        root_volume_label = QLabel("Root Note Volume:")
        root_volume_label.setFont(QFont("Arial", 11))
        options_layout.addWidget(root_volume_label)
        
        self.root_volume_slider = QSlider(Qt.Horizontal)
        self.root_volume_slider.setFont(QFont("Arial", 10))
        self.root_volume_slider.setMinimum(100)
        self.root_volume_slider.setMaximum(400)
        self.root_volume_slider.setValue(100)
        self.root_volume_slider.setTickPosition(QSlider.TicksBelow)
        self.root_volume_slider.setTickInterval(10)
        self.root_volume_slider.setMaximumWidth(200)
        options_layout.addWidget(self.root_volume_slider)
        
        self.root_volume_value_label = QLabel("100%")
        self.root_volume_value_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.root_volume_value_label.setMinimumWidth(40)
        self.root_volume_slider.valueChanged.connect(self.on_root_volume_changed)
        options_layout.addWidget(self.root_volume_value_label)
        
        options_layout.addSpacing(20)
        
        # Playback speed slider
        playback_speed_label = QLabel("Playback Speed:")
        playback_speed_label.setFont(QFont("Arial", 11))
        options_layout.addWidget(playback_speed_label)
        
        self.playback_speed_slider = QSlider(Qt.Horizontal)
        self.playback_speed_slider.setFont(QFont("Arial", 10))
        self.playback_speed_slider.setMinimum(50)
        self.playback_speed_slider.setMaximum(200)
        self.playback_speed_slider.setValue(100)
        self.playback_speed_slider.setTickPosition(QSlider.TicksBelow)
        self.playback_speed_slider.setTickInterval(10)
        self.playback_speed_slider.setMaximumWidth(150)
        options_layout.addWidget(self.playback_speed_slider)
        
        self.playback_speed_value_label = QLabel("1.0x")
        self.playback_speed_value_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.playback_speed_value_label.setMinimumWidth(40)
        self.playback_speed_slider.valueChanged.connect(self.on_playback_speed_changed)
        options_layout.addWidget(self.playback_speed_value_label)
        
        options_layout.addSpacing(20)
        
        # Start on tonic checkbox
        self.start_on_tonic_checkbox = QCheckBox("Start on Tonic")
        self.start_on_tonic_checkbox.setFont(QFont("Arial", 11))
        self.start_on_tonic_checkbox.setChecked(True)
        self.start_on_tonic_checkbox.stateChanged.connect(self.on_start_on_tonic_changed)
        options_layout.addWidget(self.start_on_tonic_checkbox)
        
        # Use common progressions only checkbox
        self.use_common_checkbox = QCheckBox("Common Progressions Only")
        self.use_common_checkbox.setFont(QFont("Arial", 11))
        self.use_common_checkbox.setChecked(False)
        self.use_common_checkbox.stateChanged.connect(self.on_use_common_changed)
        options_layout.addWidget(self.use_common_checkbox)
        
        # Play tonic button
        self.play_tonic_button = QPushButton("♪ Play Tonic")
        self.play_tonic_button.setFont(QFont("Arial", 11))
        self.play_tonic_button.setMaximumWidth(120)
        self.play_tonic_button.clicked.connect(self.on_play_tonic_clicked)
        options_layout.addWidget(self.play_tonic_button)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        instructions = QLabel(
            "Listen to the chord progression, then click the chord numbers in order."
        )
        instructions.setFont(QFont("Arial", 12))
        layout.addWidget(instructions)
        
        # Progression display
        self.progression_label = QLabel("Waiting for progression...")
        self.progression_label.setFont(QFont("Arial", 12))
        self.progression_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(self.progression_label)
        
        # Play buttons layout
        play_buttons_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶ Play Progression")
        self.play_button.setFont(QFont("Arial", 12))
        self.play_button.clicked.connect(self.on_play_clicked)
        play_buttons_layout.addWidget(self.play_button)
        
        self.play_arpeggio_button = QPushButton("▶ Play as Arpeggio")
        self.play_arpeggio_button.setFont(QFont("Arial", 12))
        self.play_arpeggio_button.clicked.connect(self.on_play_arpeggio_clicked)
        play_buttons_layout.addWidget(self.play_arpeggio_button)
        
        self.repeat_button = QPushButton("↻ Repeat")
        self.repeat_button.setFont(QFont("Arial", 12))
        self.repeat_button.clicked.connect(self.on_repeat_clicked)
        play_buttons_layout.addWidget(self.repeat_button)
        
        layout.addLayout(play_buttons_layout)
        
        # Current chord notes display
        self.notes_display_label = QLabel("")
        notes_font = QFont("Courier New", 12, QFont.Bold)
        self.notes_display_label.setFont(notes_font)
        self.notes_display_label.setAlignment(Qt.AlignCenter)
        self.notes_display_label.setStyleSheet("background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; color: #0066cc;")
        layout.addWidget(self.notes_display_label)
        
        # User's progression display and undo button
        answer_layout = QHBoxLayout()
        self.user_progression_label = QLabel("")
        self.user_progression_label.setFont(QFont("Arial", 11))
        answer_layout.addWidget(self.user_progression_label)
        
        self.undo_button = QPushButton("↶")
        self.undo_button.setFont(QFont("Arial", 10))
        self.undo_button.setMaximumWidth(80)
        self.undo_button.clicked.connect(self.on_undo_clicked)
        answer_layout.addWidget(self.undo_button)
        answer_layout.addStretch()
        layout.addLayout(answer_layout)
        
        # Result label
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 12))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Chord buttons grid (Roman numerals)
        grid = QGridLayout()

        # Explicit layout so we can control where extra sevenths appear.
        # Desktop logic mirrors mobile: all basic chords in the first row,
        # with extra chords (III7, V7) in the second row under their base chord.
        chord_positions = {
            ChordNumber.I: (0, 0),
            ChordNumber.II: (0, 1),
            ChordNumber.III: (0, 2),
            ChordNumber.IV: (0, 3),
            ChordNumber.V: (0, 4),
            ChordNumber.VI: (0, 5),
            ChordNumber.VII: (0, 6),
            ChordNumber.IIIAUG: (1, 2),  # III+
            ChordNumber.III7: (2, 2),    # under III+
            ChordNumber.V7: (1, 4),      # under V
        }

        for chord, (row, col) in chord_positions.items():
            chord_type = chord.value[1]
            
            # Label formatting for different chord qualities
            if chord is ChordNumber.IIIAUG:
                chord_label = "III+"
            else:
                # Use lowercase for minor and diminished chords
                if chord_type in ["minor", "diminished"]:
                    chord_label = chord.name.lower()
                else:
                    chord_label = chord.name
            
            btn_label = f"{chord_label}\n({chord_type})"
            btn = QPushButton(btn_label)
            btn.setFont(QFont("Arial", 11, QFont.Bold))
            btn.setMinimumHeight(70)
            btn.setMinimumWidth(90)
            btn.clicked.connect(lambda checked, ct=chord: self.guess_chord(ct))
            grid.addWidget(btn, row, col)
            self.chord_buttons[chord] = btn
        layout.addLayout(grid)
        
        exit_button = QPushButton("Exit")
        exit_button.setFont(QFont("Arial", 12))
        exit_button.clicked.connect(self.exit_training)
        layout.addWidget(exit_button)
        
        self.new_progression()
    
    def new_progression(self):
        """Generate a new progression."""
        # Determine number of chords (ignored if using common only)
        combo_text = self.num_chords_combo.currentText()
        if combo_text == "Random":
            num_chords = None
        else:
            num_chords = int(combo_text)
        
        self.current_progression = self.trainer.generate_progression(
            num_chords, 
            start_on_tonic=self.start_on_tonic,
            use_common_only=self.use_common_only
        )
        self.current_frequencies = self.trainer.get_progression_frequencies(use_inversions=True)
        self.user_progression = []
        self.guessing_index = 0
        
        self.update_ui()
        self.result_label.setText("")
        self.disable_chord_buttons(False)
    
    def update_ui(self):
        """Update UI to reflect current state."""
        if len(self.user_progression) > 0:
            progression_str = " - ".join([c.name for c in self.user_progression])
        else:
            progression_str = ""
        
        self.user_progression_label.setText(progression_str)
        
        # Show whether progression starts on tonic or random
        start_info = "starting with I (Tonic)" if self.start_on_tonic else "starting on any chord"
        self.progression_label.setText(
            f"Progression length: {len(self.current_progression)} chords ({start_info})"
        )
    
    def frequencies_to_notes(self, frequencies: list) -> str:
        """Convert frequencies to note names.
        
        Args:
            frequencies: List of frequencies in Hz
        
        Returns:
            Space-separated note names (e.g., "C E G")
        """
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        notes = []
        
        for freq in sorted(frequencies):
            # Calculate semitones from A4 (440 Hz)
            semitones_from_a4 = 12 * np.log2(freq / 440.0)
            
            # Round to nearest semitone
            semitone = round(semitones_from_a4)
            
            # Calculate octave and note
            octave = 4 + (semitone + 9) // 12
            note_index = (semitone + 9) % 12
            
            notes.append(f"{note_names[note_index]}{octave}")
        
        return " - ".join(notes)
    
    def show_progression_notes(self):
        """Display all chords with their notes stacked vertically to show voice leading."""
        if not self.current_progression or not self.current_frequencies:
            return
        
        lines = []
        # Get max number of notes in any chord
        max_notes = max(len(freqs) for freqs in self.current_frequencies)
        
        # For each note position (top to bottom)
        for note_idx in range(max_notes):
            line = []
            for chord_idx, (chord, frequencies) in enumerate(zip(self.current_progression, self.current_frequencies)):
                # Get notes for this chord sorted in descending order
                note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                chord_notes = []
                for freq in sorted(frequencies, reverse=True):
                    semitones_from_a4 = 12 * np.log2(freq / 440.0)
                    semitone = round(semitones_from_a4)
                    octave = 4 + (semitone + 9) // 12
                    note_index = (semitone + 9) % 12
                    chord_notes.append(f"{note_names[note_index]}{octave}")
                
                # Add note at this position or blank space
                if note_idx < len(chord_notes):
                    line.append(chord_notes[note_idx])
                else:
                    line.append("")
            
            lines.append(line)
        
        # Format as a grid
        display_text = ""
        for i, line in enumerate(lines):
            display_text += "  ".join(f"{note:>3}" for note in line).rstrip()
            if i < len(lines) - 1:
                display_text += "\n"
        
        # Add chord numbers as header
        chord_nums = "  ".join(f"{c.name:>3}" for c in self.current_progression)
        full_display = chord_nums + "\n" + "-" * (len(chord_nums)) + "\n" + display_text
        
        self.notes_display_label.setText(full_display)
    
    def on_play_clicked(self):
        """Handle play button click."""
        self.play_progression()
    
    def on_play_arpeggio_clicked(self):
        """Handle play arpeggio button click."""
        self.play_arpeggio()
    
    def on_repeat_clicked(self):
        """Handle repeat button click to replay the current progression without generating a new one."""
        self._play_current_progression()
    
    def _play_current_progression(self):
        """Play the current progression without generating a new one."""
        if self.current_frequencies:
            root_volume = self.root_volume_slider.value() / 100.0
            base_delay = 1200  # Base delay in ms (0.8s chord + 0.4s pause)
            for i, frequencies in enumerate(self.current_frequencies):
                chord = self.current_progression[i]
                chord_name = chord.name
                # Schedule each chord to play with delay, adjusted for playback speed
                delay = int(i * base_delay / self.playback_speed)
                QTimer.singleShot(delay, lambda freqs=frequencies, rv=root_volume, c=chord: 
                                self.play_chord_with_options(freqs, rv, c))
    
    def play_progression(self):
        """Play the current progression with spacing between chords."""
        # If a progression was already answered, generate a new one
        if len(self.user_progression) == len(self.current_progression) and self.total > 0:
            self.new_progression()
        
        if self.current_frequencies:
            root_volume = self.root_volume_slider.value() / 100.0
            for i, frequencies in enumerate(self.current_frequencies):
                chord = self.current_progression[i]
                chord_name = chord.name
                # Schedule each chord to play with delay
                delay = i * 1200  # 1.2 seconds between chords (0.8s chord + 0.4s pause)
                QTimer.singleShot(delay, lambda freqs=frequencies, rv=root_volume, c=chord: 
                                self.play_chord_with_options(freqs, rv, c))
    
    def show_chord_notes(self, frequencies: list, chord_name: str):
        """Display the notes for a chord.
        
        Args:
            frequencies: List of frequencies for the chord
            chord_name: Name of the chord (e.g., "I", "IV", "V")
        """
        notes_str = self.frequencies_to_notes(frequencies)
        self.notes_display_label.setText(f"Chord {chord_name}: {notes_str}")
    
    def play_arpeggio(self):
        """Play all notes from the progression as an ascending arpeggio."""
        if self.current_frequencies:
            # Collect all notes from all chords
            all_notes = []
            for chord_freqs in self.current_frequencies:
                all_notes.extend(chord_freqs)
            
            # Sort frequencies in ascending order
            all_notes.sort()
            
            # Play each note in sequence for the arpeggio effect
            note_duration = 0.3  # Duration per note in arpeggio
            for i, frequency in enumerate(all_notes):
                delay = i * 350  # 350ms between each note (0.3s note + 0.05s gap)
                QTimer.singleShot(delay, lambda freq=frequency: 
                                self.player.play_tone(freq, duration=note_duration,
                                                    instrument=self.selected_instrument))
    
    def play_chord_with_options(self, frequencies: list, root_volume_multiplier: float, chord: ChordNumber):
        """Play a chord with adjustable root note volume.
        
        Args:
            frequencies: List of frequencies for the chord (already inverted)
            root_volume_multiplier: Multiplier for root note volume (1.0 = normal, 2.0 = double)
            chord: The ChordNumber object to identify the actual root note
        """
        if root_volume_multiplier <= 1.0:
            # Normal playback (100% or less)
            self.player.play_frequencies(frequencies, duration=0.8, 
                                        instrument=self.selected_instrument)
        else:
            # Calculate the target root frequency based on chord semitone offset
            # The root note's semitone offset is stored in the chord value
            chord_semitone_offset = chord.value[0]
            
            # Convert semitone offset to Hz from the tonic (C4 = 262 Hz)
            # A semitone is a factor of 2^(1/12)
            semitone_factor = 2 ** (1/12)
            root_hz_at_octave = 262 * (semitone_factor ** chord_semitone_offset)
            
            # Find which frequency in the list is the root note (considering octaves)
            # The root note frequency might be in a different octave than root_hz_at_octave
            # So we need to find the frequency closest to root_hz_at_octave (within one octave range)
            root_freq = None
            min_distance = float('inf')
            
            for freq in frequencies:
                # Check if this frequency is close to our target root in any octave
                # by checking the log ratio
                if freq > 0:
                    # Calculate which semitone this frequency is from C4
                    semitones_from_c4 = np.log2(freq / 262) * 12
                    # Get the semitone modulo 12 to find the note class
                    note_class = semitones_from_c4 % 12
                    target_note_class = chord_semitone_offset % 12
                    
                    # Find the circular distance (accounting for octave wrapping)
                    distance = min(abs(note_class - target_note_class), 
                                  12 - abs(note_class - target_note_class))
                    
                    if distance < min_distance:
                        min_distance = distance
                        root_freq = freq
            
            if root_freq is None:
                # Fallback: use lowest frequency if matching fails
                root_freq = min(frequencies)
            
            # Play all frequencies together first (normal)
            waveform = None
            for freq in frequencies:
                tone = self.player.generate_rich_tone(freq, 0.8, self.selected_instrument)
                if waveform is None:
                    waveform = tone
                else:
                    waveform += tone
            
            # Now add the root note with adjustable volume
            root_tone = self.player.generate_rich_tone(root_freq, 0.8, self.selected_instrument)
            
            # Add the root tone with the specified multiplier (minus 1.0 to get the extra amount)
            extra_root_volume = root_volume_multiplier - 1.0
            waveform += root_tone * extra_root_volume
            
            # Normalize to prevent clipping
            max_val = max(abs(waveform.min()), abs(waveform.max()))
            if max_val > 0:
                waveform = waveform / max_val * 0.95
            
            # Play the modified waveform
            self.player._play_audio(waveform)
    
    def guess_chord(self, chord: ChordNumber):
        """Handle chord guess."""
        # If starting on tonic, first chord must be I
        if self.start_on_tonic and self.guessing_index == 0 and len(self.user_progression) == 0:
            # First guess should be accounted differently
            self.user_progression.append(chord)
            self.guessing_index += 1
            self.update_ui()
            
            # Check if user correctly identified the first chord should be I
            if chord != ChordNumber.I:
                self.result_label.setText("✗ First chord should be I (Tonic)! Try again.")
                self.result_label.setStyleSheet("color: red; font-weight: bold;")
                self.user_progression = []
                self.guessing_index = 0
                self.update_ui()
            return
        
        # Add chord to user's progression
        self.user_progression.append(chord)
        self.guessing_index += 1
        self.update_ui()
        
        # Check if progression is complete
        if len(self.user_progression) == len(self.current_progression):
            self.check_answer()
    
    def on_undo_clicked(self):
        """Handle undo button click to remove last chord from answer."""
        if len(self.user_progression) > 0:
            self.user_progression.pop()
            self.guessing_index -= 1
            self.update_ui()
            self.result_label.setText("")
    
    def format_progression_string(self, progression: list) -> str:
        """Format progression string with proper case (lowercase for minor/diminished).
        
        Args:
            progression: List of ChordNumber enums
        
        Returns:
            Formatted progression string like "I - iv - V - I"
        """
        formatted_chords = []
        for chord in progression:
            chord_type = chord.value[1]
            if chord_type in ["minor", "diminished"]:
                formatted_chords.append(chord.name.lower())
            else:
                formatted_chords.append(chord.name)
        return " - ".join(formatted_chords)
    
    def check_answer(self):
        """Check if user's progression matches the current one."""
        is_correct = self.trainer.submit_answer(self.user_progression)
        self.total += 1
        
        if is_correct:
            self.score += 1
            correct_progression = self.format_progression_string(self.current_progression)
            self.result_label.setText(f"✓ Correct! Progression: {correct_progression}")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            correct_progression = self.format_progression_string(self.current_progression)
            user_progression = self.format_progression_string(self.user_progression)
            self.result_label.setText(
                f"✗ Wrong. Correct: {correct_progression}, You said: {user_progression}"
            )
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.score_label.setText(f"Score: {self.score}/{self.total}")
        self.disable_chord_buttons(True)
        
        # Show the chord notes stacked to visualize voice leading
        self.show_progression_notes()
    
    def on_root_volume_changed(self):
        """Handle root volume slider change."""
        value = self.root_volume_slider.value()
        self.root_volume_value_label.setText(f"{value}%")
    
    def on_playback_speed_changed(self):
        """Handle playback speed slider change."""
        value = self.playback_speed_slider.value()
        self.playback_speed = value / 100.0
        self.playback_speed_value_label.setText(f"{self.playback_speed:.1f}x")
    
    def on_start_on_tonic_changed(self):
        """Handle start on tonic checkbox change."""
        self.start_on_tonic = self.start_on_tonic_checkbox.isChecked()
        self.new_progression()
    
    def on_use_common_changed(self):
        """Handle use common progressions only checkbox change."""
        self.use_common_only = self.use_common_checkbox.isChecked()
        self.new_progression()
    
    def on_play_tonic_clicked(self):
        """Handle play tonic button click."""
        # Play C4 (tonic) for 1 second
        tonic_freq = 262.0  # C4
        self.player.play_tone(tonic_freq, duration=1.0, instrument=self.selected_instrument)
    
    def disable_chord_buttons(self, disabled: bool):
        """Disable/enable chord buttons."""
        for btn in self.chord_buttons.values():
            btn.setEnabled(not disabled)
    
    def on_instrument_changed(self):
        """Handle instrument selection change."""
        text = self.instrument_combo.currentText()
        self.selected_instrument = text.lower()
    
    def on_num_chords_changed(self):
        """Handle number of chords selection change."""
        self.new_progression()
    
    def exit_training(self):
        """Exit training and show final score."""
        if self.total > 0:
            percentage = (self.score / self.total) * 100
            QMessageBox.information(
                self,
                "Training Complete",
                f"Final Score: {self.score}/{self.total} ({percentage:.1f}%)"
            )
        self.close()
    
    def closeEvent(self, event):
        """Handle window close event and clean up resources."""
        pygame.mixer.quit()
        event.accept()


class NoteTrainingWindow(QMainWindow):
    """GUI window for note recognition training."""
    
    def __init__(self):
        super().__init__()
        self.num_octaves = 3  # Default to 3 octaves
        self.max_interval_semitones = 36  # Default to 3 octaves
        self.trainer = NoteTrainer(octave_range=(3, 5))  # Three octaves: C3-B5
        self.player = AudioPlayer(sample_rate=44100, duration=0.8)
        self.score = 0
        self.total = 0
        self.current_note = None
        self.current_octave = None
        self.selected_instrument = "piano"
        self.instrument_combo = None
        self.octave_combo = None
        self.max_interval_combo = None
        self.note_buttons = {}
        self.keyboard_container = None
        self.available_notes = list(Note)  # All notes available by default
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Ear Training - Note Recognition")
        self.setGeometry(120, 120, 1050, 520)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title = QLabel("Note Recognition Training")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        self.score_label = QLabel(f"Score: {self.score}/{self.total}")
        self.score_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.score_label)
        
        instrument_layout = QHBoxLayout()
        instrument_label = QLabel("Instrument:")
        instrument_label.setFont(QFont("Arial", 12))
        self.instrument_combo = QComboBox()
        self.instrument_combo.setFont(QFont("Arial", 11))
        self.instrument_combo.addItems(["Piano", "Bell", "Violin", "Flute"])
        self.instrument_combo.activated.connect(self.on_instrument_changed)
        self.selected_instrument = "piano"
        instrument_layout.addWidget(instrument_label)
        instrument_layout.addWidget(self.instrument_combo)
        instrument_layout.addSpacing(20)
        
        # Add octave range selector
        octave_label = QLabel("Octave Range:")
        octave_label.setFont(QFont("Arial", 12))
        self.octave_combo = QComboBox()
        self.octave_combo.setFont(QFont("Arial", 11))
        self.octave_combo.addItems(["1 Octave", "2 Octaves", "3 Octaves"])
        self.octave_combo.setCurrentIndex(2)  # Default to 3 octaves
        self.octave_combo.activated.connect(self.on_octave_range_changed)
        instrument_layout.addWidget(octave_label)
        instrument_layout.addWidget(self.octave_combo)
        instrument_layout.addSpacing(20)
        
        # Add max interval selector
        max_interval_label = QLabel("Max Interval:")
        max_interval_label.setFont(QFont("Arial", 12))
        self.max_interval_combo = QComboBox()
        self.max_interval_combo.setFont(QFont("Arial", 11))
        # Add options from 1 octave (12 semitones) to 2 octaves (24 semitones)
        interval_options = [
            "Octave (12)",
            "Minor 9th (13)",
            "Major 9th (14)",
            "Minor 10th (15)",
            "Major 10th (16)",
            "Perfect 11th (17)",
            "Augmented 11th (18)",
            "Perfect 12th (19)",
            "Minor 13th (20)",
            "Major 13th (21)",
            "Minor 14th (22)",
            "Major 14th (23)",
            "2 Octaves (24)"
        ]
        self.max_interval_combo.addItems(interval_options)
        self.max_interval_combo.setCurrentIndex(0)  # Default to Octave
        self.max_interval_combo.activated.connect(self.on_max_interval_changed)
        instrument_layout.addWidget(max_interval_label)
        instrument_layout.addWidget(self.max_interval_combo)
        instrument_layout.addStretch()
        layout.addLayout(instrument_layout)
        
        instructions = QLabel("Listen to the note, then click the correct note")
        instructions.setFont(QFont("Arial", 12))
        layout.addWidget(instructions)
        
        # Add reference note button
        ref_button = QPushButton("▶ Play Reference Note (A)")
        ref_button.setFont(QFont("Arial", 11))
        ref_button.clicked.connect(self.play_reference)
        layout.addWidget(ref_button)
        
        self.play_button = QPushButton("▶ Play Note")
        self.play_button.setFont(QFont("Arial", 12))
        self.play_button.clicked.connect(self.on_play_clicked)
        layout.addWidget(self.play_button)
        
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 12))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Create piano keyboard using rebuild method
        self.rebuild_keyboard()
        
        exit_button = QPushButton("Exit")
        exit_button.setFont(QFont("Arial", 12))
        exit_button.clicked.connect(self.exit_training)
        layout.addWidget(exit_button)
        
        self.new_note()
        
        # Manually trigger on_max_interval_changed to properly initialize
        # (activated signal won't fire during setCurrentIndex)
        self.on_max_interval_changed()
    
    def new_note(self):
        """Generate a new note."""
        self.current_note, self.current_octave = self.trainer.generate_note(self.available_notes, max_interval=self.max_interval_semitones)
        self.result_label.setText("")
        self.disable_note_buttons(False)
    
    def play_reference(self):
        """Play the reference note (A)."""
        ref_note, ref_freq = self.trainer.get_reference_note()
        self.player.play_tone(ref_freq, duration=0.8, instrument=self.selected_instrument)
    
    def on_play_clicked(self):
        """Handle play button click."""
        self.play_note()
    
    def play_note(self):
        """Play the current note."""
        if self.current_note:
            freq = self.trainer.get_current_frequency()
            self.player.play_tone(freq, duration=0.8, instrument=self.selected_instrument)
    
    def guess_note(self, note: Note, octave: int):
        """Handle note guess."""
        is_correct = self.trainer.submit_answer(note, octave)
        self.total += 1
        
        if is_correct:
            self.score += 1
            self.result_label.setText(f"✓ Correct! It was {self.current_note.display_name}{self.current_octave}")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.result_label.setText(
                f"✗ Wrong. Correct answer: {self.current_note.display_name}{self.current_octave}, You said: {note.display_name}{octave}"
            )
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.score_label.setText(f"Score: {self.score}/{self.total}")
        self.disable_note_buttons(True)
        self.current_note, self.current_octave = self.trainer.generate_note(self.available_notes, max_interval=self.max_interval_semitones)
        QTimer.singleShot(2000, self.advance_to_next)
    
    def disable_note_buttons(self, disabled: bool):
        """Disable/enable note buttons."""
        for btn in self.note_buttons.values():
            btn.setEnabled(not disabled)
    
    def advance_to_next(self):
        """Prepare UI for next note."""
        self.result_label.setText("")
        self.disable_note_buttons(False)
        self.play_note()
    
    def on_instrument_changed(self):
        """Handle instrument selection change."""
        text = self.instrument_combo.currentText()
        self.selected_instrument = text.lower()
    
    def on_octave_range_changed(self):
        """Handle octave range selection change."""
        index = self.octave_combo.currentIndex()
        self.num_octaves = index + 1  # 0 -> 1 octave, 1 -> 2 octaves, 2 -> 3 octaves
        
        # Apply max interval constraint
        self._apply_max_interval_constraint()
        
        # Determine window width based on num_octaves
        if self.num_octaves == 1:
            new_width = 550
        elif self.num_octaves == 2:
            new_width = 1050
        else:  # 3 octaves
            new_width = 1550
        
        # Resize window
        self.setGeometry(120, 120, new_width, 520)
        
        # Rebuild keyboard
        self.rebuild_keyboard()
        
        # Generate new note with updated range
        self.new_note()
    
    def on_max_interval_changed(self):
        """Handle max interval selection change."""
        index = self.max_interval_combo.currentIndex()
        
        # Map index directly to semitones (12 through 36)
        self.max_interval_semitones = 12 + index
        
        # Update available notes
        all_notes = list(Note)
        self.available_notes = all_notes
        
        # Rebuild keyboard
        self.rebuild_keyboard()
        
        # Regenerate note with updated constraints
        self.new_note()
    
    def _apply_max_interval_constraint(self):
        """Apply max interval constraint to the octave range."""
        # Calculate how many octaves the max interval allows
        max_octaves = self.max_interval_semitones / 12
        
        # Apply constraint based on current num_octaves selection
        if self.num_octaves <= max_octaves:
            # Current octave range is within max interval, keep it
            if self.num_octaves == 1:
                self.trainer.octave_range = (4, 4)
            elif self.num_octaves == 2:
                self.trainer.octave_range = (4, 5)
            else:  # 3 octaves
                self.trainer.octave_range = (3, 5)
        else:
            # Current octave range exceeds max interval, constrain it
            max_octaves_int = int(max_octaves)
            if max_octaves_int == 1:
                self.trainer.octave_range = (4, 4)
            elif max_octaves_int == 2:
                self.trainer.octave_range = (4, 5)
            else:
                self.trainer.octave_range = (3, 5)
    
    def rebuild_keyboard(self):
        """Rebuild the keyboard with current octave settings."""
        # Clear existing keyboard
        if self.keyboard_container:
            # Remove all child widgets from keyboard container
            for btn in self.note_buttons.values():
                btn.deleteLater()
            self.note_buttons.clear()
            self.keyboard_container.deleteLater()
        
        # Recreate keyboard container
        self.keyboard_container = QWidget()
        self.keyboard_container.setMinimumHeight(180)
        self.keyboard_container.setMaximumHeight(180)
        if self.num_octaves == 1:
            self.keyboard_container.setMinimumWidth(500)
        elif self.num_octaves == 2:
            self.keyboard_container.setMinimumWidth(1000)
        else:  # 3 octaves
            self.keyboard_container.setMinimumWidth(1500)
        
        # Determine starting octave based on trainer's octave range
        start_octave = self.trainer.octave_range[0]
        
        # White keys
        white_notes = [Note.C, Note.D, Note.E, Note.F, Note.G, Note.A, Note.B]
        # Filter by available notes
        white_notes = [n for n in white_notes if n in self.available_notes]
        white_key_width = 70
        white_key_height = 150
        
        # Create octaves of white keys
        for octave in range(self.num_octaves):
            for i, note in enumerate(white_notes):
                key_position = (octave * 7 + i) * white_key_width
                label = f"{note.display_name}{start_octave + octave}"
                btn = QPushButton(label, self.keyboard_container)
                btn.setGeometry(key_position, 30, white_key_width - 2, white_key_height)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 2px solid #333;
                        border-radius: 0px 0px 5px 5px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)
                btn.clicked.connect(lambda checked, n=note, o=start_octave + octave: self.guess_note(n, o))
                self.note_buttons[note] = btn
        
        # Black keys
        black_notes_info = [
            (Note.C_SHARP, 0.7),
            (Note.D_SHARP, 1.7),
            (Note.F_SHARP, 3.7),
            (Note.G_SHARP, 4.7),
            (Note.A_SHARP, 5.7),
        ]
        # Filter by available notes
        black_notes_info = [(n, p) for n, p in black_notes_info if n in self.available_notes]
        
        black_key_width = 45
        black_key_height = 100
        
        # Create octaves of black keys
        for octave in range(self.num_octaves):
            for note, relative_position in black_notes_info:
                position = (octave * 7 + relative_position) * white_key_width
                label = f"{note.display_name}{start_octave + octave}"
                btn = QPushButton(label, self.keyboard_container)
                btn.setGeometry(int(position) - black_key_width // 2, 30, black_key_width, black_key_height)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1a1a;
                        color: white;
                        border: 2px solid #000;
                        border-radius: 0px 0px 3px 3px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #333333;
                    }
                    QPushButton:disabled {
                        background-color: #555555;
                    }
                """)
                btn.clicked.connect(lambda checked, n=note, o=start_octave + octave: self.guess_note(n, o))
                self.note_buttons[note] = btn
                btn.raise_()
        
        # Add keyboard container to the layout (find and replace in parent)
        # We need to insert it at the right position in the parent layout
        parent_layout = self.centralWidget().layout()
        # Insert before the exit button (which should be the last widget)
        parent_layout.insertWidget(parent_layout.count() - 1, self.keyboard_container)
    
    def exit_training(self):
        """Exit training and show final score."""
        if self.total > 0:
            percentage = (self.score / self.total) * 100
            QMessageBox.information(
                self,
                "Training Complete",
                f"Final Score: {self.score}/{self.total} ({percentage:.1f}%)"
            )
        self.close()
    
    def closeEvent(self, event):
        """Handle window close event and clean up resources."""
        pygame.mixer.quit()
        event.accept()


class MainMenu(QMainWindow):
    """Main menu window."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Ear Training")
        self.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Ear Training")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Spacing
        layout.addSpacing(30)
        
        # Interval button
        interval_btn = QPushButton("🎵 Interval Recognition")
        interval_btn.setFont(QFont("Arial", 14))
        interval_btn.setMinimumHeight(60)
        interval_btn.clicked.connect(self.start_interval_training)
        layout.addWidget(interval_btn)
        
        # Note button
        note_btn = QPushButton("🎹 Note Recognition")
        note_btn.setFont(QFont("Arial", 14))
        note_btn.setMinimumHeight(60)
        note_btn.clicked.connect(self.start_note_training)
        layout.addWidget(note_btn)
        
        # Chord button
        chord_btn = QPushButton("🎼 Chord Recognition")
        chord_btn.setFont(QFont("Arial", 14))
        chord_btn.setMinimumHeight(60)
        chord_btn.clicked.connect(self.start_chord_training)
        layout.addWidget(chord_btn)
        
        # Progression button
        progression_btn = QPushButton("🎵 Harmonic Progression")
        progression_btn.setFont(QFont("Arial", 14))
        progression_btn.setMinimumHeight(60)
        progression_btn.clicked.connect(self.start_progression_training)
        layout.addWidget(progression_btn)
        
        # Rhythm button
        rhythm_btn = QPushButton("🥁 Rhythm Recognition")
        rhythm_btn.setFont(QFont("Arial", 14))
        rhythm_btn.setMinimumHeight(60)
        rhythm_btn.setEnabled(False)  # Coming soon
        layout.addWidget(rhythm_btn)
        
        # Spacing
        layout.addSpacing(20)
        
        # Exit button
        exit_btn = QPushButton("Exit")
        exit_btn.setFont(QFont("Arial", 12))
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
    
    def start_interval_training(self):
        """Start interval training."""
        self.training_window = IntervalTrainingWindow()
        self.training_window.show()
        self.close()
    
    def start_note_training(self):
        """Start note recognition training."""
        self.training_window = NoteTrainingWindow()
        self.training_window.show()
        self.close()

    def start_chord_training(self):
        """Start chord training."""
        self.training_window = ChordTrainingWindow()
        self.training_window.show()
        self.close()
    
    def start_progression_training(self):
        """Start harmonic progression training."""
        self.training_window = ProgressionTrainingWindow()
        self.training_window.show()
        self.close()


def main_gui():
    """Run the GUI application."""
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main_gui()
