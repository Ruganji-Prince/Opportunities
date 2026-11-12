import unittest
from src.priority import hereon_records,date_from_text
from src.assessment import identity_key
from test_pipeline import record,NOW
import test_pipeline as fixtures
from src.pipeline import refresh
from src.storage import read

class EvidenceTests(unittest.TestCase):
    def test_paid_is_not_automatically_fully_funded(self):
        o=record(assessment={'funding_level':'paid','funding_evidence':'E13 employment contract'})
        self.assertTrue(o['funding_verified']);self.assertFalse(o['fully_funded_verified'])
    def test_explicit_full_funding(self):
        self.assertTrue(record(assessment={'funding_level':'fully_funded','funding_evidence':'Tuition and living expenses covered'})['fully_funded_verified'])
    def test_graduation_cutoff(self):
        o=record(assessment={'degree_completion_by':'2027-01-01'})
        self.assertEqual(o['graduation_compatibility'],'incompatible');self.assertEqual(o['eligibility'],'restricted')
    def test_german_requirement(self):
        self.assertEqual(record(assessment={'language_requirement':'German C1'})['eligibility'],'restricted')
    def test_daad_identity_ignores_path_variants(self):
        self.assertEqual(identity_key('https://www.daad.de/en/detail/10489?phd-id=10489'),identity_key('https://www.daad.de/en/detail/?phd-id=10489'))
    def test_hereon_rejects_administrative_rows_and_retains_earlier_conflict(self):
        body=b'<HELMHOLTZ><JOB><TITLE>Administrative assistant</TITLE><LINK>https://hereon.de/admin</LINK></JOB><JOB><TITLE>PhD materials digital twin</TITLE><LINK>https://hereon.de/phd</LINK><CLOSING_DATE>12.11.2027</CLOSING_DATE><DESCRIPTION>Application deadline: 11/12/2026. MSc required.</DESCRIPTION></JOB></HELMHOLTZ>'
        rows=list(hereon_records(body,{'url':'https://hereon.de/feed'}));self.assertEqual(len(rows),1);self.assertEqual(rows[0]['deadline'],'2026-11-12');self.assertTrue(rows[0]['assessment']['conflicts'])
    def test_numeric_application_due(self):
        self.assertEqual(date_from_text('Application due 22/11/2026')['deadline'],'2026-11-22')

class IdentityMergeTests(unittest.TestCase):
    setUp=fixtures.PipelineTests.setUp
    tearDown=fixtures.PipelineTests.tearDown
    rows=fixtures.PipelineTests.rows
    def test_url_variant_keeps_existing_saved_identity(self):
        def rows(url):return lambda s,c:[{'title':'PhD machine learning research','url':url,'description':'Python ML'}]
        refresh(self.root,rows('https://www.daad.de/en/detail/10489?phd-id=10489'),NOW)
        old=read(self.root/'data/opportunities.json',[])[0]
        result=refresh(self.root,rows('https://www.daad.de/en/detail/?phd-id=10489'),NOW)
        self.assertEqual(result['new'],0);self.assertEqual(read(self.root/'data/opportunities.json',[])[0]['id'],old['id'])
    def test_unknown_deadline_does_not_reopen_expired_cycle(self):
        refresh(self.root,self.rows('2026-10-01T12:00:00Z'),NOW)
        result=refresh(self.root,self.rows(None),NOW)
        self.assertEqual((result['active'],result['archived']),(0,1))


class DetailBudgetTests(unittest.TestCase):
    def test_detail_outage_uses_bounded_policy_and_keeps_feed_record(self):
        from unittest.mock import patch
        from src.collectors import collect
        source={'id':'bounded','name':'Bounded feed','adapter':'rss','url':'https://example.org/feed','details':True}
        settings={'timeout_seconds':25,'retries':2,'request_delay_seconds':0,'detail_timeout_seconds':8,'detail_retries':0}
        calls=[]
        def fetched(url,policy):
            calls.append((url,policy))
            if url.endswith('/feed'):return b'<rss><channel><item><title>PhD machine learning</title><link>https://example.org/detail</link><description>Doctoral call</description></item></channel></rss>'
            raise TimeoutError('detail unavailable')
        with patch('src.collectors.check_robots'),patch('src.collectors.fetch',side_effect=fetched):rows=list(collect(source,settings))
        self.assertEqual(len(rows),1);self.assertIn('detail_error',rows[0])
        self.assertEqual((calls[0][1]['timeout_seconds'],calls[0][1]['retries']),(25,2))
        self.assertEqual((calls[1][1]['timeout_seconds'],calls[1][1]['retries']),(8,0))
