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
    {"balance_candidates":0}, {"balance_candidates":65},
    {"balance_candidates":True}, {"balance_candidates":1.5},
    {"budget_seconds":True}, {"budget_seconds":"1"},
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


def test_large_space_candidate_loop_observes_cooperative_cancel():
    class CancelAfterChecks:
        def __init__(self):self.checks=0
        def is_set(self):
            self.checks+=1
            return self.checks>=4
    scenes=[[Angle(i+1,j+1,f"virtual/C{i+1}/G{j+1}.mp4",f"{i}-{j}")
             for j in range(6)] for i in range(14)]
    token=CancelAfterChecks()
    with pytest.raises(RuntimeError,match="Canceled"):
        generate(scenes,100,seed=7,window=1,different=2,
                 seconds=5,balance_candidates=8,cancel=token)
    assert token.checks==4


def test_large_space_candidate_selection_preserves_per_row_locks_and_wk():
    from fonesi_edit.matrix import matrix_rows_valid
    scenes=[[Angle(i+1,j+1,f"virtual/C{i+1}/G{j+1}.mp4",f"{i}-{j}")
             for j in range(4)] for i in range(8)]
    pinned=scenes[0][2].hash
    result=generate(scenes,80,seed=8,window=1,different=3,
                    seconds=5,locks={0:{0:pinned}},balance_candidates=8)
    assert result["complete"]
    assert result["rows"][0][0].hash==pinned
    assert matrix_rows_valid(result["rows"],[],1,3,False)


def test_large_space_solver_does_not_start_candidates_after_budget_expires():
    scenes=[[Angle(i+1,j+1,f"virtual/C{i+1}/G{j+1}.mp4",f"{i}-{j}")
             for j in range(6)] for i in range(14)]
    report=generate(scenes,100,seed=3,window=1,different=2,
                    seconds=1e-12,balance_candidates=8)
    assert not report["complete"] and report["rows"]==[]
    assert report["attempts"]==0


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



def test_large_space_candidate_competition_improves_per_scene_balance():
    baseline=benchmark(scenes=8,angles=4,outputs=600,window=1,different=2,
                       seed=2026,budget_seconds=8,balance_candidates=1)
    balanced=benchmark(scenes=8,angles=4,outputs=600,window=1,different=2,
                       seed=2026,budget_seconds=8,balance_candidates=8)
    assert baseline["complete"] and balanced["complete"]
    assert baseline["generated"]==balanced["generated"]==600
    assert baseline["theoretical_capacity"]==balanced["theoretical_capacity"]==4**8
    assert baseline["max_per_scene_spread"]>0
    assert balanced["max_per_scene_spread"]<baseline["max_per_scene_spread"]
    assert balanced["max_per_scene_spread"]<=4
    assert all(len(scene["angles"])==4 for scene in balanced["per_scene_usage"])
    assert all(sum(angle["uses"] for angle in scene["angles"])==600
               for scene in balanced["per_scene_usage"])


def test_large_space_balancing_keeps_equal_hashes_separate_per_scene():
    from fonesi_edit.matrix import combination
    # C1 is pinned to the shared hash for every output. C2 also contains
    # that same hash but must balance it locally against its other three Gs;
    # a global hash counter would treat C1's 120 uses as C2's usage.
    scenes=[
        [Angle(1,index+1,f"virtual/C1/G{index+1}.mp4",
               "shared" if index==0 else f"c1-{index}")
         for index in range(101)],
        [Angle(2,index+1,f"virtual/C2/G{index+1}.mp4",
               "shared" if index==0 else f"c2-{index}")
         for index in range(4)],
        [Angle(3,index+1,f"virtual/C3/G{index+1}.mp4",f"c3-{index}")
         for index in range(101)],
        [Angle(4,index+1,f"virtual/C4/G{index+1}.mp4",f"c4-{index}")
         for index in range(101)],
    ]
    locks={row:{"0":"shared"} for row in range(120)}
    result=generate(scenes,120,seed=41,window=0,different=0,
                    locks=locks,seconds=5,balance_candidates=8)
    assert result["complete"] and len(result["rows"])==120
    assert len({combination(row) for row in result["rows"]})==120
    assert result["usage"][0]["angles"][0]["uses"]==120
    # The same hash in C2 is balanced as a separate scene-local identity.
    assert result["usage"][1]["angles"][0]["hash"]=="shared"
    assert result["usage"][1]["angles"][0]["uses"]==30
    assert all(sum(angle["uses"] for angle in scene["angles"])==120
               for scene in result["usage"])



@pytest.mark.parametrize("kwargs",[
    {"scenes":0},{"angles":0},{"outputs":False},{"window":-1},
    {"different":100},{"budget_seconds":float("nan")},
    {"balance_candidates":0},{"balance_candidates":65},
    {"balance_candidates":True},{"balance_candidates":2.5},
])
def test_logical_benchmark_rejects_bad_configuration(kwargs):
    with pytest.raises(ValueError,match="Invalid logical"):
        benchmark(**kwargs)
