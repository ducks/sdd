import unittest
from catalog import create_app

class CatalogTests(unittest.TestCase):
    def setUp(self):self.client=create_app().test_client()
    def test_item(self):
        r=self.client.get('/api/items/42')
        self.assertEqual(r.status_code,200);self.assertEqual(r.json,{'id':42,'name':'Field notebook'})
    def test_missing(self):self.assertEqual(self.client.get('/api/items/987654').status_code,404)
    def test_unavailable(self):self.assertEqual(self.client.get('/api/unavailable').status_code,503)
    def test_internal_error(self):self.assertEqual(self.client.get('/api/crash').status_code,500)
