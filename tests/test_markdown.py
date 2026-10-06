import unittest

from notes_to_site.markdown import render, render_inline


class InlineTests(unittest.TestCase):
    def test_escapes_html(self):
        self.assertEqual(render_inline("a < b & c"), "a &lt; b &amp; c")

    def test_emphasis(self):
        self.assertEqual(render_inline("**bold** and *it*"), "<strong>bold</strong> and <em>it</em>")
        self.assertEqual(render_inline("__bold__ and _it_"), "<strong>bold</strong> and <em>it</em>")

    def test_underscores_inside_words_are_literal(self):
        self.assertEqual(render_inline("snake_case_name"), "snake_case_name")

    def test_code_span_is_not_interpreted(self):
        self.assertEqual(render_inline("`*x* <y>`"), "<code>*x* &lt;y&gt;</code>")

    def test_backslash_escape(self):
        self.assertEqual(render_inline(r"\*not em\*"), "*not em*")

    def test_link(self):
        self.assertEqual(
            render_inline('[the *site*](https://example.com/a?b=1&c=2 "T")'),
            '<a href="https://example.com/a?b=1&amp;c=2" title="T">the <em>site</em></a>',
        )

    def test_image(self):
        self.assertEqual(render_inline("![a cat](cat.png)"), '<img src="cat.png" alt="a cat">')

    def test_autolink(self):
        self.assertEqual(
            render_inline("<https://example.com>"),
            '<a href="https://example.com">https://example.com</a>',
        )

    def test_strikethrough(self):
        self.assertEqual(render_inline("~~gone~~"), "<del>gone</del>")

    def test_wikilink_without_callback_is_text(self):
        self.assertEqual(render_inline("see [[Other Note|that]]"), "see that")

    def test_wikilink_callback(self):
        seen = []

        def cb(target, label):
            seen.append((target, label))
            return "<a>X</a>"

        self.assertEqual(render_inline("[[A]] and [[B | b]]"), "A and b")
        self.assertEqual(render_inline("[[A]] and [[B | b]]", cb), "<a>X</a> and <a>X</a>")
        self.assertEqual(seen, [("A", None), ("B", "b")])

    def test_wikilink_in_code_is_literal(self):
        self.assertEqual(render_inline("`[[A]]`", lambda t, l: "LINK"), "<code>[[A]]</code>")

    def test_hard_line_break(self):
        self.assertEqual(render("one  \ntwo"), "<p>one<br>\ntwo</p>")


class BlockTests(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(render("# One\n### Three ###"), "<h1>One</h1>\n<h3>Three</h3>")

    def test_hash_without_space_is_paragraph(self):
        self.assertEqual(render("#tag"), "<p>#tag</p>")

    def test_paragraphs(self):
        self.assertEqual(render("a\nb\n\nc"), "<p>a\nb</p>\n<p>c</p>")

    def test_fenced_code(self):
        self.assertEqual(
            render("```python\nx = 1 < 2\n# not a heading\n```"),
            '<pre><code class="language-python">x = 1 &lt; 2\n# not a heading\n</code></pre>',
        )

    def test_unclosed_fence_runs_to_end(self):
        self.assertEqual(render("~~~\ncode"), "<pre><code>code\n</code></pre>")

    def test_horizontal_rule(self):
        self.assertEqual(render("a\n\n---\n\nb"), "<p>a</p>\n<hr>\n<p>b</p>")
        self.assertEqual(render("* * *"), "<hr>")

    def test_blockquote(self):
        self.assertEqual(
            render("> quoted *text*\n> more"),
            "<blockquote>\n<p>quoted <em>text</em>\nmore</p>\n</blockquote>",
        )

    def test_unordered_list(self):
        self.assertEqual(render("- a\n- b"), "<ul>\n<li>a</li>\n<li>b</li>\n</ul>")

    def test_ordered_list_with_start(self):
        self.assertEqual(render("3. c\n4. d"), '<ol start="3">\n<li>c</li>\n<li>d</li>\n</ol>')

    def test_nested_list(self):
        self.assertEqual(
            render("- a\n  - a1\n  - a2\n- b"),
            "<ul>\n<li>a\n<ul>\n<li>a1</li>\n<li>a2</li>\n</ul></li>\n<li>b</li>\n</ul>",
        )

    def test_loose_list_gets_paragraphs(self):
        self.assertEqual(render("- a\n\n- b"), "<ul>\n<li>\n<p>a</p>\n</li>\n<li>\n<p>b</p>\n</li>\n</ul>")

    def test_list_item_lazy_continuation(self):
        self.assertEqual(render("- a\nstill a\n- b"), "<ul>\n<li>a\nstill a</li>\n<li>b</li>\n</ul>")

    def test_list_interrupts_paragraph(self):
        self.assertEqual(render("Intro:\n- a"), "<p>Intro:</p>\n<ul>\n<li>a</li>\n</ul>")

    def test_code_inside_list_item(self):
        self.assertEqual(
            render("- item\n\n  ```\n  code\n  ```"),
            "<ul>\n<li>\n<p>item</p>\n<pre><code>code\n</code></pre>\n</li>\n</ul>",
        )

    def test_crlf_input(self):
        self.assertEqual(render("# T\r\n\r\ntext"), "<h1>T</h1>\n<p>text</p>")

    def test_empty(self):
        self.assertEqual(render(""), "")


if __name__ == "__main__":
    unittest.main()
