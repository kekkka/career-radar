import unittest
from radar import classify, employer, run
import tempfile, json
from pathlib import Path
from unittest.mock import patch
class Test(unittest.TestCase):
 def test_rules(self):
  cases=[('Junior Product Manager','Без опыта', 'P1'),('Middle Product Manager','Опыт от 2 лет','P2'),('Менеджер продукта','Опыт от 1 года','P1'),('Product Manager','Опыт от 3 лет',None),('Senior Product Manager','Опыт от 1 года',None),('Product Manager','Опыт 1–3 года','P1'),('Product Manager','Желательно опыт от 3 лет','P3'),('Product Manager','Опыт от 2 лет\nОпыт управления от 3 лет','P3'),('Product Analyst','Опыт от 1 года','P1'),('Младший продуктовый аналитик','Без опыта','P1'),('Middle Product Analyst','Опыт от 2 лет','P2'),('Product Analyst','Опыт от 3 лет',None),('Senior Product Analyst','Опыт от 1 года',None),('Data Analyst','Опыт от 1 года. Анализ воронок и retention','P1'),('Data Analyst','Опыт от 1 года. SQL',None),('Бизнес-аналитик','Опыт от 1 года. Воронки и retention',None),('Аналитик продукта','Опыт от 2 лет','P2')]
  for title,desc,want in cases:
   with self.subTest(title=title,desc=desc):
    r=classify(title,desc); self.assertEqual(r[0] if r else None,want)
 def test_employer(self):
  self.assertEqual(employer('Avito'),'Авито'); self.assertIsNone(employer('Ozon'))
 def test_dedup(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'fixture.json'; f.write_text(json.dumps([dict(id='1',company='Авито',title='Product Manager',description='Опыт от 2 лет',url='https://example.com')]))
   with patch('radar.send') as send, patch('radar.time.sleep'):
    run(False,f,str(Path(d)/'db')); run(False,f,str(Path(d)/'db')); self.assertEqual(send.call_count,1)
if __name__=='__main__': unittest.main()
