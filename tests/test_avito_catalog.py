import unittest
from radar_avito_catalog import can_skip_catalog
def classify(s): return 'PM' if 'product manager' in s.lower() else None
class CatalogueTests(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(can_skip_catalog(['Аналитик данных в Авито'],'Аналитик данных в Авито',classify))
    def test_new_or_generic(self):
        self.assertFalse(can_skip_catalog(['Аналитик данных'],'',classify))
        self.assertFalse(can_skip_catalog(['Подробнее'],'Аналитик данных',classify))
    def test_changed_or_conflicting(self):
        self.assertFalse(can_skip_catalog(['Аналитик данных','Product Manager'],'Аналитик данных',classify))
        self.assertFalse(can_skip_catalog(['Аналитик данных в B2C'],'Аналитик данных',classify))
    def test_target(self):
        self.assertFalse(can_skip_catalog(['Аналитик данных / Product Manager'],'Аналитик данных / Product Manager',classify))
        self.assertFalse(can_skip_catalog(['Аналитик данных / продуктовый аналитик'],'Аналитик данных / продуктовый аналитик',classify))
