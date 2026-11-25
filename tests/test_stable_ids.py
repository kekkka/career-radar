import unittest
from radar_quality import identity_keys
class StableIDTests(unittest.TestCase):
    def test_yandex_slug_and_service(self):
        a=identity_keys('Яндекс','https://yandex.ru/jobs/vacancies/old-title-12345')
        b=identity_keys('Кинопоиск','https://yandex.ru/jobs/vacancies/new-title-12345?utm_source=test')
        self.assertTrue(a&b)
        self.assertFalse(a&identity_keys('Яндекс','https://yandex.ru/jobs/vacancies/old-title-12346'))
    def test_tbank_host(self):
        jid='12345678-1234-1234-1234-123456789abc'
        self.assertTrue(identity_keys('Т-Банк','https://tbank.ru/career/it/vacancy/a/'+jid)&identity_keys('Т-Банк','https://www.tbank.ru/career/it/vacancy/b/'+jid))
    def test_aviasales_host(self):
        self.assertTrue(identity_keys('Авиасейлс','https://aviasales.ru/about/vacancies/123')&identity_keys('Авиасейлс','https://www.aviasales.ru/about/vacancies/123'))
    def test_unrelated_host(self):
        self.assertFalse(identity_keys('Яндекс','https://yandex.ru/jobs/vacancies/test-123')&identity_keys('Яндекс','https://example.org/jobs/vacancies/test-123'))
