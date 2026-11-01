from pathlib import Path
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def empty_plan():
    return json.loads((ROOT/'docs/schemas/examples/empty-composition.json').read_text())
@pytest.fixture
def multi_plan():
    return json.loads((ROOT/'docs/schemas/examples/multi-stream-composition.json').read_text())
