import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox, QListWidget, QPushButton, QWidget
from fonesi_edit.app import (normalize_shortcut_remap, parse_shortcut_remap_json,
                             shortcut_focus_policy, should_dispatch_editor_shortcut)

APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("widget,expected", [
    (QLineEdit(), "text"),
    (QPlainTextEdit(), "text"),
    (QTextEdit(), "text"),
    (QSpinBox(), "control"),
    (QComboBox(), "control"),
    (QListWidget(), "control"),
    (QPushButton("Run"), "control"),
    (QWidget(), "global"),
])
def test_shortcut_focus_policy_classifies_interactive_focus(widget, expected):
    policy, target = shortcut_focus_policy(widget)
    assert policy == expected
    assert target is (widget if expected != "global" else None)


def test_shortcut_focus_policy_follows_parent_chain_for_editor_controls():
    parent = QSpinBox()
    child = QLineEdit(parent)
    policy, target = shortcut_focus_policy(child)
    assert policy == "text"
    assert target is child


def test_shortcut_focus_policy_treats_spinbox_internal_line_edit_as_control():
    spin = QSpinBox()
    policy, target = shortcut_focus_policy(spin.lineEdit())
    assert policy == "control"
    assert target is spin


def test_partial_shortcut_remap_merges_and_normalizes_existing_values():
    current = {"Undo": "Ctrl+Z", "Redo": "Ctrl+Shift+Z", "Save": "Ctrl+S"}
    changed = normalize_shortcut_remap({"Undo": "Ctrl+Y"}, current)
    assert changed == {"Undo": "Ctrl+Y", "Redo": "Ctrl+Shift+Z", "Save": "Ctrl+S"}


def test_shortcut_remap_allows_explicitly_disabling_one_action():
    current = {"Undo": "Ctrl+Z", "Redo": "Ctrl+Shift+Z"}
    assert normalize_shortcut_remap({"Undo": ""}, current) == {"Undo": "", "Redo": "Ctrl+Shift+Z"}


@pytest.mark.parametrize("payload", ["{", "[] trailing", "null", "7", '"Ctrl+S"'])
def test_shortcut_json_parser_rejects_malformed_or_non_object_payloads(payload):
    with pytest.raises(ValueError, match="JSON phím tắt|Tên thao tác"):
        parse_shortcut_remap_json(payload, {"Save": "Ctrl+S"})


def test_shortcut_json_parser_keeps_partial_updates_merged():
    current = {"Undo": "Ctrl+Z", "Redo": "Ctrl+Shift+Z", "Save": "Ctrl+S"}
    assert parse_shortcut_remap_json('{"Undo": "Ctrl+Y"}', current) == {
        "Undo": "Ctrl+Y", "Redo": "Ctrl+Shift+Z", "Save": "Ctrl+S"
    }


def test_shortcut_remap_rejects_duplicate_after_normalization():
    current = {"Undo": "Ctrl+Z", "Redo": "Ctrl+Shift+Z"}
    with pytest.raises(ValueError, match="trùng"):
        normalize_shortcut_remap({"Redo": "Ctrl+Z"}, current)


def test_shortcut_remap_rejects_multi_stroke_sequence():
    current = {"Undo": "Ctrl+Z", "Redo": "Ctrl+Shift+Z"}
    with pytest.raises(ValueError, match="một tổ hợp"):
        normalize_shortcut_remap({"Undo": "Ctrl+K, Ctrl+C"}, current)


def test_shortcut_remap_rejects_unknown_action_and_non_string_values():
    with pytest.raises(ValueError, match="Tên thao tác"):
        normalize_shortcut_remap({"Delete everything": "Ctrl+X"}, {"Undo": "Ctrl+Z"})
    with pytest.raises(ValueError, match="phải là chuỗi"):
        normalize_shortcut_remap({"Undo": 7}, {"Undo": "Ctrl+Z"})



def test_shortcut_remap_rejects_incomplete_sequence():
    current = {"Undo": "Ctrl+Z"}
    with pytest.raises(ValueError, match="không hợp lệ"):
        normalize_shortcut_remap({"Undo": "Ctrl+"}, current)



@pytest.mark.parametrize("action", [
    "Undo", "Redo", "Nhân bản", "Split", "Đưa vào hàng đợi", "Phát/dừng",
    "Marker", "Đặt In", "Đặt Out", "Nhóm layer", "Bỏ nhóm", "Khóa layer",
])
@pytest.mark.parametrize("policy", ["text", "control"])
def test_editor_shortcuts_yield_to_focused_text_and_controls(action, policy):
    assert not should_dispatch_editor_shortcut(action, policy)


@pytest.mark.parametrize("action", ["Mở", "Lưu", "Trợ giúp", "Quét công cụ", "Cài đặt"])
@pytest.mark.parametrize("policy", ["text", "control"])
def test_app_level_shortcuts_remain_available_when_controls_have_focus(action, policy):
    assert should_dispatch_editor_shortcut(action, policy)


def test_editor_shortcuts_dispatch_when_canvas_or_global_area_has_focus():
    assert should_dispatch_editor_shortcut("Phát/dừng", "global")
