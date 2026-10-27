"""Produce fresh CPU/FFmpeg evidence. Does not claim live source/Windows success."""
from pathlib import Path
from datetime import datetime, timezone
import json
import platform
import sys

from fonesi_edit.prototypes.media import RenderSpec, create_fixture, extract_frame, render
from fonesi_edit.prototypes.tools import scan_tools


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / ".local" / ("p02-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    records = {"os": platform.platform(), "python": sys.version.split()[0],
               "sample_kind": "synthetic lavfi; not a platform download", "tools": [t.to_dict() for t in scan_tools()], "renders": []}
    for name, portrait in (("landscape", False), ("portrait", True)):
        target = folder / name
        files = create_fixture(target, portrait=portrait)
        output = target / "result.mp4"
        result = render(files["source"], output, RenderSpec(subtitles=files["subtitles"], logo=files["logo"], speed_px_s=20))
        extract_frame(output, target / "frame.png", 0.2)
        records["renders"].append(result)
    records["not_verified"] = ["Windows package", "Google Chrome session handoff", "GPU", "live channel download", "live translation"]
    path = folder / "evidence.json"
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
