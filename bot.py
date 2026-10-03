#!/usr/bin/env python3
"""
Telegram Sales & Lead Capture Bot (Hermes Commerce Engine)
==========================================================
Tính năng:
- Menu danh mục sản phẩm tương tác (Inline Keyboard)
- Xem chi tiết sản phẩm, giá niêm yết, tồn kho
- Quy trình đặt hàng trực quan từng bước (State Machine / ConversationHandler)
- Thu thập & kiểm thực số điện thoại (Hỗ trợ nút chia sẻ danh bạ hoặc nhập tay)
- Lưu trữ đơn hàng & danh sách khách hàng tiềm năng vào SQLite an toàn
- Bắn thông báo (Alert) ngay lập tức về Telegram Admin khi có đơn hàng/lead mới
- Lệnh quản trị (/admin, /orders) bảo mật theo ID admin

Yêu cầu thư viện:
    pip install python-telegram-bot python-dotenv
"""

import os
import re
import json
import uuid
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Tải cấu hình biến môi trường
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
DB_PATH = os.getenv("DB_PATH", "sales_bot.db")

# Thiết lập logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Các trạng thái của hội thoại đặt hàng
STATE_CHOOSE_PRODUCT = 1
STATE_INPUT_QUANTITY = 2
STATE_INPUT_NAME = 3
STATE_INPUT_PHONE = 4
STATE_INPUT_ADDRESS = 5
STATE_CONFIRM_ORDER = 6

# Danh mục sản phẩm mẫu (Dễ dàng tùy biến hoặc đồng bộ từ Database/API)
PRODUCTS: Dict[str, Dict[str, Any]] = {
    "P01": {
        "id": "P01",
        "category": "🏸 Vợt Cầu Lông",
        "name": "Vợt Carbon Pro 4U Siêu Nhẹ (82g)",
        "price": 390000,
        "desc": "Thân carbon 24T triệt tiêu rung 95%, trợ lực cổ tay cực tốt, đập cầu cắm sân.",
        "gift": "Tặng cước BG65 căng sẵn 10.5kg + 2 quấn cán",
    },
    "P02": {
        "id": "P02",
        "category": "🏸 Vợt Cầu Lông",
        "name": "Vợt Cầu Lông Tấn Công Smash Master 3U",
        "price": 650000,
        "desc": "Nặng đầu chuyên smash uy lực, khung isometric mở rộng điểm ngọt, chống lật cổ tay.",
        "gift": "Tặng bao nhung đựng vợt + 3 quấn cán cao cấp",
    },
    "P03": {
        "id": "P03",
        "category": "👟 Giày & Trang Phục",
        "name": "Giày Cầu Lông Đế Kép Đệm Khí PowerCushion",
        "price": 550000,
        "desc": "Đế cao su tự nhiên bám sân tuyệt đối, đệm khí giảm chấn đầu gối khi bật nhảy.",
        "gift": "Tặng kèm 2 đôi tất dệt kim chuyên dụng",
    },
    "P04": {
        "id": "P04",
        "category": "🎒 Phụ Kiện Thể Thao",
        "name": "Combo 10 Quấn Cán Chống Mồ Hôi & Trơn Trượt",
        "price": 120000,
        "desc": "Chất liệu PU xốp thấm hút mồ hôi siêu tốc, bề mặt gân bám dính chắc tay.",
        "gift": "Freeship toàn quốc từ 2 combo",
    },
    "P05": {
        "id": "P05",
        "category": "🎒 Phụ Kiện Thể Thao",
        "name": "Túi Đựng Vợt 2 Ngăn Chống Thấm Cách Nhiệt",
        "price": 280000,
        "desc": "Chứa được 4-6 cây vợt, có ngăn riêng để giày có lỗ thoáng khí khử mùi.",
        "gift": "Tặng 1 móc khóa cầu lông cute",
    },
}


# ==========================================
# KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
def init_db():
    """Khởi tạo cấu trúc bảng lưu trữ đơn hàng và leads."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Bảng đơn hàng
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT UNIQUE,
                user_id INTEGER,
                username TEXT,
                customer_name TEXT,
                phone TEXT,
                address TEXT,
                product_id TEXT,
                product_name TEXT,
                quantity INTEGER,
                total_price INTEGER,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Bảng Leads (Khách hàng để lại thông tin quan tâm)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                phone TEXT UNIQUE,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    logger.info("Cơ sở dữ liệu SQLite đã sẵn sàng: %s", DB_PATH)


def save_order(order_data: Dict[str, Any]) -> str:
    """Lưu đơn hàng vào database và trả về mã đơn."""
    order_code = f"ORD{datetime.now().strftime('%y%m%d%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders (
                order_code, user_id, username, customer_name,
                phone, address, product_id, product_name,
                quantity, total_price, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
            """,
            (
                order_code,
                order_data.get("user_id"),
                order_data.get("username", ""),
                order_data.get("name"),
                order_data.get("phone"),
                order_data.get("address"),
                order_data.get("product_id"),
                order_data.get("product_name"),
                order_data.get("quantity", 1),
                order_data.get("total_price", 0),
            ),
        )
        # Đồng thời lưu vào danh sách Leads
        cursor.execute(
            """
            INSERT OR IGNORE INTO leads (user_id, username, phone, note)
            VALUES (?, ?, ?, ?)
            """,
            (
                order_data.get("user_id"),
                order_data.get("username", ""),
                order_data.get("phone"),
                f"Đã đặt hàng mã {order_code}",
            ),
        )
        conn.commit()
    return order_code


# ==========================================
# BỘ BÀN PHÍM TƯƠNG TÁC (KEYBOARDS)
# ==========================================
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Bàn phím danh mục chính."""
    categories = sorted(list({p["category"] for p in PRODUCTS.values()}))
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(f"📂 {cat}", callback_data=f"cat_{cat}")])
    keyboard.append([InlineKeyboardButton("📞 Hỗ Trợ Trực Tiếp / Hotline", callback_data="contact_support")])
    return InlineKeyboardMarkup(keyboard)


def get_products_keyboard(category: str) -> InlineKeyboardMarkup:
    """Bàn phím danh sách sản phẩm theo danh mục."""
    keyboard = []
    for p_id, p in PRODUCTS.items():
        if p["category"] == category:
            btn_text = f"{p['name']} - {p['price']:,}đ"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"prod_{p_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Quay lại danh mục", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(keyboard)


def get_product_detail_keyboard(product_id: str) -> InlineKeyboardMarkup:
    """Bàn phím khi xem chi tiết 1 sản phẩm."""
    keyboard = [
        [InlineKeyboardButton("🛒 ĐẶT HÀNG NGAY", callback_data=f"buy_{product_id}")],
        [
            InlineKeyboardButton("🔙 Danh mục", callback_data="back_to_categories"),
            InlineKeyboardButton("💬 Cần tư vấn thêm", callback_data="request_consult"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==========================================
# CÁC HANDLER ĐIỀU HƯỚNG CƠ BẢN
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /start khởi động bot và chào đón khách hàng."""
    user = update.effective_user
    safe_first_name = escape_markdown(user.first_name, version=1) if user and user.first_name else "bạn"
    welcome_text = (
        f"👋 Chào bạn *{safe_first_name}*!\n\n"
        "Chào mừng bạn đến với *Cửa Hàng Thể Thao Tự Động Hermes* 🏸⚡\n"
        "Chúng tôi chuyên cung cấp dụng cụ & phụ kiện cầu lông chính hãng với mức giá ưu đãi nhất.\n\n"
        "👉 *Vui lòng chọn danh mục bạn quan tâm dưới đây:*"
    )
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /help hướng dẫn sử dụng."""
    help_text = (
        "📖 **HƯỚNG DẪN MUA HÀNG TRÊN TELEGRAM**\n\n"
        "1. Chọn danh mục và sản phẩm bạn muốn mua.\n"
        "2. Bấm nút **'🛒 ĐẶT HÀNG NGAY'**.\n"
        "3. Nhập số lượng, tên người nhận, số điện thoại và địa chỉ nhận hàng.\n"
        "4. Đơn hàng sẽ được tạo và nhân viên sẽ liên hệ xác nhận trong 5-10 phút!\n\n"
        "📌 Lệnh hữu ích:\n"
        "- /start : Mở danh mục sản phẩm\n"
        "- /help : Hướng dẫn chi tiết\n"
        "- /cancel : Hủy bỏ thao tác đặt hàng hiện tại"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


# ==========================================
# XỬ LÝ SỰ KIỆN CALLBACK TỪ MENU SẢN PHẨM
# ==========================================
async def handle_callback_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý điều hướng danh mục và chi tiết sản phẩm."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_categories":
        await query.message.edit_text(
            "📂 **DANH MỤC SẢN PHẨM CÓ SẴN:**\nVui lòng chọn nhóm sản phẩm bạn cần:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    elif data.startswith("cat_"):
        cat_name = data.replace("cat_", "")
        await query.message.edit_text(
            f"🏷️ **DANH SÁCH: {cat_name}**\nBấm vào sản phẩm để xem chi tiết và ưu đãi:",
            reply_markup=get_products_keyboard(cat_name),
            parse_mode="Markdown",
        )
    elif data.startswith("prod_"):
        prod_id = data.replace("prod_", "")
        p = PRODUCTS.get(prod_id)
        if not p:
            await query.message.edit_text("❌ Không tìm thấy sản phẩm.")
            return

        detail_text = (
            f"✨ **{p['name']}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Giá ưu đãi**: `{p['price']:,} VNĐ`\n"
            f"📝 **Mô tả**: {p['desc']}\n"
            f"🎁 **Quà tặng kèm**: {p['gift']}\n"
            f"🚚 **Vận chuyển**: Giao hàng toàn quốc - Kiểm tra hàng trước khi thanh toán!\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        await query.message.edit_text(
            detail_text,
            reply_markup=get_product_detail_keyboard(prod_id),
            parse_mode="Markdown",
        )
    elif data == "contact_support":
        await query.message.edit_text(
            "📞 **HỖ TRỢ TRỰC TIẾP**\n\n"
            "Hotline / Zalo: `0988.xxx.xxx`\n"
            "Telegram CSKH: @tuananh_hermes\n"
            "Giờ làm việc: 8:00 - 22:00 tất cả các ngày trong tuần.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Về menu chính", callback_data="back_to_categories")]]
            ),
            parse_mode="Markdown",
        )
    elif data == "request_consult":
        await query.message.edit_text(
            "💬 **TƯ VẤN SẢN PHẨM TRỰC TIẾP**\n\n"
            "Chuyên viên tư vấn của shop đã sẵn sàng hỗ trợ bạn.\n"
            "• Hotline / Zalo: `0988.xxx.xxx`\n"
            "• Telegram CSKH: @tuananh_hermes\n\n"
            "Bạn có thể nhắn trực tiếp cho shop hoặc bấm về menu để xem thêm các mẫu khác.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Về menu chính", callback_data="back_to_categories")]]
            ),
            parse_mode="Markdown",
        )


# ==========================================
# QUY TRÌNH ĐẶT HÀNG (CONVERSATION HANDLER)
# ==========================================
async def start_buy_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bắt đầu luồng đặt hàng khi khách bấm 'ĐẶT HÀNG NGAY'."""
    query = update.callback_query
    await query.answer()
    prod_id = query.data.replace("buy_", "")
    product = PRODUCTS.get(prod_id)

    if not product:
        await query.message.reply_text("❌ Sản phẩm không hợp lệ.")
        return ConversationHandler.END

    context.user_data["order"] = {
        "product_id": prod_id,
        "product_name": product["name"],
        "unit_price": product["price"],
        "user_id": query.from_user.id,
        "username": query.from_user.username or query.from_user.first_name,
    }

    # Bàn phím nhanh chọn số lượng
    qty_kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("1", callback_data="qty_1"),
                InlineKeyboardButton("2", callback_data="qty_2"),
                InlineKeyboardButton("3", callback_data="qty_3"),
                InlineKeyboardButton("5", callback_data="qty_5"),
            ],
            [InlineKeyboardButton("❌ Hủy đặt hàng", callback_data="cancel_order")],
        ]
    )

    await query.message.reply_text(
        f"🛒 Bạn đang đặt mua: **{product['name']}**\n"
        f"Đơn giá: `{product['price']:,} VNĐ`\n\n"
        f"👉 **Vui lòng chọn số lượng bạn muốn đặt:**",
        reply_markup=qty_kb,
        parse_mode="Markdown",
    )
    return STATE_INPUT_QUANTITY


async def handle_quantity_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý chọn số lượng sản phẩm."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_order":
        await query.message.edit_text("Đã hủy quy trình đặt hàng. Gõ /start để quay lại menu.")
        return ConversationHandler.END

    raw = query.data.replace("qty_", "")
    if not raw.isdigit() or int(raw) <= 0:
        return STATE_INPUT_QUANTITY

    qty = int(raw)
    context.user_data["order"]["quantity"] = qty
    context.user_data["order"]["total_price"] = qty * context.user_data["order"]["unit_price"]

    await query.message.reply_text(
        f"✅ Số lượng: *{qty}* (Tạm tính: `{context.user_data['order']['total_price']:,} VNĐ`)\n\n"
        "👉 *Bước 1/3: Vui lòng nhập Tên người nhận hàng:*",
        parse_mode="Markdown",
    )
    return STATE_INPUT_NAME


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lưu họ tên khách hàng."""
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Tên quá ngắn. Vui lòng nhập đầy đủ họ tên:")
        return STATE_INPUT_NAME

    context.user_data["order"]["name"] = name
    safe_name = escape_markdown(name, version=1)

    # Cung cấp bàn phím gửi số điện thoại 1 chạm
    contact_btn = KeyboardButton("📱 Chia sẻ số điện thoại của tôi", request_contact=True)
    reply_kb = ReplyKeyboardMarkup([[contact_btn]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"Cảm ơn bạn *{safe_name}*!\n\n"
        "👉 *Bước 2/3: Cung cấp Số điện thoại nhận hàng:*\n"
        "(Bấm nút bên dưới để chia sẻ nhanh hoặc tự gõ số điện thoại)",
        reply_markup=reply_kb,
        parse_mode="Markdown",
    )
    return STATE_INPUT_PHONE


def normalize_phone(raw: str) -> Optional[str]:
    """Kiểm tra và chuẩn hóa số điện thoại di động Việt Nam."""
    cleaned = raw.strip().replace(" ", "").replace(".", "")
    if re.match(r"^(?:0|\+84)[35789][0-9]{8}$", cleaned):
        return cleaned
    return None


async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lưu và kiểm tra tính hợp lệ của số điện thoại (từ contact hoặc gõ tay)."""
    phone = None
    if update.message.contact:
        contact = update.message.contact
        sender = update.effective_user
        if contact.user_id is None or (sender and contact.user_id != sender.id):
            await update.message.reply_text(
                "⚠️ Vui lòng chia sẻ số điện thoại chính chủ của bạn hoặc tự gõ số điện thoại:"
            )
            return STATE_INPUT_PHONE
        phone = normalize_phone(contact.phone_number or "")
    elif update.message.text:
        phone = normalize_phone(update.message.text)

    if not phone:
        await update.message.reply_text(
            "⚠️ Số điện thoại không hợp lệ! Vui lòng nhập số điện thoại di động 10 số (VD: 0912345678):"
        )
        return STATE_INPUT_PHONE

    context.user_data["order"]["phone"] = phone

    await update.message.reply_text(
        f"✅ Đã nhận SĐT: `{phone}`\n\n"
        "👉 *Bước 3/3: Vui lòng nhập Địa chỉ giao hàng chi tiết:*\n"
        "(Số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành phố)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    return STATE_INPUT_ADDRESS


async def handle_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lưu địa chỉ và hiển thị xác nhận đơn hàng."""
    address = update.message.text.strip()
    if len(address) < 5:
        await update.message.reply_text("Địa chỉ quá ngắn. Vui lòng nhập chi tiết hơn để shipper giao đúng nơi:")
        return STATE_INPUT_ADDRESS

    context.user_data["order"]["address"] = address
    order = context.user_data["order"]

    confirm_kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ XÁC NHẬN ĐẶT HÀNG", callback_data="confirm_final_order"),
                InlineKeyboardButton("❌ HỦY BỎ", callback_data="cancel_final_order"),
            ]
        ]
    )

    safe_name = escape_markdown(order.get("name", ""), version=1)
    safe_address = escape_markdown(order.get("address", ""), version=1)
    safe_prod = escape_markdown(order.get("product_name", ""), version=1)

    summary_text = (
        "📋 *XÁC NHẬN THÔNG TIN ĐƠN HÀNG*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Sản phẩm*: {safe_prod}\n"
        f"🔢 *Số lượng*: {order['quantity']}\n"
        f"💵 *Tổng tiền*: `{order['total_price']:,} VNĐ`\n"
        f"👤 *Người nhận*: {safe_name}\n"
        f"📞 *Số điện thoại*: `{order['phone']}`\n"
        f"📍 *Địa chỉ*: {safe_address}\n"
        f"🚚 *Hình thức*: Nhận hàng kiểm tra thanh toán (COD)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Bạn có đồng ý đặt đơn hàng này không?"
    )

    await update.message.reply_text(summary_text, reply_markup=confirm_kb, parse_mode="Markdown")
    return STATE_CONFIRM_ORDER


async def handle_final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Chốt đơn hàng, lưu SQLite và bắn alert về Admin."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_final_order":
        await query.message.edit_text("Đơn hàng đã được hủy theo yêu cầu. Gõ /start nếu muốn mua lại.")
        context.user_data.clear()
        return ConversationHandler.END

    order_data = context.user_data.get("order")
    if not order_data:
        await query.message.edit_text("❌ Lỗi phiên làm việc. Vui lòng gõ /start để đặt lại.")
        return ConversationHandler.END

    # Lưu vào database SQLite (Idempotent retry guard)
    if "committed_code" in order_data:
        order_code = order_data["committed_code"]
    else:
        order_code = save_order(order_data)
        order_data["committed_code"] = order_code

    safe_prod = escape_markdown(order_data.get("product_name", ""), version=1)

    # Thông báo cho khách hàng
    success_text = (
        "🎉 *ĐẶT HÀNG THÀNH CÔNG!* 🎉\n\n"
        f"Mã đơn hàng: `{order_code}`\n"
        f"Sản phẩm: *{safe_prod}* (x{order_data['quantity']})\n"
        f"Tổng thanh toán: `{order_data['total_price']:,} VNĐ` (Thanh toán khi nhận hàng)\n\n"
        "📞 Chuyên viên tư vấn sẽ liên hệ với bạn trong ít phút để xác nhận và đóng gói gửi hàng.\n"
        "Cảm ơn bạn đã tin tưởng ủng hộ shop! Chúc bạn một ngày tốt lành! ❤️"
    )
    await query.message.edit_text(success_text, parse_mode="Markdown")

    # BẮN ALERT VỀ ADMIN TELEGRAM
    if ADMIN_CHAT_ID:
        safe_name = escape_markdown(order_data.get("name", ""), version=1)
        safe_username = escape_markdown(order_data.get("username", ""), version=1)
        safe_address = escape_markdown(order_data.get("address", ""), version=1)
        admin_alert = (
            "🚨 *CÓ ĐƠN HÀNG MỚI TỪ BOT!* 🚨\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *Mã đơn*: `{order_code}`\n"
            f"⏰ *Thời gian*: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"👤 *Khách hàng*: {safe_name} (@{safe_username})\n"
            f"📞 *SĐT*: `{order_data['phone']}`\n"
            f"📍 *Địa chỉ*: {safe_address}\n"
            f"📦 *Hàng*: {safe_prod}\n"
            f"🔢 *SL*: {order_data['quantity']}\n"
            f"💰 *Thu hộ (COD)*: `{order_data['total_price']:,} VNĐ`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Hãy gọi điện cho khách để xác nhận đơn ngay!"
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_alert,
                parse_mode="Markdown",
            )
            logger.info("Đã gửi alert thành công về Admin ID: %s", ADMIN_CHAT_ID)
        except Exception as e:
            logger.error("Lỗi gửi tin nhắn alert admin: %s", e)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy quá trình hội thoại bất kỳ lúc nào."""
    await update.message.reply_text(
        "Thao tác đã được hủy bỏ. Gõ /start để xem lại danh mục sản phẩm.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==========================================
# CÁC LỆNH QUẢN TRỊ DÀNH CHO ADMIN
# ==========================================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem thống kê kinh doanh dành riêng cho admin."""
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Bạn không có quyền truy cập lệnh quản trị.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_price), 0) FROM orders")
        total_orders, total_rev = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]

    stats_msg = (
        "📊 **BÁO CÁO KINH DOANH TELEGRAM BOT**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Tổng số đơn hàng: **{total_orders}**\n"
        f"💵 Doanh số tạm tính: **{total_rev:,} VNĐ**\n"
        f"👥 Tổng số Leads SĐT thu thập: **{total_leads}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Gõ /orders để xem danh sách 5 đơn hàng mới nhất."
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")


async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem 5 đơn hàng gần nhất dành riêng cho admin."""
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Bạn không có quyền truy cập.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT order_code, customer_name, phone, product_name, total_price, status, created_at
            FROM orders ORDER BY id DESC LIMIT 5
            """
        )
        rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("Chưa có đơn hàng nào trong hệ thống.")
        return

    msg = "📋 *5 ĐƠN HÀNG GẦN NHẤT:*\n\n"
    for r in rows:
        code, name, phone, prod, price, status, time = r
        safe_name = escape_markdown(name or "", version=1)
        safe_prod = escape_markdown(prod or "", version=1)
        msg += (
            f"🔹 *Mã: {code}* [{status}]\n"
            f"  Khách: {safe_name} - {phone}\n"
            f"  SP: {safe_prod} ({price:,}đ)\n"
            f"  Thời gian: {time}\n\n"
        )
    await update.message.reply_text(msg, parse_mode="Markdown")


# ==========================================
# HÀM CHÍNH KHỞI CHẠY BOT (MAIN)
# ==========================================
def main():
    """Khởi động ứng dụng bot."""
    init_db()

    if not BOT_TOKEN:
        logger.warning(
            "CẢNH BÁO: Chưa cấu hình TELEGRAM_BOT_TOKEN trong biến môi trường hoặc .env! Bot sẽ không thể kết nối."
        )
        print("Vui lòng cấu hình TELEGRAM_BOT_TOKEN trong file .env trước khi chạy!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Luồng hội thoại đặt hàng
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_buy_flow, pattern="^buy_")],
        states={
            STATE_INPUT_QUANTITY: [
                CallbackQueryHandler(handle_quantity_choice, pattern=r"^(qty_[1-9][0-9]*|cancel_order)$")
            ],
            STATE_INPUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)],
            STATE_INPUT_PHONE: [
                MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), handle_phone_input)
            ],
            STATE_INPUT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address_input)],
            STATE_CONFIRM_ORDER: [
                CallbackQueryHandler(handle_final_confirmation, pattern="^(confirm_final_order|cancel_final_order)")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_flow)],
    )

    # Đăng ký các handler
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_stats))
    app.add_handler(CommandHandler("orders", admin_orders))

    app.add_handler(order_conv)
    app.add_handler(
        CallbackQueryHandler(
            handle_callback_navigation,
            pattern="^(cat_|prod_|back_to_categories|contact_support|request_consult)",
        )
    )

    logger.info("Bot Telegram bán hàng Hermes Commerce Engine đang hoạt động...")
    print("🚀 Bot đã khởi động thành công. Nhấn Ctrl+C để dừng.")
    app.run_polling()


if __name__ == "__main__":
    main()
