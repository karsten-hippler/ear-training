# Harmonic Progression Training Feature

## Overview
A new exercise module has been added to train users on harmonic chord progressions of triads with proper voice leading.

## Features

### 1. **Progression Generation** (`ear_training/modules/progressions.py`)
- **Starting Chord**: Every progression starts with the tonic (I chord)
- **Variable Length**: Users can choose 3, 4, 5, or random (3-5) chords per progression
- **Voice Leading**: Implements proper voice leading principles:
  - Smooth transitions between chords
  - Preferred chord progressions based on harmonic principles
  - Chord inversions to minimize voice leading distance

### 2. **Chord Types Included**
- **I** (Tonic) - Major
- **II** (Supertonic) - Minor
- **III** (Mediant) - Minor
- **IV** (Subdominant) - Major
- **V** (Dominant) - Major
- **VI** (Submediant) - Minor
- **VII** (Leading Tone) - Diminished

### 3. **User Interface** (`ear_training/ui/gui.py`)

#### ProgressionTrainingWindow
- **Play Progressions**: Click "Play Progression" to hear each chord (1.2 seconds apart)
- **Guess Mode**: Click chord number buttons (Roman numerals) in sequence
  - First chord is always I (automatically established)
  - User clicks subsequent chords in the progression
- **Instrument Selection**: Piano, Bell, Violin, or Flute
- **Progression Length**: Choose between 3, 4, 5, or random chords
- **Real-time Feedback**:
  - Shows user's progression as they click
  - Displays correct answer if wrong
  - Tracks score and accuracy

#### Main Menu Integration
- New button "🎵 Harmonic Progression" added to main menu
- Seamlessly integrated with other training exercises

### 4. **Scoring System**
- Tracks correct vs. incorrect progressions
- Displays final score and percentage upon exit

## Technical Details

### Voice Leading Algorithm
The progression trainer implements voice leading based on:
- Harmonic progression preferences (e.g., I preferably goes to IV, V, or VI)
- Chord inversions to minimize pitch distance between chords
- Natural, musically sensible progressions

### Audio Playback
- Each chord in the progression is played sequentially
- 0.8 seconds per chord with 0.4 second pause between chords
- Multiple instruments available: Piano, Bell, Violin, Flute
- Rich harmonic synthesis for natural sound

## How to Use

1. Launch the application
2. Click "🎵 Harmonic Progression" from the main menu
3. Select your preferences:
   - Choose instrument (Piano, Bell, Violin, or Flute)
   - Choose progression length (3, 4, 5, or Random)
4. Click "Play Progression" to hear the chord sequence
5. Click the Roman numeral buttons to guess the progression:
   - First chord (I) is assumed
   - Click the remaining chords in order
6. Get immediate feedback on correctness
7. Progressions are timed - new progression starts 2.5 seconds after answer
8. View final score when exiting

## Implementation Notes

### Dependencies
- No new external dependencies added (uses existing requirements)
- Removed numpy dependency from progressions module for lightweight code

### File Structure
```
ear_training/
├── modules/
│   ├── progressions.py      [NEW] Progression generation and training logic
│   └── __init__.py          [UPDATED] Export ProgressionTrainer and ChordNumber
└── ui/
    └── gui.py               [UPDATED] Added ProgressionTrainingWindow
```

## Testing
The progressions module has been tested to verify:
- Progression generation with various lengths
- Frequency calculation with voice leading
- Chord inversion selection
- Answer validation
- Proper Roman numeral formatting

All tests passed successfully!
