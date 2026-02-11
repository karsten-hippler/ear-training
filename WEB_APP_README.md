# Ear Training Web App

A web-based version of the ear training application for harmonic progressions.

## Setup & Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the Flask server:**
```bash
python web_app.py
```

3. **Open in browser:**
Visit `http://localhost:5000`

## Features

- **Harmonic Progression Training**: Listen to chord progressions and identify them
- **Voice Leading**: Smooth transitions between chords with proper inversions
- **Adjustable Controls**:
  - Instrument selection (Piano, Bell, Violin, Flute)
  - Playback speed (0.5x - 2.0x)
  - Root note volume emphasis (100% - 400%)
  - Number of chords (2, 3, 4, 5, or Random)
  - Start on Tonic or random chord
  - Common progressions only mode

- **Interactive UI**: 
  - Play progression or arpeggio
  - Repeat last progression
  - Play tonic reference note
  - Undo last chord guess
  - Score tracking

## Architecture

### Backend (Flask)
- `web_app.py`: Main Flask application with REST API
- `/api/progression`: Generate new progressions
- `/api/play-chord`: Generate chord audio
- `/api/play-tone`: Generate single tone audio
- `/api/check-answer`: Validate user's progression guess

### Frontend (Vue.js)
- `static/index.html`: Main HTML structure
- `static/app.js`: Vue.js application logic
- `static/style.css`: Styling

## Deployment Options

### Heroku
```bash
heroku create your-app-name
git push heroku main
heroku open
```

### DigitalOcean
1. Create a droplet with Python
2. Clone your repository
3. Install dependencies
4. Run with Gunicorn: `gunicorn web_app:app`

### AWS Lightsail
Similar to DigitalOcean, use an application platform to run the Flask app.

### Vercel/Netlify (with backend)
Split into separate frontend (deployed to Vercel/Netlify) and backend deployment.

## API Reference

### GET `/`
Serves the main HTML page

### POST `/api/progression`
Generates a new chord progression

**Request:**
```json
{
  "num_chords": "3",
  "start_on_tonic": true,
  "use_common_only": false
}
```

**Response:**
```json
{
  "progression": ["I", "IV", "V"],
  "length": 3,
  "frequencies": [[frequencies...], [frequencies...], [frequencies...]]
}
```

### POST `/api/play-chord`
Generates audio for a chord

**Request:**
```json
{
  "frequencies": [262, 330, 392],
  "instrument": "piano",
  "playback_speed": 1.0,
  "root_volume_multiplier": 1.5,
  "chord_name": "I"
}
```

### POST `/api/play-tone`
Generates audio for a single tone

**Request:**
```json
{
  "frequency": 262.0,
  "instrument": "piano",
  "duration": 1.0
}
```

### POST `/api/check-answer`
Validates the user's progression guess

**Request:**
```json
{
  "progression": ["I", "IV", "V"]
}
```

**Response:**
```json
{
  "correct": true,
  "actual": ["I", "IV", "V"],
  "user": ["I", "IV", "V"]
}
```

## Development

To modify the application:

1. **Add new chords**: Edit `ChordNumber` enum in `ear_training/modules/progressions.py`
2. **Change audio synthesis**: Modify `AudioPlayer` in `ear_training/ui/audio_player.py`
3. **Adjust voice leading**: Update `_choose_next_chord()` in `ear_training/modules/progressions.py`
4. **Modify UI**: Edit `static/index.html`, `static/style.css`, and `static/app.js`

## License

MIT
