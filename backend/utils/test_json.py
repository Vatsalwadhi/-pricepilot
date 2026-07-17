import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID
import unittest

from .json import make_json_safe

class TestEnum(Enum):
    A = 1
    B = "hello"

class JsonSafeTests(unittest.TestCase):
    def test_decimal(self):
        self.assertEqual(make_json_safe(Decimal("10.50")), 10.5)

    def test_datetime(self):
        dt = datetime.datetime(2026, 7, 10, 14, 17, 14)
        self.assertEqual(make_json_safe(dt), "2026-07-10T14:17:14")
        
        d = datetime.date(2026, 7, 10)
        self.assertEqual(make_json_safe(d), "2026-07-10")

    def test_uuid(self):
        u = UUID("12345678123456781234567812345678")
        self.assertEqual(make_json_safe(u), "12345678-1234-5678-1234-567812345678")

    def test_enum(self):
        self.assertEqual(make_json_safe(TestEnum.A), 1)
        self.assertEqual(make_json_safe(TestEnum.B), "hello")
        
    def test_set(self):
        self.assertEqual(sorted(make_json_safe({1, 2, 3})), [1, 2, 3])

    def test_nested_dict(self):
        data = {
            "mrp": Decimal("100.00"),
            "metadata": {
                "id": UUID("12345678123456781234567812345678"),
                "tags": {"a", "b"}
            }
        }
        safe = make_json_safe(data)
        self.assertEqual(safe["mrp"], 100.0)
        self.assertEqual(safe["metadata"]["id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(sorted(safe["metadata"]["tags"]), ["a", "b"])

    def test_nested_list(self):
        data = [
            Decimal("1.5"),
            [datetime.date(2020, 1, 1)]
        ]
        safe = make_json_safe(data)
        self.assertEqual(safe, [1.5, ["2020-01-01"]])

if __name__ == "__main__":
    unittest.main()
