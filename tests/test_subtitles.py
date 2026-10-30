import unittest
from fractions import Fraction as F

from fonesi_edit.subtitles import (
    Cue,
    SubtitleDocument,
    export_srt,
    parse_srt,
    rounded_millis,
)
from fonesi_edit.timing import ClipMap, Interval


class SubtitleTests(unittest.TestCase):
    def test_unicode_multiline_bom(self):
        doc = parse_srt(
            "\ufeff1\r\n00:00:01,000 --> 00:00:02,500\r\nXin chào 中文\r\nDòng hai\r\n".encode()
        )
        self.assertEqual(doc.cues[0].text, "Xin chào 中文\nDòng hai")
        self.assertEqual(parse_srt(export_srt(doc)), doc)

    def test_invalid_times(self):
        for value in ["00:60:01,000", "00:00:01.000", "-1:00:00,000"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_srt(f"1\n{value} --> 00:00:03,000\nx".encode())

    def test_bad_encoding_and_bounds(self):
        for data in [b"\xff", b"a" * 4194305, b"1\n00:00:02,000 --> 00:00:01,000\nx"]:
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                parse_srt(data)

    def test_overlaps_report_not_deleted(self):
        doc = parse_srt(
            b"1\n00:00:01,000 --> 00:00:03,000\nx\n\n2\n00:00:02,000 --> 00:00:04,000\ny"
        )
        self.assertEqual(len(doc.cues), 2)
        self.assertEqual(
            doc.diagnostics(), (("OVERLAP", "srt-1"), ("OVERLAP", "srt-2"))
        )

    def test_map_keeps_text_lock_original(self):
        cue = Cue("cue", Interval(F(1), F(5)), "<i>Literal text</i>", True)
        doc = SubtitleDocument((cue,))
        mapped = doc.map_to(ClipMap(Interval(F(2), F(8)), F(3, 2), F(5)))
        self.assertEqual(
            mapped.cues[0], Cue("cue", Interval(F(5), F(7)), cue.text, True)
        )
        self.assertEqual(doc.cues[0], cue)

    def test_half_open_outside(self):
        doc = SubtitleDocument((Cue("c", Interval(F(0), F(1)), "x"),))
        self.assertEqual(doc.map_to(ClipMap(Interval(F(1), F(2)))).cues, ())

    def test_collapsed_export_rejected(self):
        with self.assertRaises(ValueError):
            export_srt(SubtitleDocument((Cue("c", Interval(F(0), F(1, 100000)), "x"),)))

    def test_rounding_ties_up(self):
        self.assertEqual(rounded_millis(F(1, 2000)), 1)

    def test_duplicate_identity(self):
        cue = Cue("c", Interval(F(0), F(1)), "x")
        with self.assertRaises(ValueError):
            SubtitleDocument((cue, cue))

    def test_ambiguous_export(self):
        with self.assertRaises(ValueError):
            export_srt(SubtitleDocument((Cue("c", Interval(F(0), F(1)), "x\n\ny"),)))

    def test_nonadjacent_overlap(self):
        doc = SubtitleDocument(
            (
                Cue("a", Interval(F(0), F(10)), "a"),
                Cue("b", Interval(F(1), F(2)), "b"),
                Cue("c", Interval(F(3), F(4)), "c"),
            )
        )
        self.assertIn(("OVERLAP", "c"), doc.diagnostics())

    def test_text_edge_spaces_preserved(self):
        doc = parse_srt(b"1\n00:00:00,000 --> 00:00:01,000\n  text  \n")
        self.assertEqual(doc.cues[0].text, "  text  ")
        self.assertEqual(parse_srt(export_srt(doc)), doc)

    def test_out_of_order_disjoint_not_overlap(self):
        doc = SubtitleDocument(
            (Cue("a", Interval(F(5), F(6)), "a"), Cue("b", Interval(F(1), F(2)), "b"))
        )
        self.assertEqual(doc.diagnostics(), (("OUT_OF_ORDER", "b"),))

    def test_overlap_sweep_matches_pairwise_oracle(self):
        import random

        rng = random.Random(81)
        for _ in range(100):
            cues = []
            for i in range(8):
                start = rng.randrange(10)
                end = start + rng.randrange(1, 5)
                cues.append(Cue(str(i), Interval(F(start), F(end)), "x"))
            expected = {
                c.id
                for i, c in enumerate(cues)
                if any(
                    c.interval.intersect(other.interval) is not None
                    for j, other in enumerate(cues)
                    if i != j
                )
            }
            actual = {
                identity
                for code, identity in SubtitleDocument(tuple(cues)).diagnostics()
                if code == "OVERLAP"
            }
            self.assertEqual(actual, expected)


class ReplacementTests(unittest.TestCase):
    def test_literal_unicode_and_locked_cues(self):
        from fonesi_edit.subtitles import replace_text

        doc = SubtitleDocument(
            (
                Cue("a", Interval(F(0), F(1)), "a.b 中文 a.b"),
                Cue("b", Interval(F(1), F(2)), "a.b", True),
            )
        )
        result = replace_text(doc, "a.b", "Xin")
        self.assertEqual(result.document.cues[0].text, "Xin 中文 Xin")
        self.assertEqual(result.document.cues[1], doc.cues[1])
        self.assertEqual(
            (result.changed_cues, result.occurrences, result.skipped_locked), (1, 2, 1)
        )
        self.assertEqual(doc.cues[0].text, "a.b 中文 a.b")

    def test_no_match_or_identical_replacement_retains_document(self):
        from fonesi_edit.subtitles import replace_text

        doc = SubtitleDocument((Cue("a", Interval(F(0), F(1)), "Abc"),))
        self.assertIs(replace_text(doc, "abc", "x").document, doc)
        self.assertIs(replace_text(doc, "Abc", "Abc").document, doc)

    def test_invalid_empty_and_expansion_are_atomic(self):
        from fonesi_edit.subtitles import replace_text

        doc = SubtitleDocument((Cue("a", Interval(F(0), F(1)), "x" * 100000),))
        for search, replacement in [
            ("", "x"),
            ("x" * 257, "a"),
            ("x", "y" * 1025),
            ("x", "yy"),
            ("x", ""),
            ("x", "\x00"),
        ]:
            with (
                self.subTest(search=search[:10], size=len(replacement)),
                self.assertRaises(ValueError),
            ):
                replace_text(doc, search, replacement)
        self.assertEqual(doc.cues[0].text, "x" * 100000)

    def test_unrepresentable_line_break_rejects(self):
        from fonesi_edit.subtitles import replace_text

        doc = SubtitleDocument((Cue("a", Interval(F(0), F(1)), "before x after"),))
        with self.assertRaises(ValueError):
            replace_text(doc, "x", "\n\n")
        self.assertEqual(doc.cues[0].text, "before x after")

    def test_total_utf8_expansion_bound(self):
        from fonesi_edit.subtitles import replace_text

        doc = SubtitleDocument(
            tuple(Cue(str(i), Interval(F(i), F(i + 1)), "x" * 80000) for i in range(14))
        )
        with self.assertRaisesRegex(ValueError, "SUBTITLE_TOO_LARGE"):
            replace_text(doc, "x", "🎬")
        self.assertTrue(all(c.text == "x" * 80000 for c in doc.cues))
