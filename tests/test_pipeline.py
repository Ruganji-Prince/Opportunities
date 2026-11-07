from datetime import datetime,timezone
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from src.core import normalize,match,deadline_instant,deadline_status,sort_key,canonical,deduplicate,extract_deadline,plain
from src.pipeline import refresh,ROOT
from src.notifications import notify

NOW=datetime(2026,11,7,12,tzinfo=timezone.utc)
SOURCE={'id':'test','name':'Test source','url':'https://example.org/api','organization':'Institute','enabled':True,'adapter':'rss'}
PROFILE=json.loads((ROOT/'config/profile.yaml').read_text())
WEIGHTS=json.loads((ROOT/'config/scoring.yaml').read_text())
def record(**kw):
    raw={'title':'Machine learning research internship','url':'https://example.org/apply','description':'Python machine learning PyTorch scientific computing','deadline':'2026-11-09T12:00:00+00:00','deadline_precision':'timestamp',**kw}
    return match(normalize(raw,SOURCE,NOW.isoformat()),PROFILE,WEIGHTS)

class CoreTests(unittest.TestCase):
    def test_timezones_equal(self):
        self.assertEqual(deadline_instant(record(deadline='2026-11-09T08:00:00-04:00')),deadline_instant(record()))
    def test_date_only_preserved(self):
        o=record(deadline='2026-11-09',deadline_precision='date',deadline_timezone='Africa/Kigali')
        self.assertEqual(o['deadline'],'2026-11-09');self.assertEqual(deadline_instant(o).isoformat(),'2026-11-09T22:00:00+00:00')
    def test_dst(self):
        self.assertEqual(deadline_instant(record(deadline='2026-03-08',deadline_precision='date',deadline_timezone='America/New_York')).hour,4)
    def test_expired(self): self.assertEqual(deadline_status(record(deadline='2026-11-06T00:00:00Z'),NOW),'Expired')
    def test_rolling(self): self.assertEqual(deadline_status(record(deadline=None,deadline_precision='rolling'),NOW),'Rolling')
    def test_unknown(self): self.assertEqual(deadline_status(record(deadline=None,deadline_precision='unknown'),NOW),'Deadline Unknown')
    def test_boundary(self): self.assertEqual(deadline_status(record(deadline=NOW.isoformat()),NOW),'Expired')
    def test_duplicate_url(self):
        self.assertEqual(canonical('https://Example.org/apply/?utm_source=x#top'),'https://example.org/apply')
        self.assertEqual(len(deduplicate([record(),record()])),1)
    def test_duplicate_attributes(self): self.assertEqual(len(deduplicate([record(),record(url='https://other.org/posting')])),1)
    def test_ineligible(self):
        o=record(title='Postdoctoral researcher machine learning');self.assertEqual(o['eligibility'],'restricted');self.assertLess(o['relevance_score'],55)
    def test_senior(self): self.assertEqual(record(title='Senior ML engineer')['eligibility'],'restricted')
    def test_unrelated_funding_not_recommended(self): self.assertLess(record(title='Civic leadership fellowship',description='Fully funded worldwide fellowship for civic leaders')['relevance_score'],55)
    def test_company_worldwide_not_global_eligibility(self): self.assertEqual(record(description='Python machine learning. Our company works worldwide.')['applicant_coverage'],'unknown')
    def test_explicit_global_eligibility(self): self.assertEqual(record(description='Python machine learning. Open to applicants from all countries.')['applicant_coverage'],'Global')
    def test_mandatory_doctorate_in_field(self): self.assertEqual(record(description='A PhD in computer science is required. Python PyTorch machine learning.')['eligibility'],'restricted')
    def test_cv_documented_skill_is_matched(self): self.assertIn('shap',record(description='SHAP explainability for health prediction')['tags'])
    def test_cv_and_brief_skills_not_double_counted(self):
        p=copy.deepcopy(PROFILE);p['cv_documented_skills']=p['verified_skills']
        o=record();without=copy.deepcopy(p);without['cv_documented_skills']=[]
        self.assertEqual(match(copy.deepcopy(o),p,WEIGHTS)['relevance_score'],match(copy.deepcopy(o),without,WEIGHTS)['relevance_score'])
    def test_score_tie(self):
        a=record();b=record(title='Other internship',url='https://example.org/b');a['relevance_score']=b['relevance_score']=70
        self.assertEqual(sorted([a,b],key=sort_key),sorted([b,a],key=sort_key))
    def test_same_date_relevance(self):
        a=record();b=record(url='https://example.org/b');a['relevance_score']=90;b['relevance_score']=60
        self.assertEqual(sorted([b,a],key=sort_key)[0]['id'],a['id'])
    def test_roll_unknown_follow_dated(self):
        a=record();b=record(deadline=None,deadline_precision='rolling');c=record(deadline=None,deadline_precision='unknown')
        self.assertEqual([sort_key(x)[0] for x in (a,b,c)],[0,1,2])
    def test_labeled_date(self):
        self.assertEqual(extract_deadline('Application Deadline: November 12th, 2026')['deadline'],'2026-11-12')
        self.assertIsNone(extract_deadline('Conference November 12, 2026'))
    def test_no_invented_year(self): self.assertIsNone(extract_deadline('Deadline November 12'))
    def test_sanitize(self): self.assertEqual(plain('<script>alert(1)</script><b>Research</b>'),'Research')
    def test_bad_url(self):
        with self.assertRaises(ValueError):canonical('javascript:alert(1)')

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'config',self.root/'config')
        (self.root/'config/sources.yaml').write_text(json.dumps([SOURCE]));settings=json.loads((self.root/'config/settings.yaml').read_text());settings['request_delay_seconds']=0;(self.root/'config/settings.yaml').write_text(json.dumps(settings))
    def tearDown(self): self.temp.cleanup()
    def rows(self,deadline='2026-11-09T12:00:00Z'):
        return lambda s,c:[{'title':'Machine learning research internship','url':'https://example.org/apply','description':'Python PyTorch machine learning','deadline':deadline,'deadline_precision':'timestamp'}]
    def test_source_outage_preserves(self):
        refresh(self.root,self.rows(),NOW)
        before=json.loads((self.root/'data/opportunities.json').read_text())
        def outage(s,c):raise OSError('offline')
        result=refresh(self.root,outage,NOW)
        self.assertEqual(result['status'],'failed');self.assertEqual(json.loads((self.root/'data/opportunities.json').read_text()),before)
    def test_deadline_change(self):
        refresh(self.root,self.rows(),NOW);r=refresh(self.root,self.rows('2026-12-01T12:00:00Z'),NOW)
        self.assertEqual(r['modified'],1);self.assertEqual(r['new'],0)
    def test_repeated_collection_updates_without_duplicates(self):
        refresh(self.root,self.rows(),NOW)
        before=json.loads((self.root/'data/opportunities.json').read_text())
        r=refresh(self.root,self.rows(),NOW)
        after=json.loads((self.root/'data/opportunities.json').read_text())
        self.assertEqual((r['new'],r['modified'],len(after)),(0,0,1));self.assertEqual(after[0]['id'],before[0]['id']);self.assertEqual(after[0]['first_discovered'],before[0]['first_discovered'])
    def test_salary_change_counts_as_update(self):
        refresh(self.root,self.rows(),NOW)
        def updated(s,c):
            rows=self.rows()(s,c);rows[0]['salary']='Published salary changed';return rows
        self.assertEqual(refresh(self.root,updated,NOW)['modified'],1)
    def test_clock_advance_archives_previous_active_record(self):
        refresh(self.root,self.rows(),NOW)
        later=datetime(2026,11,10,12,tzinfo=timezone.utc)
        result=refresh(self.root,self.rows(),later)
        self.assertEqual((result['active'],result['archived'],result['expired']),(0,1,1))
    def test_expired_archived(self):
        r=refresh(self.root,self.rows('2026-10-01T12:00:00Z'),NOW);self.assertEqual(r['active'],0);self.assertEqual(r['archived'],1)
    def test_no_credentials_no_delivery_claim(self):
        with patch.dict('os.environ',{},clear=True):
            history={};self.assertEqual(notify([record()],history,{'minimum_score':0,'alert_threshold_hours':[168,72,24]},NOW),[]);self.assertEqual(history,{})
    def test_failed_delivery_not_recorded(self):
        with patch.dict('os.environ',{'ENABLE_GITHUB_ALERTS':'true','GITHUB_TOKEN':'fixture','GITHUB_REPOSITORY':'test/test'},clear=True),patch('src.notifications.deliver',side_effect=OSError('offline')):
            history={};r=notify([record()],history,{'minimum_score':0,'alert_threshold_hours':[168,72,24]},NOW);self.assertEqual(history,{});self.assertEqual(r[0]['status'],'failed')
    def test_successful_delivery_deduplicated(self):
        with patch.dict('os.environ',{'ENABLE_GITHUB_ALERTS':'true','GITHUB_TOKEN':'fixture','GITHUB_REPOSITORY':'test/test'},clear=True),patch('src.notifications.deliver',return_value={'id':1}):
            history={};settings={'minimum_score':0,'alert_threshold_hours':[168,72,24]}
            self.assertEqual(notify([record()],history,settings,NOW)[0]['status'],'sent');self.assertEqual(notify([record()],history,settings,NOW),[])

if __name__=='__main__': unittest.main()
