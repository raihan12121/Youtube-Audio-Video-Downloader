"""
Desktop Application Entry Point: YouTube Video & Audio Bulk Downloader.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ui.main_window import MainWindow


def main():
    try:
        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        print("Application terminated by user.")
    except Exception as e:
        print(f"Fatal error running application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
