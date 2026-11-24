"""
Count syllables per line of a lyric sheet, using syllable_counter.py.

Usage:
  python lyric_syllables.py song.txt            # per-line counts
  python lyric_syllables.py song.txt -w         # also show per-word breakdown
  python lyric_syllables.py song.txt --original # use the original 6502 routine only
  python lyric_syllables.py song.txt --no-parens  # ignore (backing vocals)
  cat song.txt | python lyric_syllables.py      # read from stdin

Section tags like [Verse 1], [Chorus], [Bridge] (Suno style) start a new
section. Within each section, lines whose count differs from the section's
most common count are flagged so you can spot verses that won't line up.
"""
import argparse
import re
import sys
from collections import Counter

from syllable_counter import count_syllables

TAG_RE = re.compile(r"^\s*\[(.*?)\]\s*$")
WORD_RE = re.compile(r"[A-Za-z0-9']+")


def words_in(line: str, keep_parens: bool) -> list[str]:
    if not keep_parens:
        line = re.sub(r"\([^)]*\)", " ", line)
    line = line.replace("-", " ").replace("\u2019", "'")
    return [w for w in WORD_RE.findall(line) if w.strip("'")]


def count_word(word: str, original: bool) -> int:
    return count_syllables(word.replace("'", ""), corrections=not original)


def analyze(text: str, keep_parens=True, original=False):
    """Return a list of sections: (name, [(line, [(word, n), ...], total), ...])."""
    sections, name, lines = [], None, []
    for raw in text.splitlines():
        m = TAG_RE.match(raw)
        if m:
            if lines or name:
                sections.append((name, lines))
            name, lines = m.group(1), []
            continue
        if not raw.strip():
            continue
        ws = [(w, count_word(w, original)) for w in words_in(raw, keep_parens)]
        lines.append((raw.strip(), ws, sum(n for _, n in ws)))
    if lines or name:
        sections.append((name, lines))
    return sections


def report(sections, show_words=False, out=sys.stdout):
    grand = 0
    for name, lines in sections:
        if name:
            print(f"\n[{name}]", file=out)
        counts = [t for _, _, t in lines if t]
        target = Counter(counts).most_common(1)[0][0] if len(counts) > 1 else None
        width = max((len(l) for l, _, _ in lines), default=0)
        width = min(width, 60)
        for line, ws, total in lines:
            flag = ""
            if target is not None and total != target:
                d = total - target
                flag = f"   <-- {d:+d} vs {target}"
            print(f"  {total:3d}  {line[:60]:<{width}}{flag}", file=out)
            if show_words:
                print("       " + " ".join(f"{w}({n})" for w, n in ws), file=out)
            grand += total
        if counts:
            print(f"       ({len(counts)} lines, {sum(counts)} syllables, "
                  f"range {min(counts)}-{max(counts)})", file=out)
    print(f"\nTotal syllables: {grand}", file=out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="lyrics text file (default: stdin)")
    ap.add_argument("-w", "--words", action="store_true", help="show per-word counts")
    ap.add_argument("--original", action="store_true", help="original 6502 routine only")
    ap.add_argument("--no-parens", action="store_true",
                    help="ignore text in (parentheses), e.g. backing vocals")
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    report(analyze(text, keep_parens=not a.no_parens, original=a.original), a.words)


if __name__ == "__main__":
    main()
