import unittest
from IDscnr.backend.ocr_utils import _parse_aamva_text, parse_fields_from_text

class TestDateParsing(unittest.TestCase):
    def test_aamva_fmt_date(self):
        raw = "DBB19900101\nDBA20301231\nDBD20150115\n"
        data = _parse_aamva_text(raw)
        self.assertEqual(data.get('date_of_birth'), '1990-01-01')
        self.assertEqual(data.get('expiration_date'), '2030-12-31')
        self.assertEqual(data.get('issue_date'), '2015-01-15')

    def test_mrz_dates(self):
        txt = "\nP<USAERIKSON<<ANNA<MARIA\n123456789<0USA9001012F2506303<<<<<<<<<<<<<<\n"
        parsed = parse_fields_from_text(txt)
        self.assertEqual(parsed.get('date_of_birth'), '1990-01-01')
        self.assertEqual(parsed.get('expiration_date'), '2025-06-30')

    def test_ddmmyyyy_passport_text(self):
        txt = "Passport\nDOB 31/12/1999\nEXP 30/06/2025\n"
        parsed = parse_fields_from_text(txt)
        self.assertEqual(parsed.get('date_of_birth'), '1999-12-31')
        self.assertEqual(parsed.get('expiration_date'), '2025-06-30')

    def test_mmddyyyy_id_text(self):
        txt = "DRIVER LICENSE\nDOB 12/31/1999\nEXP 06/30/2025\n"
        parsed = parse_fields_from_text(txt)
        self.assertEqual(parsed.get('date_of_birth'), '1999-12-31')
        self.assertEqual(parsed.get('expiration_date'), '2025-06-30')

if __name__ == '__main__':
    unittest.main()