import copy
import hashlib
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from probe_market_brief_drive import FOLDER_MIME, ProbeError
from sync_market_brief_drive import collect, parse_json

FOLDER = "authorized_folder_123"
SUMMARY = "curated_summary_123"


class SourceFixture:
    def __init__(self):
        # The disabled independent-card publisher has its own frozen contract.
        # Live monthly briefs may instead contain one report with an embedded outlook.
        self.current = json.loads((Path(__file__).resolve().parent/"fixtures/market-brief-independent.json").read_text())
        self.current.pop("provenance", None)
        b = copy.deepcopy(self.current)
        self.report = b["sources"][0]["url"].split("/d/")[1].split("/")[0]
        self.forecast = b["sources"][1]["url"].split("/d/")[1].split("/")[0]
        f = b["forecast"]
        end=datetime.fromisoformat(f["evaluates_at"].replace("Z","+00:00")).astimezone(ZoneInfo("America/New_York"))
        # Real prose ends this decimal reference with a sentence-ending full stop.
        card = (f"{f['id']} Reference S&P 500: {f['reference_close']:,.2f}.\nFinal official close {end.strftime('%A %d %B %Y')} is the sole outcome measure.\n"
                + f"| Bull | {f['probabilities']['bull']:g}% | Greater than {f['upper_bound']:g} |\n"
                + f"| Base | {f['probabilities']['base']:g}% | Inclusive range |\n"
                + f"| Bear | {f['probabilities']['bear']:g}% | Less than {f['lower_bound']:g} |\nn={f['completed_sample']}")
        self.bodies = {self.report: b"Final independent market report fixture.", self.forecast: card.encode()}
        self.envelope = {"schema_version":1,"status":"FINAL","approved_for_publication":True,"brief":b}
        self.metadata = {FOLDER:{"id":FOLDER,"mimeType":FOLDER_MIME,"capabilities":{"canEdit":False,"canAddChildren":False}}}
        for key, file_id, source in (("source_report",self.report,b["sources"][0]),("source_forecast",self.forecast,b["sources"][1])):
            self.envelope[key] = {"id":file_id,"modified_at":source["modified_at"],"sha256":hashlib.sha256(self.bodies[file_id]).hexdigest()}
            name = f"{b['session_date']}-independent-us-market-ai-report-v1.md" if key == "source_report" else f"{f['id']}.md"
            self.metadata[file_id] = {"id":file_id,"name":name,"mimeType":"text/markdown","parents":[FOLDER],"modifiedTime":source["modified_at"],"capabilities":{"canEdit":False}}
        self.metadata[SUMMARY] = {"id":SUMMARY,"name":f"market-brief-{b['session_date']}-v1.json","mimeType":"application/json","parents":[FOLDER],"modifiedTime":b["issued_at"],"capabilities":{"canEdit":False}}
        self.now = datetime.fromisoformat(b["issued_at"].replace("Z","+00:00"))+timedelta(days=1)
        self.reads = []

    def get(self, file_id, *, media=False):
        self.reads.append((file_id,media))
        if not media:
            return copy.deepcopy(self.metadata[file_id])
        return json.dumps(self.envelope).encode() if file_id == SUMMARY else self.bodies[file_id]

    def list_children(self, folder):
        return [copy.deepcopy(m) for k,m in self.metadata.items() if k != FOLDER]

    def collect(self):
        return collect(self,FOLDER,self.current,self.now)


class SyncTests(unittest.TestCase):
    def test_verified_market_only_candidate_and_noop(self):
        s=SourceFixture()
        candidate=s.collect()
        self.assertEqual(candidate["session_date"],s.current["session_date"])
        self.assertEqual(candidate["forecast"],s.current["forecast"])
        self.assertNotIn("Final independent",json.dumps(candidate))
        s.current=candidate
        self.assertEqual(s.collect(),candidate)

    def test_new_report_without_summary_never_falls_back(self):
        s=SourceFixture()
        later=(datetime.fromisoformat(s.current["session_date"])+timedelta(days=3)).date().isoformat()
        s.metadata["new_report_123"]={"id":"new_report_123","name":later+".md","parents":[FOLDER]}
        with self.assertRaisesRegex(ProbeError,"Missing curated"):
            s.collect()

    def test_duplicate_report_and_summary_fail_closed(self):
        for source in ("report","summary"):
            s=SourceFixture()
            s.metadata["duplicate_file_123"]=copy.deepcopy(s.metadata[s.report if source=="report" else SUMMARY])
            with self.assertRaisesRegex(ProbeError,"Ambiguous duplicate"):
                s.collect()

    def test_source_hash_and_timestamp_must_match(self):
        for field in ("sha256","modified_at"):
            s=SourceFixture()
            s.envelope["source_report"][field]="0"*64 if field=="sha256" else "2000-01-01T00:00:00Z"
            with self.assertRaises(ProbeError):
                s.collect()

    def test_forecast_mutation_rejected_even_if_card_matches_new_probabilities(self):
        s=SourceFixture()
        s.envelope["brief"]["forecast"]["outlook"]="Rewritten after the fact"
        with self.assertRaisesRegex(ProbeError,"retrospectively"):
            s.collect()

    def test_probabilities_must_tie_to_card(self):
        s=SourceFixture()
        p=s.envelope["brief"]["forecast"]["probabilities"]
        p["bull"]+=1
        p["bear"]-=1
        with self.assertRaisesRegex(ProbeError,"probability does not match"):
            s.collect()

    def test_private_fields_text_and_unapproved_payload_rejected(self):
        for kind in ("field","text","unapproved"):
            s=SourceFixture()
            if kind=="field": s.envelope["brief"]["account_balance"]=100
            if kind=="text": s.envelope["brief"]["summary"]="My holdings and account number: 12345"
            if kind=="unapproved": s.envelope["approved_for_publication"]=False
            with self.assertRaises(ProbeError): s.collect()

    def test_source_outside_folder_or_writable_rejected(self):
        for kind in ("parent","write"):
            s=SourceFixture()
            if kind=="parent": s.metadata[s.report]["parents"]=["another_folder_123"]
            else: s.metadata[s.report]["capabilities"]["canEdit"]=True
            with self.assertRaises(ProbeError): s.collect()

    def test_future_and_stale_publication_rejected(self):
        for stamp in ("2099-01-01T00:00:00Z","2000-01-01T00:00:00Z"):
            s=SourceFixture()
            s.envelope["brief"]["issued_at"]=stamp
            with self.assertRaises(ProbeError): s.collect()

    def test_source_changes_mid_read_rejected(self):
        s=SourceFixture()
        original=s.get
        def changing(file_id,*,media=False):
            body=original(file_id,media=media)
            if file_id==s.report and media: s.metadata[file_id]["modifiedTime"]="2099-01-01T00:00:00Z"
            return body
        s.get=changing
        with self.assertRaisesRegex(ProbeError,"changed during"):
            s.collect()

    def test_duplicate_json_keys_and_nonfinite_numbers_rejected(self):
        for body in ('{"status":"FINAL","status":"DRAFT"}','{"p":NaN}'):
            with self.assertRaises(ProbeError): parse_json(body)


if __name__=="__main__": unittest.main()
