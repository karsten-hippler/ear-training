"""Main entry point for ear training application."""

import time
from ear_training.modules import IntervalTrainer, ChordTrainer, RhythmTrainer, Interval
from ear_training.ui.audio_player import AudioPlayer


def interval_training():
    """Interactive interval training loop."""
    trainer = IntervalTrainer()
    player = AudioPlayer(sample_rate=44100, duration=0.5)
    score = 0
    total = 0
    
    print("\nInterval Training Mode")
    print("Available intervals: " + ", ".join([i.name for i in Interval]))
    print("Type 'exit' to quit, 'replay' to hear the interval again\n")
    
    while True:
        # Generate and play interval
        interval = trainer.generate_interval()
        print(f"Playing interval #{total + 1}...")
        freq1, freq2 = trainer.get_frequencies()
        player.play_tone(freq1, duration=0.3)
        time.sleep(0.3)
        player.play_tone(freq2, duration=0.3)
        
        # Get user guess
        while True:
            guess = input("\nGuess the interval (or 'replay'/'exit'): ").strip().upper()
            
            if guess == "EXIT":
                print(f"\nSession ended. Score: {score}/{total}")
                return
            
            if guess == "REPLAY":
                print("Replaying...")
                player.play_tone(freq1, duration=0.3)
                time.sleep(0.3)
                player.play_tone(freq2, duration=0.3)
                continue
            
            # Try to match user input to interval
            try:
                user_interval = Interval[guess]
                is_correct = trainer.submit_answer(user_interval)
                total += 1
                
                if is_correct:
                    print(f"✓ Correct! It was {interval.name}")
                    score += 1
                else:
                    print(f"✗ Wrong. The correct answer was {interval.name}, you said {user_interval.name}")
                
                print(f"Score: {score}/{total}\n")
                break
            except KeyError:
                print(f"Invalid interval. Try again with one of: {', '.join([i.name for i in Interval])}")


def main():
    """Run the ear training application."""
    print("Welcome to Ear Training!")
    print("\nAvailable modules:")
    print("1. Interval Recognition")
    print("2. Chord Recognition")
    print("3. Rhythm Recognition")
    
    choice = input("\nSelect a module (1-3): ").strip()
    
    if choice == "1":
        interval_training()
    elif choice == "2":
        print("Chord training coming soon!")
    elif choice == "3":
        print("Rhythm training coming soon!")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
