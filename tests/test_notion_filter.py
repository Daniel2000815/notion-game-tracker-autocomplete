import unittest
import json
from notion_gametracker.notion_filter import *

class TestNotionFilter(unittest.TestCase):
    def test_id_name(self):
        test_cases = [
            (1, 100, '{"page_size": 100, "filter": {"property": "IGDB ID", "number": {"equals": 1}}}'),
            ("Test", 50, '{"page_size": 50, "filter": {"property": "Game Title", "rich_text": {"equals": "Test"}}}'),
        ]
        
        for game_id, page_size, expected_json in test_cases:
            with self.subTest(game_id=game_id, page_size=page_size):
                filter = [create_from_name_or_id(game_id)]
                filter_params = generate_params(filter, page_size)

                expected_dict = json.loads(expected_json)
                self.assertDictEqual(filter_params, expected_dict)

    def test_multiple(self):
        filter = [
            create("Game Title", "ends_with", "#"),
            create("Rating", "equals", 5),
            create("Status", "equals", "Wishlist")
        ]
        filter_params = generate_params(filter)
        expected_json = '''{
            "page_size": 25, 
            "filter": {
                "and": [
                    {"property": "Game Title", "rich_text": {"ends_with": "#"}}, 
                    {"property": "Rating", "number": {"equals": 5}}, 
                    {"property": "Status", "select": {"equals": "Wishlist"}}
                ]
            }
        }'''

        expected_dict = json.loads(expected_json)
        self.assertDictEqual(filter_params, expected_dict)

if __name__ == '__main__':
    unittest.main()