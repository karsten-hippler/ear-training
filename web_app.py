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
    
    progression = progression_trainer.generate_progression(
        num_chords=num_chords,
        start_on_tonic=start_on_tonic,
        use_common_only=use_common_only
    )
    
    # Get frequencies for the progression
    frequencies = progression_trainer.get_progression_frequencies(use_inversions=True)
    
    # Return progression as strings
    progression_strs = [chord.name for chord in progression]
    
    return jsonify({
        'progression': progression_strs,
        'length': len(progression),
        'frequencies': frequencies
    })

@app.route('/api/test-audio', methods=['POST'])
def test_audio():
    """Test endpoint that generates a simple sine wave."""
    data = request.json
    frequency = data.get('frequency', 440.0)
    duration = data.get('duration', 1.0)
    
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    waveform = np.sin(2 * np.pi * frequency * t) * 0.7  # Reduced amplitude to 0.7
    
    # Convert to audio file
    audio_data = (waveform * 32767).astype(np.int16)
    
    buffer = io.BytesIO()
    wavfile.write(buffer, sample_rate, audio_data)
    buffer.seek(0)
    
    print(f"Generated test audio: {frequency}Hz, {duration}s, waveform min={waveform.min():.4f}, max={waveform.max():.4f}")
    
    return send_file(buffer, mimetype='audio/wav')

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
    
    # If root volume multiplier is high, add extra emphasis to the
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

        # Add the root tone with the specified multiplier (scaled reasonably)
        extra_root_volume = (root_volume_multiplier - 1.0) * 0.3
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
        
        # Convert chord names to enum (handle lowercase/mixed case)
        # Map the display names to enum names
        chord_map = {
            'I': 'I', 'i': 'I',
            'II': 'II', 'ii': 'II',
            'III': 'III', 'iii': 'III',
            'IV': 'IV', 'iv': 'IV',
            'V': 'V', 'v': 'V',
            'VI': 'VI', 'vi': 'VI',
            'VII': 'VII', 'vii': 'VII', 'vii°': 'VII'
        }
        
        user_progression = []
        for chord_name in progression_names:
            enum_name = chord_map.get(chord_name)
            if enum_name:
                user_progression.append(ChordNumber[enum_name])
            else:
                print(f"Warning: Unknown chord name '{chord_name}'")
                return jsonify({'error': f'Unknown chord: {chord_name}'}), 400
        
        is_correct = progression_trainer.submit_answer(user_progression)
        
        actual = [c.name for c in progression_trainer.current_progression]
        
        return jsonify({
            'correct': is_correct,
            'actual': actual,
            'user': [c.name for c in user_progression]
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
    app.run(host="0.0.0.0", port=5000, debug=False)
