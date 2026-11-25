import unittest
from radar_rss import rss_entries

class RSSDiscoveryTests(unittest.TestCase):
    def test_valid(self):
        item='<item><title>Product Manager</title><link>https://vacario.ru/management/product-manager-123</link></item>'
        self.assertEqual(rss_entries('<rss><channel>'+item+item+'</channel></rss>'),[('https://vacario.ru/management/product-manager-123','Product Manager')])
    def test_invalid(self):
        for raw in ('<html/>','<!DOCTYPE rss><rss/>','<rss/>'):
            with self.assertRaises(ValueError): rss_entries(raw)
    def test_untrusted_url(self):
        self.assertEqual(rss_entries('<rss><channel><item><title>PM</title><link>http://example.org/job</link></item></channel></rss>'),[])
