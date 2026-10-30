import json

import pytest

from fonesi_edit.domain import Clip, Composition, Layer
from fonesi_edit.presets import (
    MAX_PRESET_BYTES,
    build_preset_document,
    parse_preset_bytes,
)


def _composition_with_assets(tmp_path):
    source = tmp_path / "source.mp4"
    image = tmp_path / "logo.png"
    font = tmp_path / "Vietnamese.ttf"
    audio = tmp_path / "music.wav"
    for path in (source, image, font, audio):
        path.write_bytes(b"fixture")
    clip = Clip(str(source))
    image_layer = Layer(kind="image", path=str(image), clip_ids=[clip.id])
    text_layer = Layer(text="Xin chào")
    text_layer.style["font_file"] = str(font)
    return Composition(
        width=640,
        height=360,
        fps=25,
        clips=[clip],
        layers=[image_layer, text_layer],
        audio=[{"path": str(audio), "mode": "music"}],
    )


def _document():
    return build_preset_document(Composition(), "Preset hợp lệ")


def _inject_clip_binding(document):
    layer = Composition(layers=[Layer()]).to_dict()["layers"][0]
    layer["clip_ids"] = ["source-id"]
    document["composition"]["layers"] = [layer]


def test_build_and_parse_round_trip_strips_source_clips_and_preserves_assets(tmp_path):
    source = _composition_with_assets(tmp_path)
    document = build_preset_document(source, "  Preset Tiếng Việt  ")
    assert document["name"] == "Preset Tiếng Việt"
    assert document["schema_version"] == 1
    assert document["composition"]["clips"] == []
    assert all(layer["clip_ids"] == [] for layer in document["composition"]["layers"])

    parsed = parse_preset_bytes(json.dumps(document, ensure_ascii=False).encode("utf-8"))
    assert parsed.name == "Preset Tiếng Việt"
    assert parsed.composition.clips == []
    assert parsed.composition.layers[0].path == str(tmp_path / "logo.png")
    assert parsed.composition.layers[1].style["font_file"] == str(tmp_path / "Vietnamese.ttf")
    assert parsed.composition.audio[0]["path"] == str(tmp_path / "music.wav")
    assert parsed.missing_assets == ()


def test_missing_external_assets_are_reported_without_rejecting_preset(tmp_path):
    composition = Composition(
        layers=[Layer(kind="image", path=str(tmp_path / "gone-logo.png"))],
        audio=[{"path": str(tmp_path / "gone-music.wav"), "mode": "music"}],
    )
    payload = build_preset_document(composition, "Missing assets")
    parsed = parse_preset_bytes(json.dumps(payload).encode("utf-8"))
    assert parsed.name == "Missing assets"
    assert len(parsed.missing_assets) == 2
    assert any("gone-logo.png" in item for item in parsed.missing_assets)
    assert any("gone-music.wav" in item for item in parsed.missing_assets)


@pytest.mark.parametrize("name", ["", "   ", "../escape", "bad/name", "CON", "LPT1", "trailing.", "x" * 121])
def test_build_rejects_nonportable_or_invalid_preset_names(name):
    with pytest.raises(ValueError):
        build_preset_document(Composition(), name)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(schema_version=True),
        lambda d: d.update(schema_version=2),
        lambda d: d.update(extra="not allowed"),
        lambda d: d.update(name="../outside"),
        lambda d: d.update(composition=[]),
        lambda d: d["composition"].update(unknown_field=True),
        lambda d: d["composition"].update(adjustments={"api_key": "must-not-export"}),
        _inject_clip_binding,
        lambda d: d["composition"].update(clips=[{"path": "source.mp4"}]),
    ],
)
def test_parser_rejects_invalid_schema_or_composition_before_acceptance(mutate):
    document = _document()
    mutate(document)
    with pytest.raises(ValueError):
        parse_preset_bytes(json.dumps(document).encode("utf-8"))


def test_parser_rejects_duplicate_keys_and_non_finite_json():
    with pytest.raises(ValueError, match="Duplicate JSON object key"):
        parse_preset_bytes(b'{"schema_version":1,"schema_version":1,"name":"x","composition":{}}')
    with pytest.raises(ValueError, match="Non-finite"):
        parse_preset_bytes(b'{"schema_version":1,"name":"x","composition":{"adjustments":{"x":NaN}}}')


def test_parser_rejects_malformed_non_object_and_oversized_payloads():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_preset_bytes(b"{broken")
    with pytest.raises(ValueError, match="JSON object"):
        parse_preset_bytes(b"[]")
    with pytest.raises(ValueError, match="UTF-8"):
        parse_preset_bytes(b"\xff")
    with pytest.raises(ValueError, match="byte limit"):
        parse_preset_bytes(b" " * (MAX_PRESET_BYTES + 1))


def test_parser_rejects_invalid_audio_path():
    document = _document()
    document["composition"]["audio"] = [{"path": "", "mode": "music"}]
    with pytest.raises(ValueError, match="Invalid audio path"):
        parse_preset_bytes(json.dumps(document).encode("utf-8"))
