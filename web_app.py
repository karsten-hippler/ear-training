"""Flask web app for ear training."""

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import io
import json
import os
import numpy as np
import scipy.io.wavfile as wavfile
from ear_training.modules.progressions import ProgressionTrainer, ChordNumber
from ear_training.ui.audio_player import AudioPlayer

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
CUSTOM_PROGRESSIONS_FILE = os.path.join(BASE_DIR, 'custom_progressions.json')
DEACTIVATED_CHORDS_FILE = os.path.join(BASE_DIR, 'deactivated_chords.json')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')
CORS(app)

# Initialize trainers and players
progression_trainer = ProgressionTrainer()
audio_players = {
    "piano": AudioPlayer(sample_rate=44100, duration=0.8),
    "bell": AudioPlayer(sample_rate=44100, duration=0.8),
    "violin": AudioPlayer(sample_rate=44100, duration=0.8),
    "flute": AudioPlayer(sample_rate=44100, duration=0.8),
}

def load_custom_progressions():
    """Load custom progressions from file."""
    if os.path.exists(CUSTOM_PROGRESSIONS_FILE):
        try:
            with open(CUSTOM_PROGRESSIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_custom_progressions(progressions):
    """Save custom progressions to file."""
    try:
        with open(CUSTOM_PROGRESSIONS_FILE, 'w') as f:
            json.dump(progressions, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving custom progressions: {e}")
        return False

def load_deactivated_chords():
    """Load deactivated chords from file."""
    if os.path.exists(DEACTIVATED_CHORDS_FILE):
        try:
            with open(DEACTIVATED_CHORDS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_deactivated_chords(chords):
    """Save deactivated chords to file."""
    try:
        with open(DEACTIVATED_CHORDS_FILE, 'w') as f:
            json.dump(chords, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving deactivated chords: {e}")
        return False

@app.route('/api/progression', methods=['POST'])
def get_progression():
    """Generate a new chord progression."""
    data = request.json
    
    num_chords = data.get('num_chords')
    if num_chords and num_chords != 'Random':
        num_chords = int(num_chords)
    else:
        num_chords = None
    
    start_on_tonic = data.get('start_on_tonic', True)
    use_common_only = data.get('use_common_only', False)
    
    # Load deactivated chords
    deactivated_chord_names = set(load_deactivated_chords())
    
    # Keep generating progressions until we get one without deactivated chords
    max_attempts = 20
    attempt = 0
    valid_progression = False
    progression = None
    
    while not valid_progression and attempt < max_attempts:
        progression = progression_trainer.generate_progression(
            num_chords=num_chords,
            start_on_tonic=start_on_tonic,
            use_common_only=use_common_only
        )
        
        # Check if progression contains any deactivated chords
        name_map = {
            ChordNumber.IIIAUG: "III+",
        }
        
        has_deactivated = False
        for chord in progression:
            chord_display = name_map.get(chord, chord.name)
            if chord_display in deactivated_chord_names:
                has_deactivated = True
                break
        
        if not has_deactivated:
            valid_progression = True
        
        attempt += 1
    
    if progression is None:
        return jsonify({'error': 'Could not generate a valid progression'}), 500
    
    # Get frequencies for the progression
    frequencies = progression_trainer.get_progression_frequencies(use_inversions=True)
    
    # Return progression as strings, mapping special chords for display
    progression_strs = [name_map.get(chord, chord.name) for chord in progression]
    
    return jsonify({
        'progression': progression_strs,
        'length': len(progression),
        'frequencies': frequencies
    })

@app.route('/api/reference', methods=['GET'])
def get_reference():
    """Get common progressions and chord reference information."""
    # Map chord names for display
    name_map = {
        ChordNumber.IIIAUG: "III+",
    }
    
    # Get all common progressions from the trainer
    common_progs = progression_trainer.common_progressions
    
    # Convert to displayable format
    progressions_display = []
    for prog in common_progs:
        prog_strs = [name_map.get(chord, chord.name) for chord in prog]
        progressions_display.append(' - '.join(prog_strs))
    
    # All available chords
    all_chords = [name_map.get(chord, chord.name) for chord in ChordNumber]
    
    # Extract unique movements from common progressions
    movements = set()
    for prog in common_progs:
        for i in range(len(prog) - 1):
            current = name_map.get(prog[i], prog[i].name)
            next_chord = name_map.get(prog[i+1], prog[i+1].name)
            movements.add(f"{current} → {next_chord}")
    
    movements_sorted = sorted(list(movements))
    
    # Get deactivated chords
    deactivated = load_deactivated_chords()
    
    return jsonify({
        'common_progressions': progressions_display,
        'all_chords': all_chords,
        'chord_movements': movements_sorted,
        'deactivated_chords': deactivated
    })

@app.route('/api/custom-progressions', methods=['GET'])
def get_custom_progressions():
    """Get all saved custom progressions."""
    try:
        custom_progs = load_custom_progressions()
        return jsonify({
            'custom_progressions': custom_progs
        })
    except Exception as e:
        print(f"Error loading custom progressions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/custom-progressions', methods=['POST'])
def save_custom_progression():
    """Save a new custom progression."""
    try:
        data = request.json
        progression = data.get('progression', [])
        
        if not progression:
            return jsonify({'error': 'Empty progression'}), 400
        
        # Load existing progressions
        custom_progs = load_custom_progressions()
        
        # Add new progression with metadata
        new_prog = {
            'progression': progression,
            'display': ' - '.join(progression),
            'id': len(custom_progs) + 1
        }
        
        custom_progs.append(new_prog)
        
        # Save to file
        if save_custom_progressions(custom_progs):
            return jsonify({
                'success': True,
                'message': 'Progression saved',
                'id': new_prog['id']
            })
        else:
            return jsonify({'error': 'Failed to save progression'}), 500
    
    except Exception as e:
        print(f"Error saving progression: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/custom-progressions/<int:prog_id>', methods=['DELETE'])
def delete_custom_progression(prog_id):
    """Delete a custom progression."""
    try:
        custom_progs = load_custom_progressions()
        custom_progs = [p for p in custom_progs if p.get('id') != prog_id]
        
        if save_custom_progressions(custom_progs):
            return jsonify({'success': True, 'message': 'Progression deleted'})
        else:
            return jsonify({'error': 'Failed to delete progression'}), 500
    
    except Exception as e:
        print(f"Error deleting progression: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deactivated-chords', methods=['GET'])
def get_deactivated_chords():
    """Get list of deactivated chords."""
    try:
        deactivated = load_deactivated_chords()
        return jsonify({'deactivated_chords': deactivated})
    except Exception as e:
        print(f"Error loading deactivated chords: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deactivated-chords', methods=['PUT'])
def update_deactivated_chords():
    """Update the list of deactivated chords."""
    try:
        data = request.json
        deactivated = data.get('deactivated_chords', [])
        
        if save_deactivated_chords(deactivated):
            return jsonify({'success': True, 'message': 'Deactivated chords updated'})
        else:
            return jsonify({'error': 'Failed to save deactivated chords'}), 500
    
    except Exception as e:
        print(f"Error updating deactivated chords: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/play-chord', methods=['POST'])
def play_chord():
    """Generate audio for a chord and return as WAV."""
    data = request.json
    
    frequencies = data.get('frequencies', [])
    instrument = data.get('instrument', 'piano').lower()
    playback_speed = data.get('playback_speed', 1.0)
    root_volume_multiplier = data.get('root_volume_multiplier', 1.0)
    chord_name = data.get('chord_name', '')
    
    # Validate input
    if not frequencies:
        print(f"Warning: No frequencies provided for chord {chord_name}")
        return jsonify({'error': 'No frequencies provided'}), 400
    
    print(f"Playing chord {chord_name}: {frequencies} at {playback_speed}x speed")
    
    # Get the appropriate audio player
    player = audio_players.get(instrument, audio_players['piano'])
    
    # Use fixed chord duration; playback_speed only affects spacing on frontend
    duration = 0.8
    
    # Generate chord by mixing frequencies with reduced volume
    num_freqs = len(frequencies)
    
    # Reduce individual tone volume to prevent clipping when mixing
    # For a chord of n notes, reduce each by 1/sqrt(n) to prevent amplitude explosion
    tone_volume = 1.0 / np.sqrt(max(num_freqs, 1))
    
    waveform = None
    for freq in frequencies:
        tone = player.generate_rich_tone(freq, duration, instrument)
        # Scale the tone to prevent clipping when mixed
        tone = tone * tone_volume
        
        if waveform is None:
            waveform = tone.copy()
        else:
            waveform = waveform + tone
    
    # If root volume multiplier is above 1.0, add extra emphasis to the
    # theoretical root note (not just the lowest/bass note).
    if root_volume_multiplier > 1.0:
        root_freq = None

        try:
            # Get semitone offset of this chord's root from C (tonic),
            # matching the desktop app logic.
            chord_enum = ChordNumber[chord_name] if chord_name in ChordNumber.__members__ else None
            if chord_enum is not None:
                chord_semitone_offset = chord_enum.value[0]

                semitone_factor = 2 ** (1/12)
                root_hz_at_octave = 262 * (semitone_factor ** chord_semitone_offset)

                min_distance = float('inf')
                for freq in frequencies:
                    if freq <= 0:
                        continue
                    # Calculate which semitone this frequency is from C4
                    semitones_from_c4 = np.log2(freq / 262) * 12
                    note_class = semitones_from_c4 % 12
                    target_note_class = chord_semitone_offset % 12

                    distance = min(abs(note_class - target_note_class),
                                   12 - abs(note_class - target_note_class))

                    if distance < min_distance:
                        min_distance = distance
                        root_freq = freq

        except Exception as e:
            print(f"Warning: could not determine theoretical root for chord {chord_name}: {e}")

        if root_freq is None:
            # Fallback: use lowest frequency if matching fails
            root_freq = min(frequencies)

        root_tone = player.generate_rich_tone(root_freq, duration, instrument)

        # Add the root tone with the specified multiplier.
        # A multiplier of 1.0 (0% slider) means no extra root.
        # Higher values add proportionally more root before final normalization.
        extra_root_volume = max(0.0, root_volume_multiplier - 1.0)
        waveform = waveform + (root_tone * extra_root_volume)
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val * 0.9  # Use 0.9 to leave more headroom
    
    # Convert waveform to audio file
    audio_data = (waveform * 32767).astype(np.int16)
    
    # Create bytes buffer
    buffer = io.BytesIO()
    wavfile.write(buffer, 44100, audio_data)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='audio/wav',
        as_attachment=False
    )

@app.route('/api/play-tone', methods=['POST'])
def play_tone():
    """Generate audio for a single tone (tonic reference)."""
    data = request.json
    
    frequency = data.get('frequency', 262.0)
    instrument = data.get('instrument', 'piano').lower()
    duration = data.get('duration', 1.0)
    
    print(f"Playing tone: {frequency}Hz for {duration}s")
    
    player = audio_players.get(instrument, audio_players['piano'])
    waveform = player.generate_rich_tone(frequency, duration, instrument)
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val * 0.9  # Use 0.9 to leave headroom
    
    # Convert waveform to audio file
    audio_data = (waveform * 32767).astype(np.int16)
    
    buffer = io.BytesIO()
    wavfile.write(buffer, 44100, audio_data)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='audio/wav',
        as_attachment=False
    )

@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """Check if the user's progression answer is correct."""
    try:
        data = request.json
        progression_names = data.get('progression', [])
        expected_names = data.get('expected', [])

        # Convert chord display names to enum names in a robust,
        # case-insensitive way (handles ii, V7, vii°, etc.).
        user_progression = []
        for chord_name in progression_names:
            # Normalize input (strip whitespace, then upper-case)
            raw = str(chord_name)
            normalized = raw.strip()
            upper = normalized.upper()

            # Treat VII° / vii° as VII
            if upper.endswith('°'):
                upper = upper[:-1]

            # Treat III+ as the augmented mediant enum
            if upper == 'III+':
                upper = 'IIIAUG'

            if upper in ChordNumber.__members__:
                user_progression.append(ChordNumber[upper])
            else:
                print(f"Warning: Unknown chord name '{chord_name}' (normalized: '{normalized}', upper: '{upper}')")
                return jsonify({'error': f'Unknown chord: {chord_name}'}), 400
        
        # Convert expected progression names to enum for comparison
        expected_progression = []
        for chord_name in expected_names:
            # Normalize input (strip whitespace, then upper-case)
            raw = str(chord_name)
            normalized = raw.strip()
            upper = normalized.upper()
            
            # Treat III+ as the augmented mediant enum
            if upper == 'III+':
                upper = 'IIIAUG'
            
            if upper in ChordNumber.__members__:
                expected_progression.append(ChordNumber[upper])
            else:
                # If conversion fails, just use the name as-is for comparison
                expected_progression.append(chord_name)
        
        # Check if user's answer matches the expected progression
        is_correct = user_progression == expected_progression
        
        # Ensure we have valid data to return
        if not expected_names:
            return jsonify({'error': 'No expected progression provided.'}), 400
        
        # Map chord names for display consistency (same as /api/progression)
        name_map = {
            ChordNumber.IIIAUG: "III+",
        }
        actual = [name_map.get(c, c.name) if isinstance(c, ChordNumber) else c for c in expected_progression]
        user = [name_map.get(c, c.name) for c in user_progression]
        
        return jsonify({
            'correct': is_correct,
            'actual': actual,
            'user': user
        })
    
    except Exception as e:
        print(f"Error in check_answer: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_file(os.path.join(STATIC_DIR, 'index.html'))

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc)."""
    return send_from_directory(STATIC_DIR, filename)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Run without the Flask debug reloader so we bind cleanly to all interfaces
    app.run(host="0.0.0.0", port=5001, debug=False)
