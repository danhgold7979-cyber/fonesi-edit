"""Windows packaging entry for the P02 proof, not the final application."""
from argparse import ArgumentParser
from pathlib import Path
from fonesi_edit.prototypes.gui import launch

if __name__ == "__main__":
    parser = ArgumentParser(description="Fonesi P02 packaging proof")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    raise SystemExit(launch(smoke=args.smoke, source=args.source, screenshot=args.screenshot))
