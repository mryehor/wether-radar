import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from weather_bot import favorites


class FavoritesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.database_path_patch = patch.object(
            favorites,
            "DATABASE_PATH",
            Path(self.temp_dir.name) / "favorites.sqlite3",
        )
        self.database_path_patch.start()
        self.addCleanup(self.database_path_patch.stop)

    def test_favorites_persist_and_are_scoped_to_user(self):
        self.assertTrue(favorites.add_favorite(100, "Sumy"))
        self.assertFalse(favorites.add_favorite(100, "Sumy"))
        self.assertTrue(favorites.add_favorite(200, "Sumy"))

        first_id, city = favorites.get_favorites(100)[0]

        self.assertEqual(city, "Sumy")
        self.assertIsNone(favorites.get_favorite(200, first_id))
        self.assertEqual(favorites.get_favorites(200)[0][1], "Sumy")

    def test_user_can_remove_only_their_own_favorite(self):
        favorites.add_favorite(100, "Sumy")
        favorites.add_favorite(200, "Kyiv")
        favorite_id, _ = favorites.get_favorites(100)[0]

        self.assertFalse(favorites.remove_favorite(200, favorite_id))
        self.assertTrue(favorites.remove_favorite(100, favorite_id))
        self.assertEqual(favorites.get_favorites(100), [])


if __name__ == "__main__":
    unittest.main()
