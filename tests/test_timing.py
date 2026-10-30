import unittest
from fractions import Fraction as F

from fonesi_edit.timing import ClipMap, Interval, time_value


class TimingTests(unittest.TestCase):
    def test_exact_fraction(self):
        self.assertEqual(time_value(1001, 30000) * 30000, 1001)

    def test_reject_noninteger_and_bad_denominator(self):
        for pair in [(True, 1), (1, False), (1, 0), (1, -1), (1.2, 1)]:
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                time_value(*pair)

    def test_interval_validation(self):
        for pair in [(F(-1), F(2)), (F(1), F(1)), (F(2), F(1)), (0, 1)]:
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                Interval(*pair)

    def test_half_open_disjoint(self):
        self.assertIsNone(Interval(F(0), F(2)).intersect(Interval(F(2), F(3))))

    def test_trim_speed_offset(self):
        clip = ClipMap(Interval(F(2), F(8)), F(3, 2), F(5))
        self.assertEqual(clip.output, Interval(F(5), F(9)))
        self.assertEqual(clip.map_interval(Interval(F(1), F(5))), Interval(F(5), F(7)))

    def test_clip_outside(self):
        self.assertIsNone(
            ClipMap(Interval(F(2), F(8))).map_interval(Interval(F(8), F(10)))
        )

    def test_speed_validation(self):
        for speed in [F(0), F(-1), 1.0]:
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                ClipMap(Interval(F(0), F(1)), speed)

    def test_no_drift(self):
        clip = ClipMap(Interval(F(0), F(100100, 30000)), F(1001, 1000))
        self.assertEqual(clip.output.duration, F(10, 3))


if __name__ == "__main__":
    unittest.main()
