import unittest
from radar_commands import command_reply,command_keyboard

class CommandsTests(unittest.TestCase):
    def test_start(self):
        self.assertIn('внеплановый поиск',command_reply('/start',{}))
        self.assertIn('6 работодателям',command_reply('/start',{}))
    def test_status(self):
        msg=command_reply('/status',{'diagnostics':{'day':'2026-11-25','sent':3}}, {'cards':121,'sent':1})
        self.assertIn('2026-11-25',msg)
        self.assertIn('Новых вакансий: 3',msg)
        self.assertIn('Авито: 121',msg)
        self.assertNotIn('LinkedIn',msg)
    def test_empty(self):
        self.assertIn('ещё не сформирован',command_reply('/status',{}))
    def test_keyboard(self):
        self.assertEqual([x['text'] for x in command_keyboard()['keyboard'][0]],['/start','/status'])
        self.assertTrue(command_keyboard()['is_persistent'])
