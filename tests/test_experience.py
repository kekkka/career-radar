import unittest
from radar_experience import experience

class ExperienceTests(unittest.TestCase):
    def test_required_and_company_age(self):
        self.assertEqual(experience('Компания работает на рынке 20 лет. Опыт от 1 года'),('POSSIBLE_MATCH','1 years'))
        self.assertEqual(experience('Работаем на рынке 15 лет')[0],'UNKNOWN')
    def test_required(self):
        for text in ('Опыт от 2 лет','Опыт 1–3 года','Опыт работы 6 месяцев','Без опыта'):
            with self.subTest(text=text): self.assertEqual(experience(text)[0],'POSSIBLE_MATCH')
    def test_exclusions(self):
        for text in ('Опыт более двух лет','Опыт 2,5 года','3+ years of experience','Работали продактом три года','At least three years','Опыт от 2 лет. Работали аналитиком 3 года'):
            with self.subTest(text=text): self.assertEqual(experience(text)[0],'REVIEW_3_PLUS')
    def test_optional(self):
        self.assertEqual(experience('Опыт от 3 лет будет преимуществом')[0],'UNKNOWN')
        self.assertEqual(experience('Опыт от 1 года, 3 года будут преимуществом')[0],'POSSIBLE_MATCH')
