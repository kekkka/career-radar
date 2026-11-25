import unittest
import json
from linkedin_intake import linkedin_records

class LinkedInTests(unittest.TestCase):
    def setUp(self):
        self.item={'id':'123456789','company':'Яндекс','title':'Product Manager','years':2}
    def parse(self,*items):
        return linkedin_records(json.dumps(items),{'Яндекс'})
    def test_valid(self):
        self.assertEqual(self.parse(self.item),[('Яндекс','Product Manager','https://www.linkedin.com/jobs/view/123456789',2)])
    def test_unknown(self):
        for x in (None,3,-1,True,'2'):
            self.assertEqual(self.parse(dict(self.item,years=x)),[])
    def test_untrusted(self):
        for update in ({'company':'Other'},{'id':'https://example.org'},{'title':'user@example.org'},{'body':'private'}):
            self.assertEqual(self.parse(dict(self.item,**update)),[])
    def test_invalid_payload(self):
        self.assertEqual(linkedin_records('not json',{'Яндекс'}),[])
