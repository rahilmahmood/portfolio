import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / 'snapshot.py'
spec = importlib.util.spec_from_file_location('snapshot', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SnapshotTests(unittest.TestCase):
    def test_season_classification(self):
        self.assertEqual(mod.season('Mechanical Intern (Winter/Spring 2027)'), 'Winter/Spring 2027')
        self.assertEqual(mod.season('Manufacturing Intern - Summer 2027'), 'Summer 2027')
        self.assertIsNone(mod.season('Mechanical Engineer'))

    def test_us_location(self):
        self.assertTrue(mod.us('Austin, Texas'))
        self.assertTrue(mod.us('New York, New York'))
        self.assertFalse(mod.us('Toronto, Ontario'))

    def test_austin_metro(self):
        self.assertTrue(mod.austin('Hutto, Texas'))
        self.assertTrue(mod.austin('Austin, Texas'))
        self.assertFalse(mod.austin('Dallas, Texas'))

    def test_stable_fingerprint(self):
        self.assertEqual(mod.fp(['2','1','1']), mod.fp(['1','2']))

if __name__ == '__main__':
    unittest.main()
