# -*- coding: utf-8 -*-
"""
Notepad++ PythonScript wrapper for lyric_syllables.

Run it (Plugins > Python Script > Scripts) to show a syllable count for every
lyric line in the left margin of the current document. Lines whose count
differs from the most common count in their [Section] are marked with the
difference, e.g. "6 -1". Run it again to clear the margin.

Nothing in the document text is changed.

Setup: set REPO_DIR below (or the SYLLABLE_TOOLS_DIR environment variable)
to the folder that contains syllable_counter.py and lyric_syllables.py,
e.g. D:\\dev\\syllable-tools
"""
import os
import sys
from collections import Counter

REPO_DIR = os.environ.get("SYLLABLE_TOOLS_DIR", r"D:\dev\syllable-tools")

# Options
KEEP_PARENS = True      # False = ignore (backing vocals)
ORIGINAL_ONLY = False   # True = original 6502 routine, no correction layer
MARGIN = 1              # Notepad++ margin index used for the counts
MARGIN_WIDTH = 52       # pixels

if REPO_DIR and REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from lyric_syllables import TAG_RE, words_in, count_word  # noqa: E402


def compute(text, keep_parens=True, original=False):
    """Return one label per document line: (label, is_flagged) or None.

    Blank lines and [Section] tag lines get None. Pure Python, no Notepad++
    objects, so it can be tested outside the editor.
    """
    lines = text.split("\n")
    result = [None] * len(lines)
    section = []  # [(line_index, total), ...] for the current section

    def close_section():
        counts = [t for _, t in section if t]
        target = Counter(counts).most_common(1)[0][0] if len(counts) > 1 else None
        for idx, total in section:
            if target is not None and total != target:
                result[idx] = ("%d %+d" % (total, total - target), True)
            else:
                result[idx] = (str(total), False)
        del section[:]

    for i, raw in enumerate(lines):
        raw = raw.rstrip("\r")
        if TAG_RE.match(raw):
            close_section()
            continue
        if not raw.strip():
            continue
        total = sum(count_word(w, original) for w in words_in(raw, keep_parens))
        section.append((i, total))
    close_section()
    return result


def main():
    from Npp import editor  # only available inside Notepad++

    # Toggle: if the margin is already showing, clear it.
    if editor.getMarginWidthN(MARGIN) > 0:
        editor.marginTextClearAll()
        editor.setMarginWidthN(MARGIN, 0)
        return

    labels = compute(editor.getText(), KEEP_PARENS, ORIGINAL_ONLY)

    editor.setMarginTypeN(MARGIN, 5)  # SC_MARGIN_RTEXT: right-aligned text
    editor.setMarginWidthN(MARGIN, MARGIN_WIDTH)
    editor.marginTextClearAll()
    for line, item in enumerate(labels):
        if item is None:
            continue
        label, flagged = item
        editor.marginSetText(line, label)
        editor.marginSetStyle(line, 33)  # STYLE_LINENUMBER look


if __name__ == "__main__":
    main()
