"""A small Markdown to HTML converter (the stdlib has none).

Covers the common subset of Markdown that notes use: ATX headings, paragraphs,
emphasis, inline code, fenced code blocks, ordered and unordered lists (nested),
block quotes, links, images, autolinks, horizontal rules and hard line breaks.
It is not a full CommonMark implementation.

Wiki-links (`[[name]]`, `[[name|label]]`) are handed to a callback so the site
builder decides what they point to.
"""

from __future__ import annotations

import html
import re
from typing import Callable, List, Optional, Tuple

# wikilink(target, label) -> HTML. `label` is None when the link has none.
WikiLinkFn = Callable[[str, Optional[str]], str]

WIKILINK_RE = re.compile(r"\[\[([^\[\]|\n]+?)(?:\|([^\[\]\n]+?))?\]\]")

_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([^`\s]*)")
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*#*[ \t]*$")
_HR_RE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
_QUOTE_RE = re.compile(r"^ {0,3}> ?(.*)$")
_LIST_RE = re.compile(r"^( *)([-*+]|\d{1,9}[.)])(?:[ \t]+(.*)|$)")


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


# ---------------------------------------------------------------------------
# Inline


def render_inline(text: str, wikilink: Optional[WikiLinkFn] = None) -> str:
    """Render inline Markdown in `text` to HTML."""
    tokens: List[str] = []

    def stash(fragment: str) -> str:
        tokens.append(fragment)
        return f"\x00{len(tokens) - 1}\x00"

    # Code spans first: nothing inside them is interpreted.
    text = re.sub(
        r"(`+)(.+?)\1",
        lambda m: stash(f"<code>{_escape(m.group(2).strip())}</code>"),
        text,
        flags=re.S,
    )
    # Backslash escapes.
    text = re.sub(
        r"\\([\\`*_{}\[\]()#+\-.!|<>~])",
        lambda m: stash(_escape(m.group(1))),
        text,
    )

    def wiki(m: re.Match) -> str:
        target, label = m.group(1).strip(), m.group(2)
        label = label.strip() if label else None
        if wikilink is None:
            return stash(_escape(label or target))
        return stash(wikilink(target, label))

    text = WIKILINK_RE.sub(wiki, text)

    # Autolinks: <https://example.com>
    text = re.sub(
        r"<((?:https?|mailto):[^\s<>]+)>",
        lambda m: stash(f'<a href="{_escape(m.group(1))}">{_escape(m.group(1))}</a>'),
        text,
    )

    link_target = r"\(\s*<?([^\s()<>]*(?:\([^\s()]*\)[^\s()<>]*)*)>?(?:\s+\"([^\"]*)\")?\s*\)"

    def image(m: re.Match) -> str:
        alt, src, title = m.group(1), m.group(2), m.group(3)
        title_attr = f' title="{_escape(title)}"' if title else ""
        return stash(f'<img src="{_escape(src)}" alt="{_escape(alt)}"{title_attr}>')

    text = re.sub(r"!\[([^\[\]]*)\]" + link_target, image, text)

    def link(m: re.Match) -> str:
        inner, href, title = m.group(1), m.group(2), m.group(3)
        title_attr = f' title="{_escape(title)}"' if title else ""
        # The label may contain emphasis or code; its stashed tokens are
        # restored at the end like everything else.
        return stash(f'<a href="{_escape(href)}"{title_attr}>') + inner + stash("</a>")

    text = re.sub(r"\[([^\[\]]+)\]" + link_target, link, text)

    text = _escape(text)

    # Emphasis: strong before em; underscores only at word boundaries.
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"\*(?=[^\s*])(.+?)(?<=[^\s*])\*", r"<em>\1</em>", text, flags=re.S)
    text = re.sub(r"(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)", r"<em>\1</em>", text, flags=re.S)
    text = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<del>\1</del>", text, flags=re.S)

    # Hard line breaks: two or more trailing spaces before a newline.
    text = re.sub(r" {2,}\n", "<br>\n", text)

    def restore(m: re.Match) -> str:
        return tokens[int(m.group(1))]

    # Stashed fragments can hold further placeholders (a link label with code
    # in it), so restore until none are left.
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", restore, text)
    return text


# ---------------------------------------------------------------------------
# Blocks


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_blank(line: str) -> bool:
    return not line.strip()


def _starts_block(line: str) -> bool:
    """True if `line` interrupts a paragraph."""
    return bool(
        _FENCE_RE.match(line)
        or _HEADING_RE.match(line)
        or _HR_RE.match(line)
        or _QUOTE_RE.match(line)
        or _LIST_RE.match(line)
    )


Block = Tuple[str, str]  # (kind, html); for "p" the html is the inner HTML


def _parse_blocks(lines: List[str], wikilink: Optional[WikiLinkFn]) -> List[Block]:
    blocks: List[Block] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue

        fence = _FENCE_RE.match(line)
        if fence:
            marker, lang = fence.group(1), fence.group(2)
            body: List[str] = []
            i += 1
            while i < n and not (
                lines[i].strip().startswith(marker[0] * len(marker))
                and set(lines[i].strip()) == {marker[0]}
            ):
                body.append(lines[i])
                i += 1
            i += 1  # closing fence (or end of input)
            cls = f' class="language-{_escape(lang)}"' if lang else ""
            code = _escape("\n".join(body))
            if body:
                code += "\n"
            blocks.append(("pre", f"<pre><code{cls}>{code}</code></pre>"))
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            content = render_inline(heading.group(2) or "", wikilink)
            blocks.append(("h", f"<h{level}>{content}</h{level}>"))
            i += 1
            continue

        if _HR_RE.match(line):
            blocks.append(("hr", "<hr>"))
            i += 1
            continue

        if _QUOTE_RE.match(line):
            quoted: List[str] = []
            while i < n and not _is_blank(lines[i]):
                m = _QUOTE_RE.match(lines[i])
                quoted.append(m.group(1) if m else lines[i])
                i += 1
            inner = _render_blocks(_parse_blocks(quoted, wikilink))
            blocks.append(("blockquote", f"<blockquote>\n{inner}\n</blockquote>"))
            continue

        if _LIST_RE.match(line):
            html_list, i = _parse_list(lines, i, wikilink)
            blocks.append(("list", html_list))
            continue

        para = [line.lstrip()]
        i += 1
        while i < n and not _is_blank(lines[i]) and not _starts_block(lines[i]):
            # Keep trailing spaces: they mark hard line breaks.
            para.append(lines[i].lstrip())
            i += 1
        para[-1] = para[-1].rstrip()
        blocks.append(("p", render_inline("\n".join(para), wikilink)))
    return blocks


def _parse_list(lines: List[str], i: int, wikilink: Optional[WikiLinkFn]) -> Tuple[str, int]:
    n = len(lines)
    first = _LIST_RE.match(lines[i])
    base = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start = int(first.group(2)[:-1]) if ordered else 1

    items: List[List[str]] = []
    loose = False
    while i < n:
        m = _LIST_RE.match(lines[i])
        if not m or len(m.group(1)) != base or m.group(2)[0].isdigit() != ordered:
            break
        content_indent = len(m.group(0)) - len(m.group(3) or "")
        if not m.group(3):
            content_indent = len(m.group(1)) + len(m.group(2)) + 1
        item = [m.group(3) or ""]
        i += 1
        while i < n:
            line = lines[i]
            if _is_blank(line):
                j = i
                while j < n and _is_blank(lines[j]):
                    j += 1
                if j < n and _indent(lines[j]) >= content_indent:
                    item.extend([""] * (j - i))
                    i = j
                    continue
                break
            if _indent(line) >= content_indent:
                item.append(line[content_indent:])
            elif _LIST_RE.match(line) and _indent(line) > base:
                # A nested list indented less than the item's content.
                item.append(line.lstrip(" "))
            elif _starts_block(line):
                break
            else:
                item.append(line.strip())  # lazy paragraph continuation
            i += 1
        items.append(item)
        # Blank lines between items make the list loose.
        j = i
        while j < n and _is_blank(lines[j]):
            j += 1
        if j > i and j < n:
            nxt = _LIST_RE.match(lines[j])
            if nxt and len(nxt.group(1)) == base and nxt.group(2)[0].isdigit() == ordered:
                loose = True
                i = j
                continue
        if any(_is_blank(x) for x in item[1:]):
            loose = True

    rendered = []
    for item in items:
        blocks = _parse_blocks(item, wikilink)
        if not loose and blocks and blocks[0][0] == "p":
            parts = [blocks[0][1]] + [b[1] for b in blocks[1:]]
            body = "\n".join(parts)
        else:
            body = _render_blocks(blocks)
            if body:
                body = f"\n{body}\n"
        rendered.append(f"<li>{body}</li>")
    tag = "ol" if ordered else "ul"
    start_attr = f' start="{start}"' if ordered and start != 1 else ""
    return f"<{tag}{start_attr}>\n" + "\n".join(rendered) + f"\n</{tag}>", i


def _render_blocks(blocks: List[Block]) -> str:
    out = []
    for kind, fragment in blocks:
        out.append(f"<p>{fragment}</p>" if kind == "p" else fragment)
    return "\n".join(out)


def render(text: str, wikilink: Optional[WikiLinkFn] = None) -> str:
    """Render a Markdown document to an HTML fragment."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.expandtabs(4) for line in text.split("\n")]
    return _render_blocks(_parse_blocks(lines, wikilink))
