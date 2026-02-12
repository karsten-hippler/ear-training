const { createApp } = Vue;

createApp({
    data() {
        return {
            selectedInstrument: 'Piano',
            numChords: 'Random',
            rootVolume: 100,
            playbackSpeed: 1.0,
            startOnTonic: true,
            useCommonOnly: false,
            
            currentProgression: [],
            currentFrequencies: [],
            userProgression: [],
            score: 0,
            total: 0,
            
            resultMessage: '',
            resultClass: '',
            chordNotesDisplay: '',
            
            allChords: ['I', 'ii', 'iii', 'III7', 'IV', 'V', 'V7', 'vi', 'vii°'],
            progressionLength: 0,
            
            isPlaying: false,
            answeredCurrent: false,
        };
    },
    
    computed: {
        userProgressionDisplay() {
            if (this.userProgression.length === 0) {
                return '';
            }
            return this.userProgression.join(' - ');
        }
    },
    
    methods: {
        // Helper function to convert chord enum name to display format
        chordEnumToDisplay(enumName) {
            const displayMap = {
                'I': 'I',
                'II': 'ii',
                'III': 'iii',
                'III7': 'III7',
                'IV': 'IV',
                'V': 'V',
                'V7': 'V7',
                'VI': 'vi',
                'VII': 'vii°'
            };
            return displayMap[enumName] || enumName;
        },
        
        // Convert a frequency (Hz) to a note name like "C4"
        frequencyToNoteName(freq) {
            const noteNames = [
                'C', 'C#', 'D', 'D#', 'E', 'F',
                'F#', 'G', 'G#', 'A', 'A#', 'B'
            ];
            const semitonesFromA4 = 12 * Math.log2(freq / 440.0);
            const semitone = Math.round(semitonesFromA4);
            const octave = 4 + Math.floor((semitone + 9) / 12);
            const noteIndex = (semitone + 9) % 12;
            return noteNames[noteIndex] + octave;
        },

        // Build stacked chord notes display (voice leading grid),
        // similar to the desktop app's show_progression_notes.
        buildChordStackDisplay() {
            if (!this.currentProgression.length || !this.currentFrequencies.length) {
                return '';
            }

            const maxNotes = Math.max(
                ...this.currentFrequencies.map(freqs => freqs.length)
            );

            const lines = [];

            for (let noteIdx = 0; noteIdx < maxNotes; noteIdx++) {
                const line = [];

                for (let chordIdx = 0; chordIdx < this.currentProgression.length; chordIdx++) {
                    const freqs = this.currentFrequencies[chordIdx];

                    // Sort frequencies in descending order (top voice first)
                    const sortedFreqs = [...freqs].sort((a, b) => b - a);
                    const chordNotes = sortedFreqs.map(f => this.frequencyToNoteName(f));

                    if (noteIdx < chordNotes.length) {
                        line.push(chordNotes[noteIdx]);
                    } else {
                        line.push('');
                    }
                }

                lines.push(line);
            }

            // Header with chord numbers (use enum names, like desktop)
            const header = this.currentProgression
                .map(name => name.padStart(3, ' '))
                .join('  ');

            const separator = '-'.repeat(header.length);

            // Body: each line with notes aligned in columns
            const bodyLines = lines.map(line =>
                line.map(note => note.padStart(3, ' ')).join('  ').trimEnd()
            );

            return header + '\n' + separator + '\n' + bodyLines.join('\n');
        },
        
        async playProgression() {
            // Generate a new progression if the previous one has been answered
            // or if there is no progression yet.
            if (this.answeredCurrent || this.currentProgression.length === 0) {
                await this.generateNewProgression();
            }

            await this.playChordsSequence();
        },
        
        async playChordsSequence() {
            if (this.currentFrequencies.length === 0) return;
            
            this.isPlaying = true;

            // Prefetch all chord audio first so network and synthesis
            // latency do not affect the timing between chord onsets.
            const chordsCount = this.currentFrequencies.length;
            const audioElements = [];

            try {
                for (let i = 0; i < chordsCount; i++) {
                    const freqs = this.currentFrequencies[i];
                    const name = this.currentProgression[i];
                    const audio = await this.fetchChordAudio(freqs, name);
                    if (!audio) {
                        // If one chord fails, stop playback gracefully
                        this.isPlaying = false;
                        return;
                    }
                    audioElements.push(audio);
                }
            } catch (error) {
                console.error('Error prefetching chords:', error);
                this.isPlaying = false;
                return;
            }

            // Now schedule local playback with even spacing
            const baseDelay = 1200 / this.playbackSpeed; // ms between onsets

            audioElements.forEach((audio, index) => {
                const delay = index * baseDelay;
                setTimeout(() => {
                    const playPromise = audio.play();
                    if (playPromise !== undefined) {
                        playPromise.catch(err => console.error('Play error:', err));
                    }
                }, delay);
            });

            // Mark playback as finished after the last chord plus a buffer
            const totalDuration = (chordsCount - 1) * baseDelay + 1200;
            setTimeout(() => {
                this.isPlaying = false;
            }, totalDuration);
        },

        async fetchChordAudio(frequencies, chordName) {
            try {
                const response = await fetch('/api/play-chord', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        frequencies: frequencies,
                        instrument: this.selectedInstrument.toLowerCase(),
                        playback_speed: this.playbackSpeed,
                        root_volume_multiplier: this.rootVolume / 100.0,
                        chord_name: chordName
                    })
                });
                
                if (!response.ok) {
                    console.error('Error response from server:', response.status);
                    return null;
                }
                
                const audioBlob = await response.blob();
                console.log('Received audio blob:', audioBlob.size, 'bytes');
                
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.volume = 0.8; // Set volume to 80%

                return audio;
            } catch (error) {
                console.error('Error fetching chord audio:', error);
                return null;
            }
        },
        
        async playArpeggio() {
            if (this.currentFrequencies.length === 0) return;
            
            // Collect all notes from all chords
            const allNotes = [];
            for (const freqList of this.currentFrequencies) {
                allNotes.push(...freqList);
            }
            
            // Sort and remove duplicates
            allNotes.sort((a, b) => a - b);
            const uniqueNotes = [...new Set(allNotes)];
            
            this.isPlaying = true;
            
            for (let i = 0; i < uniqueNotes.length; i++) {
                const noteDuration = 0.3 / this.playbackSpeed;
                const delay = i * (350 / this.playbackSpeed);
                
                if (i > 0) {
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
                
                try {
                    const response = await fetch('/api/play-tone', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            frequency: uniqueNotes[i],
                            instrument: this.selectedInstrument.toLowerCase(),
                            duration: noteDuration
                        })
                    });
                    
                    if (!response.ok) {
                        console.error('Error response:', response.status);
                        continue;
                    }
                    
                    const audioBlob = await response.blob();
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    audio.volume = 0.8;
                    
                    const playPromise = audio.play();
                    if (playPromise !== undefined) {
                        playPromise.catch(error => console.error('Play error:', error));
                    }
                    
                    // Wait for note to finish
                    await new Promise(resolve => setTimeout(resolve, noteDuration * 1000 + 50));
                    
                } catch (error) {
                    console.error('Error playing tone:', error);
                }
            }
            
            this.isPlaying = false;
        },
        
        async repeatProgression() {
            await this.playChordsSequence();
        },
        
        async playTonic() {
            try {
                const response = await fetch('/api/play-tone', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        frequency: 262.0, // C4
                        instrument: this.selectedInstrument.toLowerCase(),
                        duration: 1.0
                    })
                });
                
                if (!response.ok) {
                    console.error('Error response:', response.status);
                    return;
                }
                
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.volume = 0.8;
                
                const playPromise = audio.play();
                if (playPromise !== undefined) {
                    playPromise.catch(error => console.error('Play error:', error));
                }
            } catch (error) {
                console.error('Error playing tonic:', error);
            }
        },
        
        async testAudio() {
            console.log('Testing audio generation...');
            try {
                const response = await fetch('/api/test-audio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        frequency: 440.0, // A4
                        duration: 1.0
                    })
                });
                
                if (!response.ok) {
                    console.error('Test audio error response:', response.status);
                    alert('Test audio failed: HTTP ' + response.status);
                    return;
                }
                
                const audioBlob = await response.blob();
                console.log('Test audio blob size:', audioBlob.size, 'bytes');
                
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.volume = 0.8;
                
                console.log('Playing test audio...');
                const playPromise = audio.play();
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => console.log('Test audio started playing'))
                        .catch(error => console.error('Test audio play error:', error));
                }
                
                alert('Test audio should be playing now (440 Hz sine wave). Check browser console for details.');
            } catch (error) {
                console.error('Error in test audio:', error);
                alert('Error testing audio: ' + error.message);
            }
        },
        
        async generateNewProgression() {
            try {
                const response = await fetch('/api/progression', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        num_chords: this.numChords,
                        start_on_tonic: this.startOnTonic,
                        use_common_only: this.useCommonOnly
                    })
                });
                
                const data = await response.json();
                this.currentProgression = data.progression;
                this.currentFrequencies = data.frequencies;
                this.progressionLength = data.length;
                this.userProgression = [];
                this.resultMessage = '';
                this.resultClass = '';
                this.chordNotesDisplay = '';
                this.answeredCurrent = false;
            } catch (error) {
                console.error('Error generating progression:', error);
            }
        },
        
        async guessChord(chord) {
            // First chord must be I if starting on tonic
            if (this.startOnTonic && this.userProgression.length === 0) {
                this.userProgression.push(chord);
                
                if (chord !== 'I') {
                    this.resultMessage = '✗ First chord should be I (Tonic)! Try again.';
                    this.resultClass = 'error';
                    this.userProgression = [];
                    return;
                }
            } else {
                this.userProgression.push(chord);
            }
            
            // Check if progression is complete
            if (this.userProgression.length === this.currentProgression.length) {
                await this.checkAnswer();
            }
        },
        
        async checkAnswer() {
            try {
                const response = await fetch('/api/check-answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        progression: this.userProgression
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    console.error('Error response:', data);
                    this.resultMessage = `Error: ${data.error}`;
                    this.resultClass = 'error';
                    return;
                }
                
                this.total += 1;
                
                // Convert enum names back to display format
                const actualDisplay = data.actual.map(name => this.chordEnumToDisplay(name));
                const correctProgressionText = actualDisplay.join(' - ');
                
                // In the solution box, show only the correct progression,
                // without any extra words or the user's answer.
                if (data.correct) {
                    this.score += 1;
                    this.resultMessage = correctProgressionText;
                    this.resultClass = 'success';
                } else {
                    this.resultMessage = correctProgressionText;
                    this.resultClass = 'error';
                }

                // After showing the solution, also show stacked chord notes
                this.chordNotesDisplay = this.buildChordStackDisplay();
                this.answeredCurrent = true;
            } catch (error) {
                console.error('Error checking answer:', error);
                this.resultMessage = `Error: ${error.message}`;
                this.resultClass = 'error';
            }
        },
        
        undoChord() {
            if (this.userProgression.length > 0) {
                this.userProgression.pop();
                this.resultMessage = '';
            }
        },
        
        exit() {
            if (this.total > 0) {
                const percentage = ((this.score / this.total) * 100).toFixed(1);
                alert(`Final Score: ${this.score}/${this.total} (${percentage}%)`);
            }
        }
    },
    
    mounted() {
        this.generateNewProgression();
    }
}).mount('#app');
