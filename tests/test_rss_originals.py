import unittest
from radar_rss import rss_originals,official_url

class RSSOriginalTests(unittest.TestCase):
    def test_original(self):
        url='https://hr.tochka.com/vacancies/catalog/product-analyst'
        feed='<rss><channel><item><title>Product Analyst</title><link>https://vacario.ru/analytics/product-analyst-123</link><description><![CDATA[<a href="'+url+'">Откликнуться</a>]]></description></item></channel></rss>'
        self.assertEqual(rss_originals(feed,'Точка'),[('https://vacario.ru/analytics/product-analyst-123','Product Analyst',url)])
        self.assertEqual(rss_originals(feed,'Т-Банк'),[])
    def test_bad_urls(self):
        for url in ('https://hr.tochka.com.evil.example/vacancies/catalog/x','https://hr.tochka.com@evil.example/vacancies/catalog/x','https://hr.tochka.com/vacancies','http://hr.tochka.com/vacancies/catalog/x'):
            self.assertIsNone(official_url('Точка',url))
    def test_no_original(self):
        self.assertEqual(rss_originals('<rss><channel><item><title>PM</title><link>https://vacario.ru/management/pm-123</link></item></channel></rss>','Точка'),[])
