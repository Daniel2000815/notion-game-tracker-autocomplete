import unittest
from notion_gametracker.igdb import Game, search_game_by_title, search_game_by_id, list_games_by_title
from notion_gametracker.status import StatusCode

class TestGameMethods(unittest.TestCase):
    def test_list_games(self):
        search_cases = [
            ("Super Mario Galaxy", "Wii"),
            ("Coral Island", ""),
            ("Hero's Hour", "Nintendo Switch")
        ]
        
        for title, platform in search_cases:
            print(f"Listing {title}")
            with self.subTest(title=title, platform=platform):
                games = list_games_by_title(title, platform_wanted=platform)
                print(f"Games found for {title}:\n{games}\n")
                self.assertGreater(len(games), 0)

    def test_search_by_name_id(self):
        search_cases = [
            ("Super Mario Galaxy", "Wii", 1077),
            ("Coral Island", "", 143061),
            ("Hero's Hour", "Nintendo Switch", 295685)
        ]
        
        for title, platform, expected_igdb_id in search_cases:
            print(f"Searching {title} by name")
            with self.subTest(title=title, platform=platform):
                game = search_game_by_title(title, platform_wanted=platform, list_all=False)
                self.assertEqual(game.title, title, f"Got game {game}")
                self.assertEqual(game.igdbId, expected_igdb_id, f"Got game {game}")

            print(f"Searching {title} by id")
            with self.subTest(id=expected_igdb_id):
                game = search_game_by_id(expected_igdb_id)
                self.assertEqual(game.title, title, f"Got game {game}")
                self.assertEqual(game.igdbId, expected_igdb_id, f"Got game {game}")

if __name__ == '__main__':
    unittest.main()