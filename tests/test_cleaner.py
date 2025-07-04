import os
import sys

# Thêm thư mục gốc vào sys.path để import cleaner
sys.path.append(os.path.abspath("../BTTH3"))

import unittest

from cleaner import extract_text


class TestExtractText(unittest.TestCase):

    def test_newline(self):
        html = "<div>ab \ncd</div>"
        self.assertEqual(extract_text(html), "ab \ncd")

    def test_tab(self):
        html = "<div>ab\tcd</div>"
        self.assertEqual(extract_text(html), "ab\tcd")

    def test_html_tags(self):
        html = "<div>Hello <b>world</b>!</div>"
        self.assertEqual(extract_text(html), "Hello\nworld\n!")

    def test_strip(self):
        html = "   <p>  test  </p>   "
        self.assertEqual(extract_text(html), "test")


if __name__ == "__main__":
    unittest.main()
