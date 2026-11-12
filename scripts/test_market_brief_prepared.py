import copy
import hashlib
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from probe_market_brief_drive import FOLDER_MIME, ProbeError
from verify_prepared_brief_source import newest_report, verify

ROOT, MONTH, REPORT = 'root_fixture_123', 'month_fixture_123', 'report_fixture_123'
NOW = datetime(2026, 10, 31, 5, tzinfo=timezone.utc)


class Fixture:
    def __init__(self):
        self.brief = json.loads((Path(__file__).parent/'fixtures/market-brief-independent.json').read_text())
        self.brief.pop('provenance', None)
        self.brief.update(session_date='2026-10-30', issued_at='2026-10-30T22:45:35.798Z')
        f = self.brief['forecast']
        f.update(id=f'drive:{REPORT}#us-original-outlook', evaluates_at='2026-11-04T21:00:00Z',
                 reference_close=7580.07, lower_bound=7480, upper_bound=7680,
                 probabilities={'bull':24,'base':43,'bear':33}, completed_sample=8)
        self.raw = ('8 个已结算窗口\n# 美股盘后日报 — 美国周五 30 Oct 2026 交易时段\n'
                    '## 9. 展望（Mon 2 – Wed 4 Nov，参考收盘 SPX 7,580.07）\n'
                    '| Bull | 24% | >7,680 |\n| Base | 43% | 7,480–7,680 |\n| Bear | 33% | <7,480 |\n'
                    '## 10. 预测记录\n## 今日澳股\n99 个已结算窗口\n').encode()
        self.brief['sources'] = [{'label':'Original report','url':f'https://drive.google.com/file/d/{REPORT}/view',
                                 'modified_at':self.brief['issued_at']},
                                {'label':'Treasury','url':'https://home.treasury.gov/'}]
        self.rehash()
        self.metadata = {
            ROOT: {'id':ROOT,'mimeType':FOLDER_MIME,'capabilities':{'canEdit':False,'canAddChildren':False}},
            MONTH: {'id':MONTH,'name':'2026-10','mimeType':FOLDER_MIME,'parents':[ROOT], 'capabilities':{'canEdit':False,'canAddChildren':False}},
            REPORT: {'id':REPORT,'name':'2026-10-31.md','mimeType':'text/markdown','parents':[MONTH],
                     'modifiedTime':self.brief['issued_at'],'capabilities':{'canEdit':False}}
        }

    def rehash(self):
        ref = {'id':REPORT,'modified_at':self.brief['issued_at'],'sha256':hashlib.sha256(self.raw).hexdigest()}
        self.brief['provenance'] = {'report':ref,'forecast':copy.deepcopy(ref)}

    def get(self, key, *, media=False):
        return self.raw if media else copy.deepcopy(self.metadata[key])

    def list_children(self, key):
        return [copy.deepcopy(v) for v in self.metadata.values() if key in v.get('parents', [])]

    def verify(self):
        return verify(self, ROOT, self.brief, NOW)


class PreparedSourceTests(unittest.TestCase):
    def test_structured_original_and_latest_modified(self):
        s = Fixture()
        extra = 'extra_archive_fixture'
        s.metadata[extra] = dict(s.metadata[ROOT], id=extra)
        s.metadata[REPORT].update(name='US_AI_Daily_2026-10-31_US-2026-10-30_v1.md', parents=[extra])
        s.metadata['older'] = dict(s.metadata[REPORT], id='older', modifiedTime='2026-10-30T22:44:00Z')
        s.brief['forecast']['id'] = 'IND-2026-10-31-3D-v1'
        s.raw = ('''| 最近完成的美国常规现金时段 | 2026-10-30（周五），16:00 EDT |
## 3. 三日 S&P 500 预测（NEW）与澳洲条件展望
### 3.1 预测块（固定解析字段）
Forecast ID: IND-2026-10-31-3D-v1
Issued: 2026-10-31 09:45:35 AEDT (UTC+11:00) / 2026-10-30 18:45:35 EDT (UTC-04:00)
Source US session: 2026-10-30
Reference S&P 500: 7580.07
Target session: 2026-11-04 16:00 America/New_York (2026-11-04T21:00:00Z)
Lower bound: 7480
Upper bound: 7680
Status: NEW
| Bull | > 7680 | 24% |
| Base | 7480 – 7680 (inclusive) | 43% |
| Bear | < 7480 | 33% |
### 3.5 澳洲条件展望
| Bull | > 9999 | 99% |
## 9. 历史预测台账
[计算] IND 序列已评分 8 个窗口。
''').encode()
        s.brief['issued_at'] = '2026-10-30T22:45:35Z'
        def rehash():
            s.rehash()
            for ref in s.brief['provenance'].values():
                ref['modified_at'] = s.metadata[REPORT]['modifiedTime']
        rehash()
        self.assertTrue(verify(s, ROOT, s.brief, NOW, extra)['source_verified'])
        original = s.raw
        for old, new in ((b'Status: NEW', b'Status: REVISED'), (b'24%', b'25%'),
                         (b'IND-2026-10-31', b'IND-2026-10-30'),
                         (b'21:00:00Z', b'20:00:00Z')):
            s.raw = original.replace(old, new)
            rehash()
            with self.subTest(change=new), self.assertRaises(ProbeError):
                verify(s, ROOT, s.brief, NOW, extra)
        s.raw = original
        rehash()
        s.metadata['older']['modifiedTime'] = '2026-10-30T22:46:00Z'
        with self.assertRaises(ProbeError):
            verify(s, ROOT, s.brief, NOW, extra)

    def test_section_nine_bullets_and_cumulative_sample(self):
        s = Fixture()
        s.raw = ('累计美股 Brier 现为 **0.721（8 个窗口，5.768/8）**\n'
                 '# 美股盘后日报 — 美国周五 30 Oct 2026 交易时段\n'
                 '## 9. 展望：Mon 2 – Wed 4 Nov 2026（参考 SPX 7,580.07）\n'
                 '- **Bull 24%**（收盘 **>7,680**，反弹）\n'
                 '- **Base 43%**（**7,480–7,680**，震荡）\n'
                 '- **Bear 33%**（收盘 **<7,480**，续跌）\n'
                 '## 10. 往绩\n## 今日澳股\n').encode()
        s.rehash()
        self.assertTrue(s.verify()['source_verified'])
        s.raw = s.raw.replace(b'/8', b'/9')
        s.rehash()
        with self.assertRaises(ProbeError):
            s.verify()

    def paragraph_fixture(self):
        s = Fixture()
        s.raw = ('8 个已结算原始窗口\n# 美股盘后日报 — 美国周五 30 Oct 2026 交易时段\n'
                 '## 4. 新美股展望：Mon 2 – Wed 4 Nov 2026（按 Wed 4 Nov 收盘判定，参考 SPX 7,580.07）\n'
                 '- Bull 24%（收盘 >7,680，回升）/ Base 43%（7,480–7,680）/ Bear 33%（收盘 <7,480，下跌）。\n'
                 '## 5. AI 核心表\n## 7. 今日澳股预测修正\n'
                 'Bull 99%（收盘 >9,999）/ Base 0%（1–9,999）/ Bear 1%（收盘 <1）\n').encode()
        s.rehash()
        return s

    def test_paragraph_original_preserves_all_source_gates(self):
        s = self.paragraph_fixture()
        self.assertTrue(s.verify()['source_verified'])
        for key, value in (('reference_close',7581),('lower_bound',7479),('upper_bound',7681),
                           ('completed_sample',99),('evaluates_at','2026-11-05T21:00:00Z')):
            s = self.paragraph_fixture(); s.brief['forecast'][key] = value
            with self.subTest(key=key), self.assertRaises(ProbeError): s.verify()
        s = self.paragraph_fixture(); s.brief['forecast']['probabilities'].update(bull=25,base=42)
        with self.assertRaises(ProbeError): s.verify()

    def test_paragraph_rejects_revisions_missing_duplicate_and_wrong_layout(self):
        for old, new in [('新美股展望','美股预测修正'), ('Bear 33%','Other 33%'),
                         ('收盘 >7,680','盘中 >7,680'),
                         ('## 5.', '- Bull 24%（收盘 >7,680）\n## 5.')]:
            s = self.paragraph_fixture(); s.raw = s.raw.replace(old.encode(), new.encode()); s.rehash()
            with self.subTest(change=new), self.assertRaises(ProbeError): s.verify()
        s = self.paragraph_fixture()
        s.raw += ('\n## 9. 展望（Mon 2 – Wed 4 Nov，参考收盘 SPX 7,580.07）\n'
                  '| Bull | 24% | >7,680 |\n').encode(); s.rehash()
        with self.assertRaises(ProbeError): s.verify()

    def test_monthly_original_and_short_horizon(self):
        s=Fixture()
        self.assertTrue(s.verify()['source_verified'])
        self.assertNotIn('raw', s.verify())

    def test_hash_timestamp_permissions_and_parent_fail_closed(self):
        for kind in ('hash','time','write','parent','root_write','month_parent'):
            s=Fixture()
            if kind=='hash': s.raw+=b'changed'
            if kind=='time': s.metadata[REPORT]['modifiedTime']='2026-10-31T01:00:00Z'
            if kind=='write': s.metadata[REPORT]['capabilities']['canEdit']=True
            if kind=='parent': s.metadata[REPORT]['parents']=['outside_folder_123']
            if kind=='root_write': s.metadata[ROOT]['capabilities']['canAddChildren']=True
            if kind=='month_parent': s.metadata[MONTH]['parents']=['outside_folder_123']
            with self.subTest(kind=kind), self.assertRaises(ProbeError): s.verify()

    def test_forecast_numbers_cannot_be_rewritten(self):
        for key, value in (('reference_close',7581),('lower_bound',7479),('upper_bound',7681),
                           ('completed_sample',99),('evaluates_at','2026-11-05T21:00:00Z')):
            s=Fixture(); s.brief['forecast'][key]=value
            with self.subTest(key=key), self.assertRaises(ProbeError): s.verify()
        s=Fixture(); s.brief['forecast']['probabilities'].update(bull=25,base=42)
        with self.assertRaises(ProbeError): s.verify()

    def test_latest_daily_not_weekly_or_preview(self):
        s=Fixture()
        for key,name in [('weekly','2026-10-31-weekly.md'),('preview','2026-10-31-PM.md')]:
            s.metadata[key]=dict(s.metadata[REPORT],id=key,name=name)
        self.assertTrue(s.verify()['source_verified'])
        s.metadata['new']=dict(s.metadata[REPORT],id='new_report_fixture_123',name='2026-10-31-v2.md')
        with self.assertRaises(ProbeError): s.verify()

    def test_duplicate_and_source_changes_rejected(self):
        s=Fixture(); s.metadata['dup']=dict(s.metadata[REPORT],id='dup')
        with self.assertRaisesRegex(ProbeError,'Ambiguous'): s.verify()
        s=Fixture(); original=s.get
        def changed(key, *, media=False):
            result=original(key,media=media)
            if media: s.metadata[key]['modifiedTime']='2026-10-31T01:00:00Z'
            return result
        s.get=changed
        with self.assertRaisesRegex(ProbeError,'changed during'): s.verify()

    def test_private_fields_and_non_us_report_rejected(self):
        s=Fixture(); s.brief['holdings']='private'
        with self.assertRaises(ProbeError): s.verify()
        s=Fixture(); s.raw=s.raw.replace('美股盘后日报'.encode(),'澳股盘后日报'.encode());s.rehash()
        with self.assertRaises(ProbeError): s.verify()

    def test_month_rollover_reads_previous_month(self):
        s=Fixture()
        month, report=newest_report(s,ROOT,datetime(2026,11,1,5,tzinfo=timezone.utc))
        self.assertEqual((month,report['id']),(MONTH,REPORT))


if __name__=='__main__': unittest.main()
