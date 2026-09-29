import os
import tempfile
import unittest

from app import create_app

CSV = "category,amount,date\nfood,10,2024-01-01\nrent,500,2024-01-02\n"


class TestApi(unittest.TestCase):
    def setUp(self):
        self.client = create_app("sqlite:///:memory:").test_client()

    def _session(self):
        return self.client.post("/sessions").get_json()["session_id"]

    def test_health(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})

    def test_full_flow_csv_multi_turn(self):
        sid = self._session()
        r1 = self.client.post(f"/sessions/{sid}/upload", data=CSV, content_type="text/csv")
        self.assertEqual((r1.status_code, r1.get_json()["added"]), (201, 2))
        # second turn adds more data to the same session -> state persisted
        self.client.post(f"/sessions/{sid}/upload", data="category,amount,date\nfood,5,2024-02-01", content_type="text/csv")
        rep = self.client.get(f"/sessions/{sid}/report").get_json()
        self.assertEqual(rep["summary"]["count"], 3)
        self.assertEqual(rep["by_category"]["food"], 15.0)

    def test_json_upload(self):
        sid = self._session()
        r = self.client.post(f"/sessions/{sid}/upload", json={"rows": [{"category": "x", "amount": 1, "date": "2024-03-01"}]})
        self.assertEqual(r.status_code, 201)

    def test_validation_error_422(self):
        sid = self._session()
        r = self.client.post(f"/sessions/{sid}/upload", data="category,amount,date\nfood,abc,2024-01-01", content_type="text/csv")
        self.assertEqual(r.status_code, 422)
        self.assertIn("details", r.get_json())

    def test_unknown_session_404(self):
        self.assertEqual(self.client.get("/sessions/nope/report").status_code, 404)
        self.assertEqual(self.client.post("/sessions/nope/upload", data=CSV).status_code, 404)

    def test_sessions_are_isolated(self):
        a, b = self._session(), self._session()
        self.client.post(f"/sessions/{a}/upload", data=CSV, content_type="text/csv")
        self.assertEqual(self.client.get(f"/sessions/{b}/report").get_json()["summary"]["count"], 0)

    def test_state_persists_across_app_instances_with_file_db(self):
        with tempfile.TemporaryDirectory() as d:
            url = f"sqlite:///{os.path.join(d, 't.db')}"
            c1 = create_app(url).test_client()
            sid = c1.post("/sessions").get_json()["session_id"]
            c1.post(f"/sessions/{sid}/upload", data=CSV, content_type="text/csv")
            c2 = create_app(url).test_client()               # "restart"
            self.assertEqual(c2.get(f"/sessions/{sid}/report").get_json()["summary"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
