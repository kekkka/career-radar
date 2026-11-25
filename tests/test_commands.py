import unittest
from radar_commands import command_reply

class CommandsTests(unittest.TestCase):
    def test_start(self):
        self.assertIn('Career Radar',command_reply('/start',{}))
    def test_status(self):
        self.assertIn('2026-11-25',command_reply('/status',{'diagnostics':{'day':'2026-11-25','sent':3}}))
        self.assertIn('3',command_reply('/status',{'diagnostics':{'sent':3}}))
    def test_empty(self):
        self.assertIn('ещё не сформирован',command_reply('/status',{}))
