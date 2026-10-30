"""PyInstaller entry, no data or executable discovery at import time."""

from fonesi_edit.launch import main

if __name__ == "__main__":
    raise SystemExit(main())
