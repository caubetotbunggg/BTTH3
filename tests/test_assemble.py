import os
import json
import unittest

class TestAssembleDataset(unittest.TestCase):
    def test_all_chunks_json_is_list(self):
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "processed", "all_chunks.json"
        )
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "Danh sách chunk phải có ít nhất 1 phần tử")

    def test_sample_chunk_fields(self):
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "processed", "all_chunks.json"
        )
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sample = data[0]
        self.assertIn("chuong", sample)
        self.assertIn("tieu_de", sample)
        self.assertIn("noi_dung", sample)
        self.assertIn("khoan", sample)

if __name__ == "__main__":
    unittest.main()