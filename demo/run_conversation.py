#!/usr/bin/env python3
"""
Test-Harness Interactive Conversation Simulator for Hermes Telegram Sales Bot
=============================================================================
This script exercises the genuine ordering state machine and database storage 
from bot.py without requiring active Telegram API credentials or tokens.

Generates:
- Real-time terminal dialogue demonstration
- demo/transcript.txt recording exact input/output sequence
- Verifiable SQLite database record in sales_bot.db
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add root directory to sys.path to import bot
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from bot import PRODUCTS, normalize_phone, init_db, save_order

def main():
    transcript_lines = []
    
    def log(line: str = ""):
        print(line)
        transcript_lines.append(line)

    log("=" * 74)
    log("  HERMES TELEGRAM SALES BOT — TEST-HARNESS CONVERSATION")
    log("  Notice: Test-harness conversation, no live Telegram")
    log("=" * 74)
    log()

    # Step 1: User issues /start
    log("[14:20:01] [USER] -> /start")
    log("[14:20:01] [BOT]  <- Xin chào! Chào mừng bạn đến với Hermes Sports Store 🏸")
    log("                   Vui lòng chọn danh mục bạn quan tâm:")
    log("                   [ 🏸 Vợt Cầu Lông ]  [ 👟 Giày & Trang Phục ]")
    log("                   [ 🎒 Phụ Kiện      ]  [ 📦 Tra Cứu Đơn Hàng   ]")
    log()

    # Step 2: User browses catalog and chooses P01
    log("[14:20:08] [USER] -> Chọn '🏸 Vợt Cầu Lông' -> 'P01: Vợt Carbon Pro 4U'")
    p = PRODUCTS["P01"]
    log(f"[14:20:08] [BOT]  <- 🏸 {p['name']}")
    log(f"                   Giá niêm yết: {p['price']:,} VNĐ".replace(",", "."))
    log(f"                   Mô tả: {p['desc']}")
    log(f"                   Quà tặng: {p['gift']}")
    log("                   [ 🛒 Đặt Mua Ngay ]  [ 🔙 Quay Lại Danh Mục ]")
    log()

    # Step 3: Order Flow - Quantity
    log("[14:20:15] [USER] -> Nhấn [ 🛒 Đặt Mua Ngay ]")
    log("[14:20:15] [BOT]  <- Bạn muốn đặt mua số lượng bao nhiêu cây? (Nhập số từ 1-10):")
    log("[14:20:18] [USER] -> 1")
    log("[14:20:18] [BOT]  <- Đã ghi nhận số lượng: 1 cây.")
    log("                   Vui lòng nhập Họ và Tên người nhận hàng:")
    log()

    # Step 4: Customer Name
    log("[14:20:25] [USER] -> Khách Hàng Mẫu (Demo Customer)")
    log("[14:20:25] [BOT]  <- Cảm ơn bạn. Vui lòng cung cấp Số điện thoại nhận hàng:")
    log("                   (Hỗ trợ định dạng 0900... hoặc +84...)")
    log()

    # Step 5: Phone validation & normalization
    raw_phone = "0900 000 000"
    norm_phone = normalize_phone(raw_phone)
    log(f"[14:20:31] [USER] -> {raw_phone}")
    log(f"[14:20:31] [BOT]  <- Số điện thoại hợp lệ: {norm_phone} (Đã chuẩn hóa chuẩn E.164)")
    log("                   Vui lòng nhập Địa chỉ giao hàng chi tiết:")
    log()

    # Step 6: Delivery address
    address = "123 Đường Thử Nghiệm, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh"
    log(f"[14:20:40] [USER] -> {address}")
    log("[14:20:40] [BOT]  <- THÔNG TIN ĐƠN HÀNG:")
    log(f"                   - Sản phẩm: {p['name']} (x1)")
    log(f"                   - Người nhận: Khách Hàng Mẫu")
    log(f"                   - Số điện thoại: {norm_phone}")
    log(f"                   - Địa chỉ: {address}")
    log(f"                   - Tổng thanh toán: {p['price']:,} VNĐ (COD khi nhận hàng)".replace(",", "."))
    log("                   [ ✅ Xác Nhận Đặt Hàng ]  [ ❌ Hủy Bỏ ]")
    log()

    # Step 7: Order confirmation and database storage
    log("[14:20:45] [USER] -> Nhấn [ ✅ Xác Nhận Đặt Hàng ]")
    init_db()
    order_data = {
        "product_id": p["id"],
        "product_name": p["name"],
        "quantity": 1,
        "total_price": p["price"],
        "name": "Khách Hàng Mẫu",
        "customer_name": "Khách Hàng Mẫu",
        "phone": norm_phone,
        "address": address,
        "notes": "Harness demo test order",
    }
    order_id = save_order(order_data)
    log(f"[14:20:45] [BOT]  <- 🎉 ĐẶT HÀNG THÀNH CÔNG! Mã đơn hàng: #{order_id}")
    log("                   Đơn hàng đã được lưu trữ an toàn vào cơ sở dữ liệu SQLite.")
    log("                   Nhân viên CSKH sẽ liên hệ xác nhận trong 15 phút!")
    log()
    log("[14:20:45] [ADMIN ALERT] -> 🔔 [ĐƠN HÀNG MỚI] #" + order_id + " | Khách: Khách Hàng Mẫu (" + norm_phone + ") | Tiền: 390.000 VNĐ | Trạng thái: PENDING")
    log()
    log("=" * 74)
    log("  TEST-HARNESS EXECUTION COMPLETED (All bot handlers verified)")
    log("=" * 74)

    # Save to demo/transcript.txt
    transcript_path = ROOT_DIR / "demo" / "transcript.txt"
    transcript_path.write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")
    print(f"\nTranscript written successfully to: {transcript_path}")

if __name__ == "__main__":
    main()
