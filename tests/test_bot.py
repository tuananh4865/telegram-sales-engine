"""Automated unit test suite for Autonomous Telegram Sales & Lead Bot."""
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bot import normalize_phone, init_db, save_order

class TestTelegramBot(unittest.TestCase):
    def test_normalize_phone_valid_formats(self):
        """Verify Vietnamese phone number normalization formats properly."""
        self.assertEqual(normalize_phone("0988123456"), "0988123456")
        self.assertEqual(normalize_phone("+84988123456"), "+84988123456")
        self.assertEqual(normalize_phone("0988.123.456"), "0988123456")
        self.assertEqual(normalize_phone("0988 123 456"), "0988123456")

    def test_normalize_phone_invalid_formats(self):
        """Verify invalid or incomplete numbers return None."""
        self.assertIsNone(normalize_phone("12345"))
        self.assertIsNone(normalize_phone("abcdefghij"))
        self.assertIsNone(normalize_phone(""))

    def test_sqlite_order_persistence(self):
        """Verify order insertion into SQLite database with ACID integrity."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db = tmp.name

        try:
            with patch("bot.DB_PATH", tmp_db):
                init_db()
                order_data = {
                    "user_id": 123456,
                    "username": "test_client",
                    "product_id": "PRD-001",
                    "product_name": "Premium B2B Lead Suite",
                    "name": "Nguyen Van A",
                    "phone": "0988123456",
                    "address": "123 Le Loi, Da Nang",
                    "total_price": 1500000,
                    "quantity": 1
                }
                order_id = save_order(order_data)
                self.assertTrue(order_id.startswith("ORD"))

                # Query database to confirm persisted record
                conn = sqlite3.connect(tmp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT customer_name, phone, product_name, total_price FROM orders WHERE order_code = ?", (order_id,))
                row = cursor.fetchone()
                conn.close()

                self.assertIsNotNone(row)
                self.assertEqual(row[0], "Nguyen Van A")
                self.assertEqual(row[1], "0988123456")
                self.assertEqual(row[2], "Premium B2B Lead Suite")
                self.assertEqual(row[3], 1500000)
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)

if __name__ == "__main__":
    unittest.main()
