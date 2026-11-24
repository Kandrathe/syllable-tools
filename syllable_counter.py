"""
Python port of the syllable counter in READABILITY TESTS (Apple II, 6502).

Two layers:
  count_syllables_6502(word)  the original routine, ported branch for branch
                              (only the $2684 bug is fixed).
  count_syllables(word)       the original plus a correction layer (CORRECTIONS,
                              OVERRIDES) for patterns it gets wrong. Pass
                              corrections=False for the original behaviour.

Original routine: $2584-$27AD, with the vowel test at $27AE.
The assembly is a heuristic: it counts vowel groups with special cases for
common English endings and vowel pairs. This port is branch-for-branch
faithful, including quirks, so results match the original exactly.
Hex addresses in comments refer to the original listing.

Original conventions:
  * Input is the word with only chars >= '0' kept (letters/digits), in
    upper case, at $02C0 with zero terminators. X = length.
  * $D5 = syllable count, $FC bit 7 = "vowel group opened, not yet counted".
"""

VOWELS = frozenset("AEIOUY")          # $27AE: Y counts as a vowel
NUL = "\0"                            # the zero terminator / "nothing there"

# What to do with a middle character (the five exits of the main loop)
CLOSE, NORMAL, EXTRA, SKIP = "close", "normal", "extra", "skip"


def is_vowel(c: str) -> bool:
    return c in VOWELS


def _clean(word: str) -> list[str]:
    # The tokenizer ($27C5) only admits 0-9 and A-Z; the copy loop at $22C5
    # drops anything below '0' (this is what removes a leading '#').
    return [c for c in word.upper() if c.isascii() and c.isalnum()]


def count_syllables_6502(word: str) -> int:
    """Faithful port of the original routine (with the $2684 bug fixed)."""
    w = _clean(word)
    L = len(w)

    def ch(i: int) -> str:
        """Character at index i, or NUL if outside the word."""
        return w[i] if 0 <= i < L else NUL

    # ---- $258A: words shorter than 3 letters get 1 syllable ($27A9) ------
    if L < 3:
        return 1

    count = 0          # $D5
    pending = is_vowel(w[0])   # $258E-$2596: word starting with a vowel

    def classify(y: int) -> str:
        """The vowel/consonant decision for the middle character at index y."""
        c = ch(y)
        nxt, prv = ch(y + 1), ch(y - 1)

        if not is_vowel(c):                       # $25A2: consonant
            return CLOSE

        if c == "E":                              # $25D8
            if ch(y + 2) == NUL or y == 1:
                return NORMAL
            if is_vowel(prv) or is_vowel(nxt):
                return NORMAL
            pp = ch(y - 2)
            if pp == "E" or not is_vowel(pp):
                return NORMAL
            t = ch(y + 2)
            if not is_vowel(t):                   # $2637
                if t != "H":
                    return NORMAL
                a = ch(y + 4)
                return NORMAL if a in (NUL, "R") else SKIP
            if nxt == "R" or prv == "W":          # $2605-$260F
                return NORMAL
            a3 = ch(y + 3)
            if a3 == "R":
                return NORMAL
            if a3 == NUL and nxt == "E":          # $261C (unreachable in practice)
                return NORMAL
            return SKIP                           # silent E, $2628

        if c == "I":                              # $2649
            if is_vowel(nxt):
                if nxt == "E":                    # $2655
                    if ch(y + 2) == NUL or y == 1:
                        return SKIP
                    return EXTRA if ch(y + 2) == "R" else SKIP
                if prv in ("S", "T", "C"):        # $2667: -tion, -sion, -cial
                    return SKIP
                return EXTRA
            if nxt != "N":                        # $2678
                return NORMAL
            if not is_vowel(prv):
                return NORMAL
            # FIXED: the original at $2684 is LDA $02C2 (absolute, i.e. w[2])
            # where LDA $02C2,Y (w[y+2]) was clearly intended, so its "-ing"
            # test looked at the wrong letter. Here we check the letter two
            # ahead of the I, as intended.
            if ch(y + 2) != "G":
                return NORMAL
            if prv == "I":
                return NORMAL
            if y == 1:
                return EXTRA
            return NORMAL if is_vowel(ch(y - 2)) else EXTRA

        if c == "U":                              # $26A2
            if nxt != "A":
                return NORMAL
            if prv in ("G", "Q"):                 # guard, quad
                return SKIP
            return EXTRA

        if c == "Y":                              # $25C2
            if L < 4:
                return SKIP
            if not is_vowel(nxt):
                return NORMAL
            if not is_vowel(prv):
                return EXTRA
            return CLOSE                          # between vowels: consonant

        return NORMAL                             # A, O

    # ---- main loop $2599-$26BE: chars 1 .. L-2 ----------------------------
    y = 1
    while True:
        action = classify(y)
        if action == CLOSE:                       # $25A2
            if pending:
                count += 1
                pending = False
        elif action == EXTRA:                     # $26B4
            count += 1
            pending = True
        elif action == NORMAL:                    # $26B6
            pending = True
        # SKIP ($26B9): nothing
        if ch(y + 2) == NUL:                      # $26B9: stop when 2 ahead is end
            break
        y += 1

    # ---- end-of-word rules $26C1-$27AD ------------------------------------
    last, l2, l3, l4 = ch(L - 1), ch(L - 2), ch(L - 3), ch(L - 4)
    at_least_one = count or 1                     # $27A9
    plus_one = count + 1                          # $27A5
    final_pending = plus_one if pending else at_least_one   # $27A1

    if is_vowel(last):
        if last == "E":                           # $26C9
            if is_vowel(l2):
                return plus_one                   # -ee, -ie, -ue ...
            if l2 not in ("L", "R"):
                return at_least_one               # silent final E
            if l3 == "L" or is_vowel(l3):
                return at_least_one
            return plus_one                       # -ble, -tre ...
        count += 1                                # $26EC: close last vowel group
        if l2 != "E":
            return count
        if L == 3:
            return count or 1
        return count + 1 if last in ("A", "O") else count   # -ea, -eo

    if last == "D":                               # $272E
        if l2 != "E":
            return final_pending
        if l3 in ("D", "T") or is_vowel(l3):
            return plus_one                       # -ded, -ted, -Ved
        return at_least_one

    if last == "S":                               # $2748
        if l2 != "E":
            return final_pending
        if is_vowel(l3) or l3 in ("S", "C", "Z"):
            return plus_one                       # -ses, -ces, -zes, -Ves
        if L < 4:
            return at_least_one
        if l3 == "G":
            return plus_one if l4 == "N" else at_least_one
        if l3 == "H":
            return plus_one if l4 == "S" else at_least_one
        if l3 == "R":
            return at_least_one if is_vowel(l4) else plus_one
        if l3 == "L":
            if is_vowel(l4) or l4 == "L":
                return at_least_one
            return plus_one
        return at_least_one

    if last == "T":                               # $2711
        if l2 == "S":
            if l3 != "E" or L < 7:
                return at_least_one
            return plus_one if l4 == "I" else at_least_one   # -iest
        return final_pending

    return final_pending                          # any other consonant, $27A1


# ===========================================================================
# Correction layer (not in the original program)
# ===========================================================================
# Each rule adds or subtracts one syllable from the original routine's answer.
# Rules were chosen by measuring against the CMU Pronouncing Dictionary on the
# 25,000 most common English words (tuned on half, confirmed on the other
# half). The first matching rule wins. Patterns are upper-case regexes.
import re

CORRECTIONS = [
    # (description, pattern, delta)
    ("-ism/-asm: the M is its own syllable",    r"[AEIOUY]SMS?$",                       +1),
    ("-ges: syllabic ES (-nges already ok)",    r"(?<!N)GES$",                          +1),
    ("-ches: syllabic ES",                      r"CHES$",                               +1),
    ("-xes: syllabic ES",                       r"XES$",                                +1),
    ("-ying after a consonant (drying)",        r"[^AEIOU]YING$",                       -1),
    ("-yed after a vowel (played)",             r"[AEIOU]YED$",                         -1),
    ("silent -que/-gue (league, unique)",       r"^(?!.*(ARGU|CONTINU)).*[QG]UES?$",    -1),
    ("-tled (whistled)",                        r"TLED$",                               +1),
    ("consonant+L/R+ED (tumbled, hundred)",     r".[^AEIOULR][LR]ED$",                   +1),
    ("Mc- prefix is a syllable",                r"^MC",                                 +1),
    ("creat- (create)",                         r"^CREAT(?!UR)",                              +1),
    ("react-",                                  r".EACT",                               +1),
    ("realiz-/realit-",                         r"^REALI[TZ]",                          +1),
    ("-eo- hiatus (video); not people/george",  r"^(?!.*(PEOP|LEOP|JEOP|GEOR|MEO|EOU|GEON|EOV|EOF|LEON)).+EO.+$", +1),
    ("-iet- hiatus (society, quiet)",           r".IET",                                +1),
    ("-ciat- (association)",                    r".CIAT",                               +1),
    ("-ience/-uence (science, influence)",      r"^(?!.*(TIENCE|QUENCE|NIENCE|CONSCIENCE)).*[IU]ENCES?$", +1),
    ("-nio-/-gio-/-lio- one syllable (union)",  r"^(?!.*(ONIO|OLIO|REUNI|BIBLIO)).+(NIO|GIO|LIO)",                      -1),
    ("every- compounds (everything)",           r"^EVERY",                              -1),
]
_COMPILED = [(d, re.compile(p), delta) for d, p, delta in CORRECTIONS]

# Irregular common words the rules can't express (and abbreviations that have
# no usable vowel pattern).
OVERRIDES = {
    "BUSINESS": 2, "BUSINESSES": 3, "MAYBE": 2, "SEEING": 2, "OPENING": 3,
    "OPENED": 2, "EVENING": 2, "SOMEWHERE": 2, "ELSEWHERE": 2, "THEREFORE": 2,
    "MR": 2, "MRS": 2, "DR": 2, "JR": 2, "MS": 1,
}


def count_syllables(word: str, corrections: bool = True) -> int:
    """Syllables in `word`. corrections=False gives the original routine."""
    base = count_syllables_6502(word)
    if not corrections:
        return base
    key = "".join(_clean(word))
    if key in OVERRIDES:
        return OVERRIDES[key]
    for _desc, rx, delta in _COMPILED:
        if rx.search(key):
            return max(1, base + delta)
    return base


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    original = "--original" in args
    args = [a for a in args if a != "--original"]
    words = args or ["cat", "make", "table", "wanted", "walked",
                              "idea", "changes", "happiest", "quiet", "guard"]
    for wd in words:
        print(f"{wd:12s} {count_syllables(wd, corrections=not original)}")
