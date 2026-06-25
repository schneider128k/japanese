#!/usr/bin/env python3
"""
Renders every stories/**/study.md → study.html and build/all.html.

Usage:
    pip install markdown
    python build.py

Config flags (edit the block below):
    PRACTICE_LINES  – emit handwriting lines under each sentence
    PRACTICE_STYLE  – "ruled" (lines) | "grid" (genkō-yōshi squares)
    READING_SCRIPT  – "kana" only (romaji not yet implemented)
"""
import os, re, glob
import markdown

# ── Config ────────────────────────────────────────────────────────────────────
PRACTICE_LINES = True
PRACTICE_STYLE = "ruled"   # "ruled" | "grid"
READING_SCRIPT = "kana"

MD_EXTS = ["tables", "md_in_html", "extra"]

CSS_STORY = "../../assets/print.css"   # relative from stories/YYYY-MM-DD-slug/
CSS_ALL   = "../assets/print.css"      # relative from build/

TOGGLE_BTN = (
    '<button id="furigana-toggle" '
    "onclick=\"document.body.classList.toggle('is-no-ruby')\">"
    "フリガナ　表示/非表示</button>"
)


# ── Markdown pre-processing ───────────────────────────────────────────────────

def _add_sentence_wrappers(text: str) -> str:
    """
    Wrap ### Sentence N blocks in <div class="sentence"> … </div>.
    Splits on '\\n---\\n' between sentences; rebuilds without the bare <hr>.
    """
    first = re.search(r'^###\s+Sentence\s+1\b', text, re.MULTILINE)
    if not first:
        return text

    vocab = re.search(r'^##\s+Vocabulary', text, re.MULTILINE)

    header = text[: first.start()]
    body   = text[first.start() : (vocab.start() if vocab else len(text))]
    footer = text[vocab.start() :] if vocab else ""

    blocks = re.split(r'\n---\n', body)
    wrapped = []
    for blk in blocks:
        blk = blk.strip()
        if not blk:
            continue
        if re.match(r'###\s+Sentence\s+\d+', blk):
            wrapped.append(
                f'<div class="sentence" markdown="1">\n\n{blk}\n\n</div>'
            )
        else:
            wrapped.append(blk)

    middle = "\n\n".join(wrapped)
    return header + middle + ("\n\n---\n\n" + footer if footer else "")


def _preprocess(text: str) -> str:
    if not PRACTICE_LINES:
        text = re.sub(r'\n<div class="write[^"]*"></div>', '', text)
    if PRACTICE_STYLE == "grid":
        text = text.replace('<div class="write">', '<div class="write grid">')
    return _add_sentence_wrappers(text)


# ── HTML assembly ─────────────────────────────────────────────────────────────

_HTML_TMPL = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>{title}</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
{toggle}
{body}
</body>
</html>"""


def _title_from_html(html: str) -> str:
    m = re.search(r'<h1>(.*?)</h1>', html, re.DOTALL)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else "Study Sheet"


def _md_to_html(text: str, css: str) -> str:
    text = _preprocess(text)
    body = markdown.markdown(text, extensions=MD_EXTS)
    return _HTML_TMPL.format(
        title=_title_from_html(body),
        css=css,
        toggle=TOGGLE_BTN,
        body=body,
    )


# ── Build targets ─────────────────────────────────────────────────────────────

def build_story(story_dir: str) -> None:
    md_path   = os.path.join(story_dir, "study.md")
    html_path = os.path.join(story_dir, "study.html")
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    html = _md_to_html(text, CSS_STORY)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ {html_path}")


def build_all(story_dirs: list) -> None:
    parts = []
    for d in story_dirs:
        md_path = os.path.join(d, "study.md")
        if not os.path.exists(md_path):
            continue
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
        text = _preprocess(text)
        parts.append(markdown.markdown(text, extensions=MD_EXTS))

    separator = '\n<p style="page-break-after:always"></p>\n'
    body = separator.join(parts)
    html = _HTML_TMPL.format(
        title="All Study Sheets",
        css=CSS_ALL,
        toggle=TOGGLE_BTN,
        body=body,
    )
    os.makedirs("build", exist_ok=True)
    out = "build/all.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ {out}")


def main() -> None:
    story_dirs = sorted(
        d for d in glob.glob("stories/*/*")
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "study.md"))
    )
    if not story_dirs:
        print("No story directories found under stories/")
        return
    for d in story_dirs:
        build_story(d)
    build_all(story_dirs)


if __name__ == "__main__":
    main()
