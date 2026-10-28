from pathlib import Path
import pytest
from fonesi_edit.core.model import *
from fonesi_edit.services.editing import *
from fonesi_edit.services.motion import *
from fonesi_edit.services.renaming import *


def test_timeline_split_gap_ripple_and_source_safe():
    p=Project(assets=[Asset('source',id='a')],clips=[Clip('a',0,2*US),Clip('a',0,2*US,offset=2*US)],cues=[Cue(3*US,4*US,'last')],markers=[3*US])
    left,right=split_clip(p,US);assert len(p.clips)==3;assert p.duration==4*US
    delete_clip(p,left,ripple=False);assert p.clips[0].offset==US;assert p.duration==4*US
    delete_clip(p,right,ripple=True);assert p.clips[0].offset==US;assert p.cues[0].start==2*US;assert p.markers==[2*US]


def test_motion_seed_repeat_and_no_fps_dependency():
    layer=Layer(width=.2,height=.2)
    a=motion(layer,'random',duration=2*US,seed=42);b=motion(layer,'random',duration=2*US,seed=42)
    assert a==b;layer.keyframes=motion(layer,'ping-pong',duration=2*US,repeat=2)
    assert layer.at(US)['x']>layer.at(0)['x'];assert layer.at(2*US)['x']==layer.at(0)['x']
    layer.locked=True
    with pytest.raises(ValueError):motion(layer,'fade',duration=US)


def test_random_placement_avoid_and_failure():
    layer=Layer(width=.2,height=.2)
    a=layout_random(layer,2,[(0,0,.5,1)]);assert a['x']>=.5
    impossible=layout_random(layer,2,[(0,0,1,1)]);assert 'warning' in impossible and impossible['x']==layer.x


def test_preset_version_secrets_and_missing_asset(tmp_path):
    p=Project(layers=[Layer(kind='logo',asset_path=str(tmp_path/'missing.png'))]);preset=export_preset(p)
    restored=Project();assert import_preset(restored,preset)['missing_assets'];assert restored.layers[0].asset_path==p.layers[0].asset_path
    preset['schema_version']=99
    with pytest.raises(ValueError):import_preset(Project(),preset)


def test_relink_hash_identity_not_name(tmp_path):
    source=tmp_path/'moved.mp4';source.write_bytes(b'data')
    p=Project(assets=[Asset('/missing/old.mp4',fingerprint=content_hash(source))]);identity=p.assets[0].id
    assert relink(p,tmp_path)['relinked']==[identity];assert p.assets[0].id==identity


def test_rename_preview_apply_undo_and_conflict(tmp_path):
    paths=[]
    for n in range(2):p=tmp_path/f'a{n}.mp4';p.write_bytes(str(n).encode());paths.append(p)
    plan=plan_rename(paths,'C{n}');journal=tmp_path/'rename.json';apply_rename(plan,journal)
    assert (tmp_path/'C1.mp4').read_bytes()==b'0';assert not paths[0].exists()
    undo_rename(journal,tmp_path/'undo.json');assert paths[0].read_bytes()==b'0'
    (tmp_path/'C1.mp4').write_bytes(b'existing')
    with pytest.raises(FileExistsError):plan_rename(paths,'C{n}')
