import tempfile
import unittest
from pathlib import Path

from manhwateca.catalog.discovery import find_manga_folders, is_manga_folder


class CatalogDiscoveryTests(unittest.TestCase):
    def test_cover_only_folder_is_cataloged_as_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / "BC" / "Butler"
            work.mkdir(parents=True)
            (work / "cover.jpeg").touch()

            self.assertTrue(is_manga_folder(work))
            self.assertEqual([work], find_manga_folders(root))

    def test_empty_folder_is_not_cataloged(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory) / "BC" / "Empty"
            work.mkdir(parents=True)

            self.assertFalse(is_manga_folder(work))


if __name__ == "__main__":
    unittest.main()
