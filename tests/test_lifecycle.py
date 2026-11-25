import unittest
from datetime import date
from radar_lifecycle import is_closed,vacancy_key,belongs_to_habr

class LifecycleTests(unittest.TestCase):
    def test_closed_markers(self):
        for text in ('Эта вакансия в архиве, но можно посмотреть похожие','Набор по вакансии закрыт','This job is no longer available'):
            self.assertTrue(is_closed(text))
    def test_active_and_dates(self):
        today=date(2026,11,25)
        self.assertFalse(is_closed('Работа с архивом документов',[],today))
        self.assertTrue(is_closed('',[{'validThrough':'2026-11-24T23:59:00Z'}],today))
        self.assertFalse(is_closed('',[{'validThrough':'2026-11-25'}],today))
        self.assertFalse(is_closed('',[{'validThrough':'invalid'}],today))
    def test_keys(self):
        self.assertNotEqual(vacancy_key('https://example.org/?view=1'),vacancy_key('https://example.org/?view=2'))
        self.assertEqual(vacancy_key('https://example.org/1?utm_source=x'),vacancy_key('https://example.org/1'))
    def test_company(self):
        self.assertTrue(belongs_to_habr([{'hiringOrganization':{'name':'Dodo Brands'}}],['Dodo Brands']))
        self.assertFalse(belongs_to_habr([{'hiringOrganization':{'name':'Other'}}],['Dodo Brands']))
        self.assertFalse(belongs_to_habr([],['Dodo Brands']))
