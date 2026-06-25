# NHK Easy → Study Repo — build spec

**Hand this whole file to Claude Code.** It is the contract for setting up and
running a small repo that turns NHK Easy News stories into printable study
sheets plus a Renshuu-ready vocabulary list. This file is the *spec*, not a
study sheet; the sheets it describes are what print nicely.

---

## 1. What this repo is for

Daily loop: paste an NHK Easy story → get (a) a printable per-story study sheet
(furigana, translation, sentence-by-sentence breakdown, optional handwriting
lines) and (b) a list of kanji words to paste into Renshuu, which handles the
spaced repetition. Genki (3rd ed.) is used separately for grammar and Renshuu
already has the prebuilt Genki vocab lists, so **this repo does nothing for
Genki** — no grammar section is generated.

The repo is also a permanent, greppable archive of every story studied. NHK
rotates old articles out, but that link rot is not critical: by the time a link
dies the audio has been heard many times and the vocabulary learned, and the
archived text here is the source of truth.

---

## 2. Repo layout

```
nhk-study/
├── README.md                  # short human readme (purpose + how to add a story + how to print)
├── SPEC.md                    # this file
├── assets/
│   └── print.css              # the stylesheet in §6 (verbatim)
├── stories/
│   └── YYYY-MM-DD-<slug>/
│       ├── study.md           # canonical, GitHub-readable source (format in §4)
│       └── study.html         # generated printable sheet (build output)
├── renshuu-queue.txt          # running list of lemmas to paste into Renshuu
├── build.py                   # renders study.md → study.html using assets/print.css
└── Makefile                   # `make` builds every study.html + build/all.html
```

- `<slug>` = short romaji/English tag, e.g. `ukraine-drone`.
- A `build/all.html` that concatenates all sheets lets the user **print
  everything from the repo at once** (browser → Print → Save as PDF).
- `study.html` is committed so it is printable straight from a clone with no
  build step.

**Config flags** (put at top of `build` script, documented in README):
- `PRACTICE_LINES = true` — emit handwriting lines under each sentence (see §4/§6).
- `PRACTICE_STYLE = "ruled"` — `"ruled"` (lines) or `"grid"` (genkō-yōshi-style
  squares for kanji practice).
- `READING_SCRIPT = "kana"` — readings in kana, not romaji.

---

## 3. Input from the user, per story

1. The full Japanese story text, pasted.
2. The NHK article URL and, if available, the headline. If the headline is
   missing, synthesize a short descriptive one and mark it `— working title`.

---

## 4. `study.md` format contract

Produce exactly this structure. See §7 for a full worked example.

**Header**
- H1 = headline with `<ruby>` furigana; italic English rendering on the next line.
- A metadata line: date · article ID · source link (mark the link best-effort).

**One block per sentence, in order, separated by `---`:**
1. `### Sentence N`
2. The full sentence on one line inside `<span class="jp">`, every kanji wrapped
   in `<ruby>` furigana. This single line is both the original sentence and its
   reading.
3. `**EN —** ` natural English (not word-for-word; the literal structure lives
   in the table).
4. A 3-column table `| part | reading | meaning |` segmenting the sentence into
   phrase/bunsetsu-sized chunks. **The meaning cell names each particle's role**
   (が subject, を object, は topic, に target, で means/location, の linking,
   から from/since, と quote, ので because, …).
5. If `PRACTICE_LINES`, immediately after the table emit the writing area:
   ```html
   <div class="write"></div>
   <div class="write"></div>
   ```
   (These are invisible on GitHub — its renderer strips the styling — and render
   as ruled lines or a grid in the printed `study.html`. That is expected.)

**Footer: `## Vocabulary → Renshuu`** — a fenced code block, dictionary forms
only, one per line, deduplicated. One sentence telling the user to paste it into
the Renshuu term search and pick the matching dictionary entry per line.

### Conventions
- **Furigana:** `<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>`. Always
  include the `<rp>(</rp> … <rp>)</rp>` fallback parentheses (accessibility +
  non-ruby renderers). Ruby only on kanji; leave kana/Latin bare. Number+unit
  spans with no kanji (e.g. `2000km`) get no ruby — the reading goes in the table.
- **Readings:** hiragana (katakana for katakana words). No romaji.
- **Segmentation:** fine enough that each row is one learnable chunk, not so fine
  it splits a word from its particle.

---

## 5. Vocabulary extraction → Renshuu

- Extract **content words containing at least one kanji**, in **dictionary
  (lemma) form** (surface 生まれました → 生まれる; 攻撃した → 攻撃).
- Use the orthography Renshuu's dictionary expects (kanji where normal, kana
  where the word is usually kana) so term-search matches fast.
- **Deduplicate** within the story; also append each lemma to `renshuu-queue.txt`
  under a `# YYYY-MM-DD <slug>` comment line.
- **Exclude:** particles, pronouns, bare numbers/counters (年・月・日・km as
  counts), and grammaticalized patterns (〜ことができる, 〜ようになる, 〜そうです …).
- **Proper nouns** (place/person names): excluded from the Renshuu list by
  default; they still get furigana in the sentence. Katakana names (ロシア,
  ゼレンスキー) fall out automatically since they have no kanji.
- **Basic single-kanji threshold:** trivial standalone kanji that only appear
  bound inside a name (e.g. 西 in 西シベリア) are **borderline** — default is to
  *include* them (rule = "all kanji content words"); flip to exclude here if the
  user finds the SRS cluttered. Treat this as the one tunable knob.

---

## 6. `assets/print.css`

Design: Mincho-style serif for Japanese, a book serif for English, one vermilion
accent for furigana and rules, slate for labels. `break-inside: avoid` keeps a
sentence and its writing lines together on one page.

The furigana toggle (`フリガナ 表示/非表示` button) works by toggling the class
`is-no-ruby` on `<body>`. It uses `visibility: hidden` (not `display: none`) so
the line-height space is preserved and text does not jump when toggling. On print,
hidden furigana uses `display: none` instead to reclaim vertical space.

---

## 7. Worked example — `stories/2026-06-22-ukraine-drone/study.md`

See the committed file at that path — it is the canonical reference for the
format with `PRACTICE_LINES=true`.

---

## 8. Acceptance check (run once on the example)

Build the example, open `study.html`, print to PDF, and confirm: furigana sits
above each kanji; each sentence + its writing lines stay on one page (no mid-
sentence page breaks); the vocab block paste-matches Renshuu dictionary entries
cleanly. If a class of lemmas mis-matches Renshuu, tighten the orthography rule
in §5 — that manual selection is the only hand step in the loop.
