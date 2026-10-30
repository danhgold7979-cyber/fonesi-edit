"""Pure timing constraints for the draggable subtitle cue lane."""
import pytest
from fonesi_edit.ui.cue_timeline import retime_cue


def test_move_keeps_duration_and_clamps_negative_origin():
    assert retime_cue(1000,3000,500)==(1500,3500)
    assert retime_cue(1000,3000,-5000)==(0,2000)
    assert retime_cue(0,1,-100)==(0,1)


def test_edge_trims_never_reverse_or_remove_cue():
    assert retime_cue(1000,3000,-700,'start')==(300,3000)
    assert retime_cue(1000,3000,9000,'start')==(2999,3000)
    assert retime_cue(1000,3000,-9000,'end')==(1000,1001)
    assert retime_cue(0,1000,500,'end')==(0,1500)


@pytest.mark.parametrize('start,end,delta,mode',[
    (-1,100,10,'move'),(100,100,10,'move'),(500,100,-10,'move'),
    (0,100,True,'move'),(0,100,.5,'move'),(0,100,0,'unknown')
])
def test_bad_drag_inputs_rejected_before_mutation(start,end,delta,mode):
    with pytest.raises(ValueError):
        retime_cue(start,end,delta,mode)
