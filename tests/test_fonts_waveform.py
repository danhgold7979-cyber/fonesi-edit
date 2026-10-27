from pathlib import Path
from threading import Event
from fontTools.ttLib import TTFont,TTCollection
from fonesi_edit.fonts import font_faces,open_font,missing_glyphs
from fonesi_edit.prototypes.media import find_font,create_fixture
from fonesi_edit.waveform import waveform


def test_collection_font_selects_the_requested_face_and_supports_glyph_checks(tmp_path):
    fonts=[TTFont(find_font()),TTFont(find_font())]
    for font,family in zip(fonts,['FonesiFaceA','FonesiFaceB']):
        for record in font['name'].names:
            if record.nameID in {1,4,6,16}:record.string=family.encode(record.getEncoding())
    collection=TTCollection();collection.fonts=fonts;path=tmp_path/'faces.ttc';collection.save(path)
    for font in fonts:font.close()
    assert [face['family'] for face in font_faces(str(path))]==['FonesiFaceA','FonesiFaceB']
    with open_font(path,{'font_family':'FonesiFaceB'}) as font:assert font['name'].getDebugName(1)=='FonesiFaceB'
    assert missing_glyphs(path,'Tiếng Việt',{'font_family':'FonesiFaceB'})==[]


def test_real_waveform_is_cached_without_touching_source(tmp_path):
    files=create_fixture(tmp_path/'media',duration=.5);source=files['source'];stamp=source.stat().st_mtime_ns
    first=waveform(source,tmp_path/'cache',Event());second=waveform(source,tmp_path/'cache',Event())
    assert first==second and Path(first['path']).read_bytes().startswith(b'\x89PNG')
    assert .4<first['duration']<.7 and source.stat().st_mtime_ns==stamp
