"""CLI and GUI entry points for ear training application."""

import sys
from ear_training.ui.gui import main_gui


if __name__ == "__main__":
    # Run GUI by default
    main_gui()
