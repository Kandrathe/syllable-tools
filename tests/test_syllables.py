import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "notepadpp"))

from syllable_counter import count_syllables  # noqa: E402
from lyric_syllables_npp import compute       # noqa: E402

KNOWN = {
    "cat": 1, "make": 1, "table": 2, "wanted": 2, "walked": 1,
    "idea": 3, "changes": 2, "happiest": 3, "quiet": 2, "guard": 1,
    "business": 2, "everything": 3, "tonight": 2, "burning": 2,
}


class WordCounts(unittest.TestCase):
    def test_known_words(self):
        for word, n in KNOWN.items():
            self.assertEqual(count_syllables(word), n, word)

    def test_original_vs_corrected(self):
        # The correction layer changes 'business' from the original routine's answer.
        self.assertEqual(count_syllables("business", corrections=True), 2)

    def test_short_words_are_one(self):
        self.assertEqual(count_syllables("I"), 1)
        self.assertEqual(count_syllables("is"), 1)


class LineLabels(unittest.TestCase):
    def test_flags_off_pattern_lines(self):
        text = ("[Verse 1]\nI walked down the road tonight\n"
                "The stars were burning bright\n"
                "We walked down the road tonight\n\n[Chorus]\nOh maybe\n")
        labels = compute(text)
        self.assertIsNone(labels[0])            # tag line
        self.assertEqual(labels[1], ("7", False))
        self.assertEqual(labels[2], ("6 -1", True))
        self.assertEqual(labels[3], ("7", False))
        self.assertIsNone(labels[4])            # blank line
        self.assertEqual(labels[6], ("3", False))  # single line: nothing to compare


if __name__ == "__main__":
    unittest.main()
