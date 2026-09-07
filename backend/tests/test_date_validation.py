import unittest
from IDscnr.backend.utils.date_utils import normalize_date_to_iso as norm, parse_iso_date as parse

class TestDateValidation(unittest.TestCase):
    def test_norm_formats(self):
        self.assertEqual(norm('1999-12-31'), '1999-12-31')
        self.assertEqual(norm('12/31/1999'), '1999-12-31')
        self.assertEqual(norm('31/12/1999'), '1999-12-31')
        self.assertEqual(norm('19991231'), '1999-12-31')
        self.assertEqual(norm('990101'), '1999-01-01')

    def test_parse_iso(self):
        dt = parse('1999-12-31')
        self.assertEqual(dt.year, 1999)
        self.assertEqual(dt.month, 12)
        self.assertEqual(dt.day, 31)

    def test_us_formatting(self):
        iso = norm('31/12/1999')
        y, m, d = iso.split('-')
        us = f"{m}/{d}/{y}"
        self.assertEqual(us, '12/31/1999')

if __name__ == '__main__':
    unittest.main()