"""P09 solver parameter validation and logical matrix stress evidence."""
from threading import Event
import math
import pytest
from fonesi_edit.matrix import Angle, generate, matrix_rows_valid
from pathlib import Path
from runpy import run_path

# The CLI lives outside the installed package. Load its actual file, not a
# fictitious importable `scripts` package (pytest runs from installed src).
benchmark = run_path(str(Path(__file__).resolve().parents[1] /
                         "scripts" / "benchmark_matrix.py"))["benchmark"]


def _scenes():
    return [[Angle(i+1,j+1,f"virtual/C{i+1}/G{j+1}.mp4",f"{i}-{j}")
             for j in range(3)] for i in range(2)]


@pytest.mark.parametrize("options", [
    {"count":True}, {"count":2.5}, {"count":0},
    {"window":False}, {"window":-1}, {"different":True},
    {"different":3}, {"seed":None}, {"seed":1.5},
    {"compare_window":1}, {"seconds":0}, {"seconds":float("nan")},
    {"seconds":float("inf")}, {"seconds":"2"}, {"seconds":True},
])
def test_matrix_rejects_malformed_parameters_before_search(options):
    arguments={"count":2}
    arguments.update(options)
    with pytest.raises(ValueError):
        generate(_scenes(),**arguments)


def test_matrix_empty_universe_refused_and_pre_cancel_keeps_input():
    with pytest.raises(ValueError,match="Empty matrix"):
        generate([],1)
    universe=_scenes()
    old=[[a.hash for a in group] for group in universe]
    cancel=Event();cancel.set()
    with pytest.raises(RuntimeError,match="Canceled"):
        generate(universe,2,cancel=cancel)
    assert [[a.hash for a in group] for group in universe]==old


def test_logical_stress_large_product_does_not_allocate_cartesian_media():
    report=benchmark(scenes=14,angles=6,outputs=100,window=1,different=2,
                     seed=123,budget_seconds=3)
    assert report["theoretical_capacity"]==6**14
    assert report["complete"] and report["generated"]==100
    assert report["unique_and_wk_valid"] and report["source_unchanged"]
    assert report["python_tracemalloc_peak_bytes"]>0
    assert "no FFprobe" in report["limitations"]


def test_matrix_seeded_logical_result_is_reproducible_without_clock_threshold():
    first=benchmark(scenes=4,angles=3,outputs=8,window=1,different=2,
                    seed=3,budget_seconds=3)
    second=benchmark(scenes=4,angles=3,outputs=8,window=1,different=2,
                     seed=3,budget_seconds=3)
    for key in ("generated","complete","attempts","theoretical_capacity"):
        assert first[key]==second[key]


def test_logical_benchmark_reports_incomplete_search_without_claiming_unsat():
    # Under K=2 a binary 2-scene matrix must alternate exact complements.
    # A third unique composition cannot follow; the budget is deliberately tiny.
    report=benchmark(scenes=2,angles=2,outputs=3,window=1,different=2,
                     seed=11,budget_seconds=.025)
    assert report["requested"]==3
    assert 0<=report["generated"]<3
    assert report["complete"] is False
    assert report["unique_and_wk_valid"]
    assert "no claim" in report["limitations"]



@pytest.mark.parametrize("kwargs",[
    {"scenes":0},{"angles":0},{"outputs":False},{"window":-1},
    {"different":100},{"budget_seconds":float("nan")},
])
def test_logical_benchmark_rejects_bad_configuration(kwargs):
    with pytest.raises(ValueError,match="Invalid logical"):
        benchmark(**kwargs)
