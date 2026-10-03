# Telegram E-Commerce Sales & Lead Engine (Demo Project)

> **Project Type:** Personal open-source & engineering demo by Tuan Anh Trinh ([@tuananh4865](https://github.com/tuananh4865))  
> **Tech Stack:** Python 3.11+, python-telegram-bot v21+ (Asyncio), SQLite3, Pytest

---

## 1. Overview

This repository demonstrates an asynchronous Telegram commerce and lead capture bot built with `python-telegram-bot` v21 and SQLite. It implements a finite-state conversation flow for catalog browsing, multi-step order placement, customer phone number normalization, and administrative push notifications.

### Core Features
- **Async Conversation Flow**: State machine handling `/start`, catalog browsing, item selection, address input, and order confirmation.
- **Interactive Inline Keyboards**: Dynamic button menus for browsing categories and selecting products.
- **Phone Number Normalization**: Regex-based validator supporting Vietnamese carrier prefixes (`09x`, `08x`, `07x`, `03x`, `05x`) alongside standard input cleanup.
- **Transactional SQLite Storage**: Order records saved with ACID compliance and automatic schema initialization.
- **Admin Alert Dispatch**: Asynchronous dispatch of formatted order summaries to designated admin Telegram channels.

---

## 2. Project Structure

```text
telegram_sales_bot/
├── bot.py                     # Main bot application and event handlers
├── requirements.txt           # Python dependencies
├── tests/
│   └── test_bot.py            # Automated test suite (3 unit tests)
└── README.md                  # Technical documentation
```

---

## 3. Quickstart & Verification

```bash
# 1. Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated tests (offline, no bot token required)
python -m pytest tests/ -v

# 4. Optional: Run the bot live (requires Telegram Bot Token)
export TELEGRAM_BOT_TOKEN="your_token_from_botfather"
export ADMIN_CHAT_ID="your_telegram_id"
python bot.py
```

---

## 4. Automated Test Suite

The test suite in `tests/test_bot.py` includes 3 automated tests verifying:
- Product catalog dictionary structure and field completeness.
- Phone number normalization and regex validation for Vietnamese mobile formats.
- SQLite order creation, schema execution, and data retrieval.

---

## 5. License

MIT License &copy; 2026 Tuan Anh Trinh. Open for personal, learning, and reference use.
