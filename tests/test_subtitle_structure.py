import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path

from PySide6.QtWidgets import QApplication

from fonesi_edit.subtitle_editor import (
    CueStructureDialog,
    SubtitleEditor,
    write_new_srt,
)
from fonesi_edit.subtitles import (
    Cue,
    SubtitleDocument,
    export_srt,
    merge_next_cue,
    parse_srt,
    split_cue,
)
from fonesi_edit.timing import Interval


def document(locked=False):
    return SubtitleDocument(
        (
            Cue("a", Interval(F(0), F(2)), "Xin 中文🙂", locked),
            Cue("b", Interval(F(3), F(4)), "Next"),
        )
    )


class StructureTests(unittest.TestCase):
    def test_exact_unicode_split_and_roundtrip(self):
        original = document()
        result = split_cue(original, 0, F(1), 4, "new")
        left, right = result.cues[:2]
        self.assertEqual(left.text + right.text, original.cues[0].text)
        self.assertEqual(left.id, "a")
        self.assertEqual(right.id, "new")
        self.assertEqual(left.interval.end, right.interval.start)
        self.assertEqual(parse_srt(export_srt(result)).cues[1].text, right.text)
        self.assertEqual(len(original.cues), 2)

    def test_invalid_split_atomic(self):
        original = document()
        for row, at, offset, new_id in (
            (-1, F(1), 4, "new"),
            (True, F(1), 4, "new"),
            (0, F(0), 4, "new"),
            (0, F(2), 4, "new"),
            (0, F(1), 0, "new"),
            (0, F(1), 99, "new"),
            (0, F(1), True, "new"),
            (0, F(1), 4, "b"),
            (0, F(1, 10000), 4, "new"),
        ):
            with (
                self.subTest(row=row, at=at, offset=offset, new_id=new_id),
                self.assertRaises(ValueError),
            ):
                split_cue(original, row, at, offset, new_id)
        self.assertEqual(original, document())
        with self.assertRaises(ValueError):
            split_cue(document(True), 0, F(1), 4, "new")

    def test_blank_or_unrepresentable_text_split_rejects(self):
        for text, offset in ((" x", 1), ("x\ny", 2)):
            doc = SubtitleDocument((Cue("a", Interval(F(0), F(2)), text),))
            with self.assertRaises(ValueError):
                split_cue(doc, 0, F(1), offset, "new")

    def test_merge_gap_preserves_text_and_first_identity(self):
        original = document()
        result = merge_next_cue(original, 0)
        self.assertEqual(
            result.cues[0], Cue("a", Interval(F(0), F(4)), "Xin 中文🙂\nNext")
        )
        self.assertEqual(len(original.cues), 2)
        self.assertEqual(
            parse_srt(export_srt(result)).cues[0].text, result.cues[0].text
        )

    def test_merge_rejects_locks_overlap_reverse_and_last(self):
        for doc, row in (
            (document(True), 0),
            (document(), 1),
            (document(), False),
            (SubtitleDocument(tuple(reversed(document().cues))), 0),
            (
                SubtitleDocument(
                    (
                        Cue("a", Interval(F(0), F(3)), "a"),
                        Cue("b", Interval(F(2), F(4)), "b"),
                    )
                ),
                0,
            ),
        ):
            with self.subTest(doc=doc, row=row), self.assertRaises(ValueError):
                merge_next_cue(doc, row)
        locked_second = SubtitleDocument(
            (document().cues[0], Cue("b", Interval(F(3), F(4)), "b", True))
        )
        with self.assertRaises(ValueError):
            merge_next_cue(locked_second, 0)

    def test_merge_size_and_split_count_limits(self):
        big = SubtitleDocument(
            (
                Cue("a", Interval(F(0), F(1)), "a" * 50000),
                Cue("b", Interval(F(1), F(2)), "b" * 50000),
            )
        )
        with self.assertRaises(ValueError):
            merge_next_cue(big, 0)
        many = SubtitleDocument(
            tuple(
                Cue(str(i), Interval(F(i * 2), F(i * 2 + 2)), "ab")
                for i in range(10000)
            )
        )
        with self.assertRaises(ValueError):
            split_cue(many, 0, F(1), 1, "new")


class StructureUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.editor = SubtitleEditor()
        self.editor.model.replace(document(), remember=False)
        self.editor.table.setCurrentIndex(self.editor.model.index(0, 3))

    def tearDown(self):
        self.editor.close()
        self.app.processEvents()

    def test_native_split_undo_redo_and_cancel(self):
        self.assertTrue(self.editor.open_structure("split"))
        dialog = self.editor.structure_dialog
        dialog.offset.setValue(4)
        dialog.time_text.setText("00:00:01,000")
        self.assertTrue(dialog.apply_edit())
        self.assertEqual(len(self.editor.model.document.cues), 3)
        self.assertEqual(len(self.editor.model.undo_stack), 1)
        self.editor.model.undo()
        self.assertEqual(self.editor.model.document, document())
        self.editor.model.redo()
        self.assertEqual(len(self.editor.model.document.cues), 3)
        self.editor.table.setCurrentIndex(self.editor.model.index(0, 3))
        self.assertTrue(self.editor.open_structure("merge"))
        before = self.editor.model.document
        self.editor.structure_dialog.reject()
        self.assertIs(self.editor.model.document, before)
        self.assertEqual(len(self.editor.model.undo_stack), 1)

    def test_merge_and_stale_or_busy_apply(self):
        dialog = CueStructureDialog(self.editor, "merge", 0)
        self.editor.model.setData(self.editor.model.index(0, 3), "Changed")
        self.assertFalse(dialog.apply_edit())
        self.assertEqual(self.editor.model.document.cues[0].text, "Changed")
        dialog.reject()
        fresh = CueStructureDialog(self.editor, "merge", 0)
        self.editor.closing = True
        self.assertFalse(fresh.apply_edit())
        self.editor.closing = False
        self.editor.worker = object()
        self.assertFalse(fresh.apply_edit())
        self.editor.worker = None
        self.assertTrue(fresh.apply_edit())
        self.assertEqual(len(self.editor.model.document.cues), 1)
        self.editor.model.undo()
        self.assertEqual(len(self.editor.model.document.cues), 2)

    def test_structure_save_reopen_no_source_overwrite(self):
        original = document()
        split = split_cue(original, 0, F(1), 4, "new")
        with tempfile.TemporaryDirectory() as folder:
            source, destination = Path(folder) / "source.srt", Path(folder) / "new.srt"
            source.write_bytes(export_srt(original))
            before = source.read_bytes()
            write_new_srt(split, destination)
            parsed = parse_srt(destination.read_bytes())
            self.assertEqual(
                [(c.text, c.interval) for c in parsed.cues],
                [(c.text, c.interval) for c in split.cues],
            )
            with self.assertRaises(FileExistsError):
                write_new_srt(split, source)
            self.assertEqual(source.read_bytes(), before)

    def test_invalid_preview_and_parent_close(self):
        self.assertTrue(self.editor.open_structure("split"))
        dialog = self.editor.structure_dialog
        dialog.time_text.setText("invalid")
        self.assertFalse(dialog.apply_button.isEnabled())
        self.assertFalse(dialog.apply_edit())
        self.assertFalse(self.editor.model.undo_stack)
        self.editor.close()
        self.assertIsNone(self.editor.structure_dialog)
