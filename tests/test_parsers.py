"""Offline extraction fixtures, never exported as real opportunities."""
import copy
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from src.parsers import feed_records,euraxess_detail,jobinrwanda_detail,jobinrwanda_links,article_detail
from src.collectors import check_robots,collect
from src.core import normalize,match,deduplicate,deadline_status,relevant
from tests.test_pipeline import PROFILE,WEIGHTS,NOW,SOURCE,record

class FeedTests(unittest.TestCase):
    def test_creator_and_category(self):
        body=b'<rss><channel><item><title>PhD machine learning</title><link>/jobs/123</link><description>Python research</description><category>Funded</category><creator>University</creator></item></channel></rss>'
        raw=list(feed_records(body,{**SOURCE,'creator_is_organization':True}))[0]
        self.assertEqual(raw['organization'],'University');self.assertEqual(raw['url'],'https://example.org/jobs/123');self.assertEqual(raw['source_category'],'Funded')
    def test_declared_encoding(self):
        body='<?xml version="1.0" encoding="ISO-8859-1"?><rss><channel><item><title>PhD caf\xe9</title><link>https://example.org/job</link></item></channel></rss>'.encode('latin-1')
        self.assertEqual(list(feed_records(body,SOURCE))[0]['title'],'PhD caf\xe9')
    def test_atom_namespace(self):
        body=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Research</title><link href="https://example.org/job"/><summary>Python</summary></entry></feed>'
        self.assertEqual(list(feed_records(body,SOURCE))[0]['description'],'Python')
    def test_drupal_debug_prefix(self):
        body=b'<!-- Debug -->\n<?xml version="1.0"?><rss><channel><item><title>PhD</title><link>https://example.org/p</link></item></channel></rss>'
        self.assertEqual(len(list(feed_records(body,SOURCE))),1)
    def test_empty_feed_is_not_fabricated(self):self.assertEqual(list(feed_records(b'<rss><channel/></rss>',SOURCE)),[])
    def test_daad_structured_calendar_deadline(self):
        body=b'<rss><channel><item><title>ML doctoral position</title><link>https://example.org/phd</link><company><name>Institute</name></company><location>Berlin</location><applicationDeadline>04. Dec 2026</applicationDeadline></item></channel></rss>'
        raw=list(feed_records(body,{**SOURCE,'structured_phd':True,'host_country':'Germany'}))[0]
        self.assertEqual(raw['deadline'],'2026-12-04');self.assertEqual(raw['location'],'Berlin, Germany');self.assertEqual(raw['organization'],'Institute');self.assertEqual(raw['deadline_precision'],'date')
    def test_html_is_not_a_feed(self):
        with self.assertRaises(ValueError):list(feed_records(b'<html><body>Blocked</body></html>',SOURCE))
    def test_funded_phd_category_does_not_assert_eligibility(self):
        raw={'title':'Machine learning for materials','url':'https://example.org/p','description':'Python PyTorch statistical learning','source_category':'PhD Studentship (Funded)','funding_evidence':'Official funded PhD category'}
        o=match(normalize(raw,SOURCE,NOW.isoformat()),PROFILE,WEIGHTS)
        self.assertEqual(o['subcategory'],'PhD');self.assertEqual(o['funding_status'],'funded');self.assertEqual(o['eligibility'],'unknown')

class DetailTests(unittest.TestCase):
    def test_euraxess_deadline_country_and_application(self):
        html='<main id="block-rtd-euraxess-main-page-content"><dl><dt>Organisation/Company</dt><dd>Institute</dd><dt>Country</dt><dd>Portugal</dd><dt>Application Deadline</dt><dd><time datetime="2026-11-09T23:59:00+00:00">9 Nov 2026 - 23:59 (Europe/Lisbon)</time></dd></dl><p>Python research</p><a class="job-apply-button" href="https://example.org/apply">Apply</a></main>'
        raw=euraxess_detail(html,{'title':'PhD','url':'https://example.org/job'})
        self.assertEqual(raw['deadline'],'2026-11-09T23:59:00+00:00');self.assertEqual(raw['deadline_timezone'],'Europe/Lisbon');self.assertEqual(raw['location'],'Portugal');self.assertEqual(raw['application_url'],'https://example.org/apply')
    def test_mailto_not_used_as_application_website(self):
        raw=euraxess_detail('<a class="job-apply-button" href="mailto:office@example.org">Apply</a>',{'url':'https://example.org/job'})
        self.assertNotIn('application_url',raw)
    def test_rwanda_listing_limits_to_job_links(self):
        rows=list(jobinrwanda_links('<a href="/user/login">Login</a><a href="/job/ml">ML engineer</a><a href="/job/ml">duplicate</a>','https://example.org'))
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['title'],'ML engineer')
    def test_rwanda_summary_date_excludes_related_jobs(self):
        html='<h1>ML engineer</h1><div id="block-jobemployerblock"><a href="/employer/lab">Lab</a></div><div class="field--name-field-job-full-description">Location: Kigali, Rwanda Purpose of role: Python machine learning</div><div id="block-jobsummaryblock">Deadline: Sunday, 06/12/2026 23:59</div><aside>Deadline: 01/01/2020</aside>'
        raw=jobinrwanda_detail(html,{'url':'https://example.org/job'})
        self.assertEqual(raw['deadline'],'2026-12-06');self.assertEqual(raw['deadline_precision'],'date');self.assertIsNone(raw['deadline_timezone']);self.assertEqual(raw['organization'],'Lab');self.assertIn('Rwanda',raw['location'])
    def test_rwanda_changed_schema_is_reported(self):
        with self.assertRaises(ValueError):jobinrwanda_detail('<html>Different website</html>',{'url':'https://example.org/job'})
    def test_article_text_excludes_script_and_navigation(self):
        raw=article_detail('<nav>Ignore</nav><div class="entry-content">Python fellowship<script>bad()</script></div>',{})
        self.assertEqual(raw['description'],'Python fellowship')
    def test_robots_denial(self):
        with patch('src.collectors.fetch',return_value=b'User-agent: *\nDisallow: /private/'):
            with self.assertRaises(PermissionError):check_robots({**SOURCE,'url':'https://example.org/private/feed'},{})
    def test_missing_robots_allows_published_feed(self):
        with patch('src.collectors.fetch',side_effect=HTTPError('https://example.org/robots.txt',404,'Not Found',{},None)):check_robots(SOURCE,{})
    def test_forbidden_robots_is_not_bypassed(self):
        with patch('src.collectors.fetch',side_effect=HTTPError('https://example.org/robots.txt',403,'Forbidden',{},None)):
            with self.assertRaises(HTTPError):check_robots(SOURCE,{})
    def test_detail_outage_keeps_feed_evidence(self):
        body=b'<rss><channel><item><title>PhD machine learning</title><link>https://example.org/job</link><description>Feed evidence</description></item></channel></rss>'
        with patch('src.collectors.check_robots'),patch('src.collectors.time.sleep'),patch('src.collectors.fetch',side_effect=[body,OSError('offline')]):
            rows=list(collect({**SOURCE,'details':True},{'request_delay_seconds':0}))
        self.assertEqual(rows[0]['description'],'Feed evidence');self.assertIn('offline',rows[0]['detail_error'])
    def test_aliases_remain_unique_on_repeated_merge(self):
        a=record();b=record(url='https://example.org/other');merged=deduplicate([a,b]);merged=deduplicate([*merged,b])
        self.assertEqual(merged[0]['additional_sources'],['https://example.org/other'])
    def test_unknown_institution_not_enough_to_merge_distinct_posts(self):
        a=record(organization='unknown');b=record(organization='unknown',url='https://example.org/other')
        self.assertEqual(len(deduplicate([a,b])),2)
    def test_spaced_postdoctoral_title_is_restricted(self):self.assertEqual(record(title='Post Doctoral Research Associate')['eligibility'],'restricted')
    def test_internal_auditor_not_misclassified_as_intern(self):self.assertEqual(record(title='Junior Internal Auditor')['subcategory'],'job')
    def test_international_heading_alone_not_opportunity_type(self):self.assertFalse(relevant({'title':'International community update'}))

if __name__=='__main__':unittest.main()
