import unittest

from beecrawler import BeeCrawler

class Test_Bee_Crawler_Search(unittest.TestCase):
    def test_search_unique_username(self):
        bee = BeeCrawler()
        resp = bee.search_username('mrgustavoip')
        self.assertEqual(resp, ["16348"])
    def test_search_generic_username(self):
        bee = BeeCrawler()
        resp = bee.search_username('gustavo')
        assert len(resp) > 1
    def test_search_invalid_username(self):
        bee = BeeCrawler()
        resp = bee.search_username('gustavoipaaaa')
        self.assertEqual(resp, [])
    
class Test_Bee_Crawler_Info(unittest.TestCase):
    bee = BeeCrawler()
    resp = bee.get_info('16348')
    def test_get_info_valid_username(self):
        self.assertEqual(self.resp['username'], 'mrgustavoip')
    
    def test_get_info_valid_university(self):
        self.assertEqual(self.resp['university'], 'UTFPR')

    def test_get_info_valid_points(self):
        self.assertIsInstance(self.resp['points'], int)
    
    def test_get_info_valid_avatar(self):
        self.assertIn('https://www.gravatar.com/avatar', self.resp['avatar'])