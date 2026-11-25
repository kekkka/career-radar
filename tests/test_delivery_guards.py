import unittest
from radar_lifecycle import active_application,posting_experience
class DeliveryGuards(unittest.TestCase):
    def test_open(self):
        self.assertTrue(active_application(['Product Manager','Откликнуться'],[],'Product Manager'))
        self.assertFalse(active_application(['Product Manager','В архиве','Откликнуться'],[],'Product Manager'))
        self.assertFalse(active_application(['Product Manager','Описание'],[],'Product Manager'))
    def test_structured(self):
        self.assertEqual(posting_experience([{'experienceRequirements':{'monthsOfExperience':36}}])[0],'REVIEW_3_PLUS')
        self.assertEqual(posting_experience([{'experienceRequirements':{'monthsOfExperience':24}}])[0],'POSSIBLE_MATCH')
        self.assertEqual(posting_experience([{'experienceRequirements':{'monthsOfExperience':True}}])[0],'UNKNOWN')
