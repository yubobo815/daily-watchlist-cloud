import copy
import unittest

from probe_market_brief_drive import FOLDER_MIME, MAX_BYTES, NoRedirect, ProbeError, probe

FOLDER = "authorized_folder_123"
REPORT = "published_report_123"
FORECAST = "published_forecast_123"


class FakeReader:
    def __init__(self):
        self.metadata = {
            FOLDER: {"id": FOLDER, "mimeType": FOLDER_MIME, "capabilities": {"canEdit": False, "canAddChildren": False}},
            REPORT: {"id": REPORT, "mimeType": "text/markdown", "parents": [FOLDER], "capabilities": {"canEdit": False}},
            FORECAST: {"id": FORECAST, "mimeType": "text/markdown", "parents": [FOLDER], "capabilities": {"canEdit": False}},
        }
        self.content = {REPORT: b"Private source text", FORECAST: b"Private forecast text"}

    def get(self, file_id, *, media=False):
        return self.content[file_id] if media else copy.deepcopy(self.metadata[file_id])


class DriveProbeTests(unittest.TestCase):
    def test_read_only_access_without_returning_content(self):
        result = probe(FakeReader(), FOLDER, [REPORT, FORECAST])
        self.assertEqual(result, {"status": "ok", "folder_read_only": True, "readable_source_files": 2, "private_content_logged": False})
        self.assertNotIn("Private", repr(result))

    def test_reject_write_or_unknown_permissions(self):
        for capability in ("canEdit", "canAddChildren"):
            for value in (True, None):
                with self.subTest(capability=capability, value=value):
                    reader = FakeReader()
                    reader.metadata[FOLDER]["capabilities"][capability] = value
                    with self.assertRaises(ProbeError):
                        probe(reader, FOLDER, [REPORT, FORECAST])

    def test_reject_wrong_folder_type(self):
        reader = FakeReader()
        reader.metadata[FOLDER]["mimeType"] = "text/plain"
        with self.assertRaises(ProbeError):
            probe(reader, FOLDER, [REPORT, FORECAST])

    def test_reject_source_outside_folder(self):
        reader = FakeReader()
        reader.metadata[REPORT]["parents"] = ["another_folder_123"]
        with self.assertRaises(ProbeError):
            probe(reader, FOLDER, [REPORT, FORECAST])

    def test_reject_writable_source(self):
        reader = FakeReader()
        reader.metadata[REPORT]["capabilities"]["canEdit"] = True
        with self.assertRaises(ProbeError):
            probe(reader, FOLDER, [REPORT, FORECAST])

    def test_reject_empty_oversized_or_binary_source(self):
        for content in (b"", b"   ", b"a" * (MAX_BYTES + 1)):
            reader = FakeReader()
            reader.content[REPORT] = content
            with self.assertRaises(ProbeError):
                probe(reader, FOLDER, [REPORT, FORECAST])
        reader = FakeReader()
        reader.metadata[REPORT]["mimeType"] = "application/pdf"
        with self.assertRaises(ProbeError):
            probe(reader, FOLDER, [REPORT, FORECAST])

    def test_reject_duplicate_or_missing_sources(self):
        for sources in ([REPORT], [REPORT, REPORT], []):
            with self.assertRaises(ProbeError):
                probe(FakeReader(), FOLDER, sources)

    def test_never_forward_authorization_through_redirect(self):
        with self.assertRaises(ProbeError):
            NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://untrusted.example")


if __name__ == "__main__":
    unittest.main()
