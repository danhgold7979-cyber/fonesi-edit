from copy import deepcopy
import uuid
import pytest

from fonesi_edit.domain.composition import CompositionPlan,PlanError


def _mask_layer(empty_plan,transform):
    return {
        'id':str(uuid.uuid4()),'type':'mask','z':0,
        'intervals':[{'start':[0,1],'end':empty_plan['output']['duration']}],
        'transform':deepcopy(transform),
        'style':{'mode':'color','amount':[0,1],'feather_px':[0,1],
                 'radius_px':[0,1],'color':[0,0,0,180]},
        'content':None,'keyframes':[],'visible':True,'locked_fields':[],
    }


def test_old_schema_v1_layers_without_group_id_remain_valid(empty_plan):
    empty_plan['layers']=[_mask_layer(empty_plan,deepcopy(empty_plan['layers'][0]['transform'])
                                      if empty_plan['layers'] else {
        'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
        'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
        'anchor':'center','flip_x':False,'flip_y':False})]
    assert 'group_id' not in empty_plan['layers'][0]
    CompositionPlan.parse(empty_plan)


def test_singleton_group_is_rejected(empty_plan):
    transform={'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
        'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
        'anchor':'center','flip_x':False,'flip_y':False}
    layer=_mask_layer(empty_plan,transform);layer['group_id']=str(uuid.uuid4())
    empty_plan['layers']=[layer]
    with pytest.raises(PlanError,match='at least two'):
        CompositionPlan.parse(empty_plan)


def test_shared_uuid_group_with_two_layers_is_valid(empty_plan):
    transform={'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
        'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
        'anchor':'center','flip_x':False,'flip_y':False}
    group_id=str(uuid.uuid4())
    first=_mask_layer(empty_plan,transform);first['group_id']=group_id
    second=_mask_layer(empty_plan,transform);second['z']=1;second['group_id']=group_id
    empty_plan['layers']=[first,second]
    CompositionPlan.parse(empty_plan)


def test_group_id_must_be_uuid(empty_plan):
    transform={'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
        'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
        'anchor':'center','flip_x':False,'flip_y':False}
    first=_mask_layer(empty_plan,transform);second=_mask_layer(empty_plan,transform)
    first['group_id']=second['group_id']='not-a-uuid'
    second['z']=1;empty_plan['layers']=[first,second]
    with pytest.raises(PlanError):
        CompositionPlan.parse(empty_plan)
