"""
Diorite backend entry point.

Used by:
- PyInstaller (builds the standalone diorite-backend exe — no Python
  needed on the user's machine)
- Anyone who wants to run the backend without uvicorn CLI:
      python run_backend.py

Dev mode with hot-reload is still `python -m uvicorn app.main:app --reload`.
"""
import multiprocessing
import sys


def main() -> int:
    # Required by PyInstaller on Windows: prevents re-spawning the whole
    # frozen app when a multiprocessing/subprocess child is created.
    multiprocessing.freeze_support()

    import os
    import uvicorn

    from app.main import app

    port = int(os.getenv("DIORITE_PORT", "7331"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
