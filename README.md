# nhk-study

Turns NHK Easy News stories into printable Japanese study sheets and a
[Renshuu](https://www.renshuu.org)-ready vocabulary list.

**Live study sheets:** <https://schneider128k.github.io/japanese/>

---

## Daily workflow

1. Find an article on [NHK Easy News](https://www3.nhk.or.jp/news/easy/).
2. Paste the full Japanese text and the article URL to Claude Code with the
   prompt: *"Add this NHK Easy story to the repo."*  Claude generates
   `stories/YYYY-MM-DD-<slug>/study.md` following the format in `SPEC.md`.
3. Run `make` to rebuild all HTML sheets.
4. Open `build/all.html` in a browser → **Print → Save as PDF** to get a
   printable packet of everything studied so far.
5. Copy the vocab block from the new `study.md` into Renshuu's term search
   to add new words to your SRS deck.

---

## Printing a single story

Open `stories/YYYY-MM-DD-<slug>/study.html` in a browser and print, or use
the GitHub Pages link above. The **フリガナ 表示/非表示** button at the
top-right toggles furigana on/off — hide it for self-testing before printing.

---

## Build

```
pip install markdown
make          # rebuilds all study.html + build/all.html
make clean    # removes generated HTML
```

Config flags live at the top of `build.py`:

| Flag | Default | Effect |
|------|---------|--------|
| `PRACTICE_LINES` | `True` | Emit handwriting lines under each sentence |
| `PRACTICE_STYLE` | `"ruled"` | `"ruled"` = lines · `"grid"` = genkō-yōshi squares |
| `READING_SCRIPT` | `"kana"` | Readings in hiragana/katakana (no romaji) |

---

## Repo layout

```
nhk-study/
├── assets/print.css                    # print stylesheet
├── build/all.html                      # all sheets concatenated (print everything)
├── stories/
│   └── YYYY-MM-DD-<slug>/
│       ├── study.md                    # source of truth (furigana + breakdown)
│       └── study.html                  # generated printable sheet
├── renshuu-queue.txt                   # running vocab list for Renshuu
├── build.py                            # Markdown → HTML renderer
├── Makefile
└── SPEC.md                             # full format contract
```

Grammar is handled separately with Genki (3rd ed.) and Renshuu's prebuilt
Genki vocab lists — this repo is purely for NHK Easy news comprehension and
vocabulary mining.
