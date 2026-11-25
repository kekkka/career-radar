import unittest
from radar_experience import experience, header_experience, combine_experience, requirements_text
from radar_lifecycle import archived_label, is_closed

class RealScenarioTests(unittest.TestCase):
    def test_yandex_conflicting_requirements(self):
        title='Менеджер продукта «Колесо призов» в Маркет'
        chunks=[title,'Москва','От трёх лет','Мы ждём, что вы','Опыт от двух лет']
        self.assertEqual(combine_experience(header_experience(chunks,title),experience(requirements_text(chunks)))[0],'REVIEW_3_PLUS')
    def test_header_split(self):
        self.assertEqual(header_experience(['Менеджер продукта','От','2','лет'],'Менеджер продукта')[0],'POSSIBLE_MATCH')
    def test_no_unrelated_header(self):
        self.assertEqual(header_experience(['Менеджер продукта','Компания существует 20 лет'],'Менеджер продукта')[0],'UNKNOWN')
    def test_strict_minimum(self):
        self.assertEqual(experience('Опыт не менее двух лет')[0],'POSSIBLE_MATCH')
        self.assertEqual(experience('Опыт более двух лет')[0],'REVIEW_3_PLUS')
    def test_reverse_word_order(self):
        self.assertEqual(experience('Три года работали продактом')[0],'REVIEW_3_PLUS')
    def test_archived(self):
        self.assertTrue(archived_label(['Менеджер продукта','В архиве'],'Менеджер продукта'))
        self.assertTrue(is_closed('Вакансия находится в архиве'))
        self.assertFalse(is_closed('Работа с архивом документов'))
    def test_optional_section(self):
        text=requirements_text(['Требования','Опыт от 1 года','Будет плюсом','Опыт от 3 лет'])
        self.assertEqual(experience(text)[0],'POSSIBLE_MATCH')
