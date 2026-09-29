import unittest

from app.services import logic, parser, reporting

CSV = "category,amount,date\nFood,12.5,2024-01-03\nfood,7.5,2024-01-20\nRent,900,2024-02-01\n"


class TestParser(unittest.TestCase):
    def test_parse_csv_normalises(self):
        recs = parser.parse_csv(CSV)
        self.assertEqual(len(recs), 3)
        self.assertEqual(recs[0]["category"], "food")

    def test_missing_columns(self):
        with self.assertRaises(parser.ParseError):
            parser.parse_csv("a,b\n1,2")

    def test_reports_all_row_errors(self):
        with self.assertRaises(parser.ParseError) as cm:
            parser.parse_csv("category,amount,date\nfood,abc,2024-01-01\nrent,5,01/02/2024\n")
        self.assertEqual(len(cm.exception.errors), 2)

    def test_thousands_separator(self):
        recs = parser.parse_rows([{"category": "x", "amount": "1,250.50", "date": "2024-01-01"}])
        self.assertEqual(recs[0]["amount"], 1250.5)

    def test_empty_rejected(self):
        with self.assertRaises(parser.ParseError):
            parser.parse_rows([])


class TestLogic(unittest.TestCase):
    def setUp(self):
        self.recs = parser.parse_csv(CSV)

    def test_totals_sorted_desc(self):
        self.assertEqual(list(logic.totals_by_category(self.recs)), ["rent", "food"])
        self.assertEqual(logic.totals_by_category(self.recs)["food"], 20.0)

    def test_monthly(self):
        self.assertEqual(logic.monthly_totals(self.recs), {"2024-01": 20.0, "2024-02": 900.0})

    def test_summary_empty(self):
        self.assertEqual(logic.summary_stats([])["count"], 0)

    def test_outlier_flagged(self):
        recs = [{"category": "a", "amount": a, "date": "2024-01-01"} for a in [10, 11, 9, 10, 12, 10, 500]]
        self.assertEqual([r["amount"] for r in logic.flag_outliers(recs)], [500])

    def test_report_shape(self):
        rep = reporting.build_report("s1", self.recs)
        self.assertEqual(set(rep), {"session_id", "summary", "by_category", "by_month", "outliers"})


if __name__ == "__main__":
    unittest.main()
