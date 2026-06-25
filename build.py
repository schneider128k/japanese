#!/usr/bin/env python3
"""
Renders every stories/**/study.md → study.html and build/all.html.

Usage:
    pip install markdown
    python build.py

Config flags (edit the block below):
    PRACTICE_LINES  – emit handwriting lines for each phrase and full sentence
    PRACTICE_STYLE  – "ruled" (lines) | "grid" (genkō-yōshi squares)
    WRITE_REPS      – how many write-line rows to insert after each table row
    SENTENCE_REPS   – how many full-sentence write lines at end of each block
"""
import os, re, glob
import markdown

# ── Config ────────────────────────────────────────────────────────────────────
PRACTICE_LINES = True
PRACTICE_STYLE = "ruled"   # "ruled" | "grid"
WRITE_REPS     = 1         # write-line rows per phrase in the parse table
SENTENCE_REPS  = 2         # full-sentence write lines per sentence block

MD_EXTS = ["tables", "md_in_html", "extra"]

CSS_STORY = "../../assets/print.css"
CSS_ALL   = "../assets/print.css"

FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP'
    ':wght@400;700&display=swap" rel="stylesheet">'
)

PRINT_BTN = '<button id="print-btn" onclick="window.print()">印刷</button>'
TOGGLE_BTN = (
    '<button id="furigana-toggle" '
    "onclick=\"document.body.classList.toggle('is-no-ruby')\">"
    "フリガナ　表示/非表示</button>"
)


# ── Markdown pre-processing ───────────────────────────────────────────────────

def _sentence_wrappers(text: str) -> str:
    """Wrap ### Sentence N blocks in <div class="sentence"> … </div>."""
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

    return header + "\n\n".join(wrapped) + ("\n\n---\n\n" + footer if footer else "")


def _preprocess(text: str) -> str:
    # Remove write divs from source — build.py injects them after the table
    text = re.sub(r'\n<div class="write[^"]*"></div>\n?', '', text)
    return _sentence_wrappers(text)


# ── HTML post-processing ──────────────────────────────────────────────────────

WRITE_ROW = '<tr class="write-line"><td colspan="3"></td></tr>'

def _write_lines(n: int) -> str:
    return "\n".join(WRITE_ROW for _ in range(n))

def _sentence_write_block(n: int, style: str) -> str:
    cls = "write grid" if style == "grid" else "write"
    lines = "\n".join(f'  <div class="{cls}"></div>' for _ in range(n))
    return f'<div class="sentence-write">\n{lines}\n</div>'


def _enhance_html(html: str) -> str:
    """
    Post-process converted Markdown HTML:
      1. Strip "EN —" / "EN – " prefix from translation paragraphs → class="translation"
      2. Add class="part" to tbody <tr> rows; insert write-line rows after each
      3. Inject .sentence-write block after each </table> inside .sentence
    """
    # 0. Strip sentence number headings (keep .sentence div structure, lose the label)
    html = re.sub(r'<h3>[^<]*Sentence\s+\d+[^<]*</h3>\s*\n?', '', html)

    # 1. Translation label
    html = re.sub(
        r'<p><strong>EN\s*[—–\-]+\s*</strong>\s*',
        '<p class="translation">',
        html,
    )

    if not PRACTICE_LINES:
        return html

    # 2. Per-phrase write-line rows in tables
    def _augment_tbody(m: re.Match) -> str:
        tbody = m.group(1)
        # Mark each <tr> as a part row
        tbody = tbody.replace('<tr>', '<tr class="part">')
        # After each </tr> insert write-line rows
        tbody = re.sub(
            r'(</tr>)',
            r'\1\n' + _write_lines(WRITE_REPS),
            tbody,
        )
        return f'<tbody>{tbody}</tbody>'

    html = re.sub(r'<tbody>(.*?)</tbody>', _augment_tbody, html, flags=re.DOTALL)

    # 3. Full-sentence practice block after each </table> within a .sentence div
    write_block = _sentence_write_block(SENTENCE_REPS, PRACTICE_STYLE)
    # Insert after the closing </table> that follows a .sentence opening
    # We do this by finding </table> and appending the block; it only appears
    # inside .sentence divs in our generated HTML.
    html = html.replace('</table>', f'</table>\n{write_block}')

    return html


# ── HTML assembly ─────────────────────────────────────────────────────────────

_JISHO_SCRIPT = """\
<script>
document.addEventListener('DOMContentLoaded', function () {
  var base = 'https://jisho.org/search/';
  document.querySelectorAll('tbody tr.part td:first-child').forEach(function (td) {
    var word = td.textContent.trim();
    td.title = word + ' — Jisho で調べる';
    td.addEventListener('click', function () {
      window.open(base + encodeURIComponent(word), '_blank');
    });
  });
  document.querySelectorAll('pre').forEach(function (pre) {
    var lines = pre.textContent.trim().split('\\n');
    pre.innerHTML = lines.map(function (line) {
      line = line.trim();
      if (!line) return '';
      return '<a class="vocab-link" href="' + base + encodeURIComponent(line) +
             '" target="_blank">' + line + '</a>';
    }).join('\\n');
  });
});
</script>"""

_HTML_TMPL = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>{title}</title>
{fonts}
<link rel="stylesheet" href="{css}">
</head>
<body>
{print_btn}
{toggle}
{body}
{script}
</body>
</html>"""


def _title_from_html(html: str) -> str:
    m = re.search(r'<h1>(.*?)</h1>', html, re.DOTALL)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else "Study Sheet"


def _md_to_html(text: str, css: str) -> str:
    text = _preprocess(text)
    body = markdown.markdown(text, extensions=MD_EXTS)
    body = _enhance_html(body)
    return _HTML_TMPL.format(
        title=_title_from_html(body),
        fonts=FONTS_LINK,
        css=css,
        print_btn=PRINT_BTN,
        toggle=TOGGLE_BTN,
        body=body,
        script=_JISHO_SCRIPT,
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
        raw = markdown.markdown(text, extensions=MD_EXTS)
        parts.append(_enhance_html(raw))

    separator = '\n<p style="page-break-after:always"></p>\n'
    body = separator.join(parts)
    html = _HTML_TMPL.format(
        title="All Study Sheets",
        fonts=FONTS_LINK,
        css=CSS_ALL,
        print_btn=PRINT_BTN,
        toggle=TOGGLE_BTN,
        body=body,
        script=_JISHO_SCRIPT,
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
