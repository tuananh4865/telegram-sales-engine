#!/usr/bin/env python3
"""
Test-Harness Interactive Conversation Simulator for Hermes Telegram Sales Bot
=============================================================================
This script exercises the genuine ordering state machine and database storage 
from bot.py without requiring active Telegram API credentials or tokens.

Invokes genuine async handlers from bot.py:
- start_command
- handle_callback_navigation (catalog category & product detail)
- start_buy_flow
- handle_quantity_choice
- handle_name_input
- handle_phone_input
- handle_address_input
- handle_final_confirmation

Generates:
- Real-time terminal dialogue demonstration
- demo/transcript.txt recording exact input/output sequence
- Verifiable SQLite database record in sales_bot.db
"""

import sys
import os
import asyncio
from pathlib import Path

# Add root directory to sys.path to import bot
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from bot import (
    start_command,
    handle_callback_navigation,
    start_buy_flow,
    handle_quantity_choice,
    handle_name_input,
    handle_phone_input,
    handle_address_input,
    handle_final_confirmation,
    PRODUCTS,
    normalize_phone,
    init_db
)

transcript_lines = []

def log(line: str = ""):
    print(line)
    transcript_lines.append(line)

class MockUser:
    def __init__(self, user_id=12345678, first_name="Khách Hàng Mẫu", username="demouser"):
        self.id = user_id
        self.first_name = first_name
        self.username = username

class MockMessage:
    def __init__(self, text="", contact=None, from_user=None):
        self.text = text
        self.contact = contact
        self.from_user = from_user or MockUser()

    async def reply_text(self, text, reply_markup=None, parse_mode=None):
        lines = text.strip().splitlines()
        for idx, l in enumerate(lines):
            prefix = "[14:20:00] [BOT]  <- " if idx == 0 else "                   "
            log(f"{prefix}{l}")
        return self

    async def edit_text(self, text, reply_markup=None, parse_mode=None):
        lines = text.strip().splitlines()
        for idx, l in enumerate(lines):
            prefix = "[14:20:00] [BOT]  <- " if idx == 0 else "                   "
            log(f"{prefix}{l}")
        return self

class MockCallbackQuery:
    def __init__(self, data, from_user=None):
        self.data = data
        self.from_user = from_user or MockUser()
        self.message = MockMessage(from_user=self.from_user)

    async def answer(self):
        pass

class MockUpdate:
    def __init__(self, message=None, callback_query=None, effective_user=None):
        self.message = message
        self.callback_query = callback_query
        self.effective_user = effective_user or (message.from_user if message else callback_query.from_user if callback_query else MockUser())

class MockContext:
    def __init__(self):
        self.user_data = {}

async def run_harness():
    log("=" * 74)
    log("  HERMES TELEGRAM SALES BOT — TEST-HARNESS CONVERSATION")
    log("  Notice: Test-harness conversation, no live Telegram")
    log("=" * 74)
    log()

    init_db()
    user = MockUser()
    context = MockContext()

    # Step 1: User issues /start
    log("[14:20:01] [USER] -> /start")
    up1 = MockUpdate(message=MockMessage(text="/start", from_user=user))
    await start_command(up1, context)
    log("                   [ 🏸 Vợt Cầu Lông ]  [ 👟 Giày & Trang Phục ]")
    log("                   [ 🎒 Phụ Kiện      ]  [ 📦 Tra Cứu Đơn Hàng   ]")
    log()

    # Step 2: User browses catalog and chooses category
    log("[14:20:08] [USER] -> Chọn '🏸 Vợt Cầu Lông'")
    up2 = MockUpdate(callback_query=MockCallbackQuery("cat_Vợt Cầu Lông", from_user=user))
    await handle_callback_navigation(up2, context)
    log()

    # Step 3: User views product detail: P01
    log("[14:20:10] [USER] -> Chọn 'P01: Vợt Carbon Pro 4U'")
    up3 = MockUpdate(callback_query=MockCallbackQuery("prod_P01", from_user=user))
    await handle_callback_navigation(up3, context)
    log()

    # Step 4: User clicks buy: buy_P01
    log("[14:20:15] [USER] -> Nhấn [ 🛒 Đặt Mua Ngay ]")
    up4 = MockUpdate(callback_query=MockCallbackQuery("buy_P01", from_user=user))
    await start_buy_flow(up4, context)
    log()

    # Step 5: Quantity choice: qty_1
    log("[14:20:18] [USER] -> Chọn số lượng: 1")
    up5 = MockUpdate(callback_query=MockCallbackQuery("qty_1", from_user=user))
    await handle_quantity_choice(up5, context)
    log()

    # Step 6: Customer Name
    customer_name = "Khách Hàng Mẫu"
    log(f"[14:20:25] [USER] -> {customer_name}")
    up6 = MockUpdate(message=MockMessage(text=customer_name, from_user=user))
    await handle_name_input(up6, context)
    log()

    # Step 7: Phone validation & normalization
    raw_phone = "0900 000 000"
    log(f"[14:20:31] [USER] -> {raw_phone}")
    up7 = MockUpdate(message=MockMessage(text=raw_phone, from_user=user))
    await handle_phone_input(up7, context)
    log()

    # Step 8: Delivery address
    address = "123 Đường Thử Nghiệm, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh"
    log(f"[14:20:40] [USER] -> {address}")
    up8 = MockUpdate(message=MockMessage(text=address, from_user=user))
    await handle_address_input(up8, context)
    log()

    # Step 9: Order confirmation and database storage
    log("[14:20:45] [USER] -> Nhấn [ ✅ Xác Nhận Đặt Hàng ]")
    up9 = MockUpdate(callback_query=MockCallbackQuery("confirm_final_order", from_user=user))
    await handle_final_confirmation(up9, context)
    log()

    log("=" * 74)
    log("  TEST-HARNESS EXECUTION COMPLETED (State Machine Handlers Executed)")
    log("=" * 74)

    # Save to demo/transcript.txt
    transcript_path = ROOT_DIR / "demo" / "transcript.txt"
    transcript_path.write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")
    print(f"\nTranscript written successfully to: {transcript_path}")

def main():
    asyncio.run(run_harness())

if __name__ == "__main__":
    main()
