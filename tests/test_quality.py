import unittest
from urllib.error import HTTPError, URLError
from radar_quality import identity_keys, retry_fetch, source_status, daily_message

class QualityTests(unittest.TestCase):
    def test_tracking(self):
        self.assertEqual(identity_keys('Яндекс','https://example.com/job/1?utm_source=tg'),identity_keys('Яндекс','https://example.com/job/1'))
    def test_different_jobs(self):
        self.assertNotEqual(identity_keys('Яндекс','https://example.com/job/1'),identity_keys('Яндекс','https://example.com/job/2'))
    def test_query_ids(self):
        self.assertNotEqual(identity_keys('Яндекс','https://example.com/job?id=1'),identity_keys('Яндекс','https://example.com/job?id=2'))
    def test_linkedin(self):
        self.assertEqual(identity_keys('Яндекс','https://www.linkedin.com/jobs/view/product-manager-123?trk=x'),{'linkedin:123'})
    def test_avito(self):
        self.assertEqual(identity_keys('Авито','https://career.avito.com/vacancies/product/123/'),identity_keys('Авито','https://career.avito.com/publications/product/123/'))
    def test_untrusted(self):
        self.assertEqual(identity_keys('Авито','https://career.avito.com/vacancies/product/123/'),{'avito:123'})
        self.assertNotIn('avito:123',identity_keys('Авито','https://example.org/vacancies/product/123/'))
    def test_retry(self):
        stats={}; calls=[]
        def request():
            calls.append(1)
            if len(calls)<3: raise URLError('temporary')
            return 'ok'
        self.assertEqual(retry_fetch(request,stats,lambda _:None),'ok')
        self.assertEqual(stats['retries'],2)
    def test_no_retry_block(self):
        stats={}
        def request(): raise HTTPError('https://example.org',403,'blocked',{},None)
        with self.assertRaises(HTTPError): retry_fetch(request,stats,lambda _:None)
        self.assertEqual(stats,{})
    def test_status(self):
        self.assertEqual(source_status(1,0,0),'NO_CARDS_UNVERIFIED')
        self.assertEqual(source_status(1,0,1),'ERROR')
        self.assertEqual(source_status(2,1,1),'PARTIAL')
        self.assertEqual(source_status(2,1,0,True),'PARTIAL')
        self.assertEqual(source_status(1,3,0),'CARDS_FOUND')
    def test_report(self):
        self.assertIn('Без карточек (не подтверждено): 1',daily_message({'day':'2026-11-25','runs':1,'sent':0,'duplicates':0,'retries':0,'latest_health':{'X':'NO_CARDS_UNVERIFIED'}}))
