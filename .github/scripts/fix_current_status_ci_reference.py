"""Remove a historical Actions URL from CURRENT_STATUS without changing evidence meaning."""
from pathlib import Path

path = Path("docs/CURRENT_STATUS.md")
text = path.read_text(encoding="utf-8")
old = "Targeted hosted run [`42341716342`](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/42341716342) passed"
new = "Targeted hosted run `42341716342` passed"
count = text.count(old)
if count != 1:
    raise RuntimeError(f"expected exactly one historical run link, found {count}")
updated = text.replace(old, new, 1)
if "actions/runs/42341716342" in updated:
    raise RuntimeError("historical Actions URL remains in CURRENT_STATUS")
path.write_text(updated, encoding="utf-8")
