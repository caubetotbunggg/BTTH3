import sys
import os
import unittest

# Thêm thư mục gốc vào sys.path để import chunker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chunker import chunk_by_chapter_and_article

class TestChunker(unittest.TestCase):
    def test_split_with_khoan(self):
        text = (
            "CHƯƠNG I\n"
            "Điều 1. Quy định chung\n"
            "1. Khoản một của Điều 1\n"
            "2. Khoản hai của Điều 1\n"
            "Điều 2. Quy định riêng\n"
            "1. Khoản một của Điều 2\n"
            "2. Khoản hai của Điều 2\n"
        )
        chunks = chunk_by_chapter_and_article(text)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]['tieu_de'], "Điều 1. Quy định chung")
        self.assertEqual(len(chunks[0]['khoan']), 2)
        self.assertEqual(chunks[0]['khoan'][0]['khoan'], "1.")
        self.assertEqual(chunks[0]['khoan'][1]['noi_dung'], "Khoản hai của Điều 1")
        self.assertEqual(chunks[1]['tieu_de'], "Điều 2. Quy định riêng")
        self.assertEqual(len(chunks[1]['khoan']), 2)

    def test_split_no_khoan(self):
        text = (
            "CHƯƠNG I\n"
            "Điều 1. Điều không có khoản\n"
            "Nội dung điều không có khoản\n"
            "Điều 2. Điều có khoản\n"
            "1. Khoản một\n"
            "2. Khoản hai\n"
        )
        chunks = chunk_by_chapter_and_article(text)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]['tieu_de'], "Điều 1. Điều không có khoản")
        self.assertIsNone(chunks[0]['khoan'])
        self.assertEqual(chunks[0]['noi_dung'], "Nội dung điều không có khoản")
        self.assertEqual(len(chunks[1]['khoan']), 2)
        self.assertEqual(chunks[1]['khoan'][0]['noi_dung'], "Khoản một")

if __name__ == "__main__":
    unittest.main()