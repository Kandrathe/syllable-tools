# syllable-tools

Syllable counting for song lyrics, in three pieces:

- **`syllable_counter.py`**: a Python port of the syllable counter from
  *READABILITY TESTS* (Apple II, 6502, 1979), ported branch for branch, plus an
  optional correction layer tuned against the CMU Pronouncing Dictionary.
- **`lyric_syllables.py`**: a command-line tool that counts syllables per line
  of a lyric sheet, understands `[Verse]` / `[Chorus]` section tags, and flags
  lines that don't match the rest of their section.
- **`notepadpp/lyric_syllables_npp.py`**: a Notepad++ PythonScript that shows
  the counts live in the editor margin.

## Command line

```
python lyric_syllables.py song.txt              # per-line counts
python lyric_syllables.py song.txt -w           # per-word breakdown
python lyric_syllables.py song.txt --original   # original 6502 routine only
python lyric_syllables.py song.txt --no-parens  # ignore (backing vocals)
```

Example output:

```
[Verse 1]
    7  I walked down the road tonight
    6  The stars were burning bright   <-- -1 vs 7
```

## Notepad++ (PythonScript)
> **Note:** Use PythonScript **3.x** (which bundles Python 3). The older 2.x build
> bundles Python 2.7 and fails with a SyntaxError on the type hints. Check with
> `import sys; print(sys.version)` in Plugins > Python Script > Show Console.

1. In Notepad++: Plugins > Plugins Admin > install **Python Script**.
2. Clone this repo, e.g. to `D:\dev\syllable-tools`.
3. Plugins > Python Script > New Script, name it `lyric_syllables_npp.py`, and
   paste in the contents of `notepadpp/lyric_syllables_npp.py` (or copy the
   file into the PythonScript `scripts` folder).
4. Edit `REPO_DIR` at the top of the script to your clone's folder
   (or set the `SYLLABLE_TOOLS_DIR` environment variable).
5. Run it from Plugins > Python Script > Scripts. Each lyric line gets a count
   in the left margin; off-pattern lines show the difference (e.g. `6 -1`).
   Run it again to clear. The document text is never modified.

Optional: Plugins > Python Script > Configuration > add the script to the
menu/toolbar, then bind a shortcut under Settings > Shortcut Mapper > Plugin commands.

## Tests

```
python -m unittest discover -s tests -v
```

## Credits

The original syllable routine is from *READABILITY TESTS* by R. Erickson,
A. McCarthy, E. Rantapaa and S. McCarron (Apple II, 1979). The correction layer
and the Python port are by Russell Erickson.

## License

MIT, see [LICENSE](LICENSE).
