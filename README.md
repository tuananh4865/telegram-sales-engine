# Gói Dịch Vụ: Telegram Sales & Lead Capture Bot Tự Động
**Đơn vị phát triển**: Hermes Automation Solutions  
**Công nghệ**: Python 3.11+, `python-telegram-bot` v21+ (Async), SQLite  
**Mục tiêu**: Tự động hóa 100% khâu tư vấn danh mục sản phẩm, chốt đơn hàng, thu thập số điện thoại khách hàng (Leads) và bắn thông báo tức thì về Telegram của chủ shop / nhân viên chốt sale.

---

## 1. Bảng Giá Dịch Vụ & Các Gói Triển Khai

| Tiêu Chí | Gói 1: Starter Bot (Cơ Bản) | Gói 2: Pro Automation (Bán Chạy) | Gói 3: Custom Enterprise (Tùy Biến) |
| :--- | :---: | :---: | :---: |
| **Giá trọn gói** | **3.000.000 VNĐ** | **5.000.000 VNĐ** | **8.000.000 VNĐ** |
| **Đối tượng phù hợp** | Shop cá nhân, người mới kinh doanh online, muốn chốt đơn Telegram nhanh | Doanh nghiệp vừa & nhỏ, shop có nhiều nhân viên trực sale, cần tích hợp thanh toán | Chuỗi cửa hàng, công ty cần kết nối đồng bộ CRM, ERP, Notion hoặc AI tư vấn |
| **Menu danh mục sản phẩm** | Menu tương tác tĩnh (Inline Keyboard phân nhóm) | Menu động kết nối cơ sở dữ liệu / Google Sheets | Menu không giới hạn, đồng bộ đa chi nhánh qua API |
| **Luồng đặt hàng & Thu SĐT** | Có (Hỗ trợ nút chia sẻ danh bạ + gõ tay + regex check) | Có (Hỗ trợ giỏ hàng đa sản phẩm, mã giảm giá) | Có (Cá nhân hóa theo lịch sử mua hàng của khách) |
| **Lưu trữ dữ liệu** | SQLite cục bộ an toàn trên VPS / máy chủ | SQLite + Tự động đồng bộ ra **Google Sheets** thời gian thực | Kết nối cơ sở dữ liệu riêng (PostgreSQL, MySQL, Lark Base, CRM) |
| **Bắn Alert về Admin** | Bắn về **01** tài khoản Admin Telegram cá nhân | Bắn về **Nhóm chat Telegram** (phân bổ cho toàn bộ nhân viên sale) | Bắn alert đa kênh (Telegram Group, Zalo ZNS, Webhook nội bộ) |
| **Thanh toán chuyển khoản** | Hướng dẫn thanh toán COD | Tự sinh mã **VietQR động** có sẵn số tiền và nội dung đơn hàng | Tích hợp cổng thanh toán trực tuyến (MoMo, PayOS, SeABank Webhook) |
| **Tích hợp Trí tuệ Nhân tạo** | Không | Không | **Tích hợp AI GPT/Claude** tự động trả lời thắc mắc sản phẩm 24/7 |
| **Bảo hành & Hỗ trợ kỹ thuật** | 1 tháng | 3 tháng | 6 tháng (Bảo trì nâng cấp tính năng) |
| **Thời gian bàn giao** | **24 Giờ** | **48 Giờ** | **3 - 5 Ngày** |

---

## 2. Tính Năng Nổi Bật Của Hệ Thống

1. **Giao diện mua sắm 1 chạm (Zero Friction)**:
   - Khách hàng không cần cài thêm app, thao tác ngay trong cửa sổ chat Telegram quen thuộc.
   - Nút bấm trực quan (Inline Buttons), chia danh mục rõ ràng (Vợt, Giày, Phụ kiện...).
2. **Thu thập Lead & SĐT chuẩn 100%**:
   - Sử dụng tính năng `request_contact` độc quyền của Telegram: Khách chỉ cần 1 chạm là gửi SĐT chính chủ mà không cần mất công gõ phím.
   - Hỗ trợ nhập tay với bộ lọc Regex kiểm tra đầu số nhà mạng Việt Nam (`09x`, `08x`, `07x`, `03x`, `05x`).
3. **Bắn thông báo đơn hàng siêu tốc (Realtime Alert)**:
   - Ngay khi khách bấm **Xác nhận đặt hàng**, điện thoại của chủ shop/nhân viên sale sẽ rung ngay lập tức với đầy đủ thông tin: Tên khách, SĐT, Địa chỉ, Danh sách món, Tổng tiền cần thu hộ (COD).
   - Tốc độ phản hồi khách chỉ tính bằng giây, tăng tỷ lệ chốt đơn lên hơn 40%.
4. **Báo cáo kinh doanh nội bộ**:
   - Chủ shop có thể dùng lệnh bí mật `/admin` và `/orders` để xem thống kê doanh thu, số đơn hàng và danh sách khách hàng tiềm năng ngay trong bot.

---

## 3. Hướng Dẫn Cài Đặt & Triển Khai (Setup Guide)

### Bước 1: Khởi tạo Bot trên Telegram
1. Mở ứng dụng Telegram, tìm kiếm bot chính thức **`@BotFather`**.
2. Gửi lệnh `/newbot`.
3. Đặt tên hiển thị cho bot (Ví dụ: `Cửa Hàng Cầu Lông Tuấn Anh`).
4. Đặt username kết thúc bằng chữ `bot` (Ví dụ: `tuananh_badminton_bot`).
5. Copy chuỗi **HTTP API Token** được cấp (dạng: `7123456789:AAFx...`).

### Bước 2: Lấy Chat ID của Quản Trị Viên
1. Mở Telegram, tìm kiếm bot **`@userinfobot`** hoặc **`@getmyid_bot`**.
2. Nhấn `/start`, bot sẽ trả về thông tin `Id: 123456789`.
3. Lưu lại dãy số này, đây chính là `ADMIN_CHAT_ID`.

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` nằm cùng thư mục với `bot.py`:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAFx_your_actual_token_here
ADMIN_CHAT_ID=123456789
DB_PATH=sales_bot.db
```

### Bước 4: Cài đặt thư viện & Khởi chạy

```bash
# 1. Di chuyển vào thư mục bot
cd outputs/monetization/packages/telegram_sales_bot

# 2. Tạo môi trường ảo Python (khuyên dùng Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# 3. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 4. Khởi chạy bot
python bot.py
```

Khi màn hình hiển thị:
```text
🚀 Bot đã khởi động thành công. Nhấn Ctrl+C để dừng.
```
Bạn đã có thể mở Telegram, tìm username bot của mình và nhấn `/start` để thử nghiệm!

---

## 4. Hướng Dẫn Vận Hành Nền 24/7 (Production Deployment)

### Cách 1: Thiết lập tự chạy trên Linux / VPS (Systemd Service)
Tạo file dịch vụ `/etc/systemd/system/telegram_bot.service`:

```ini
[Unit]
Description=Hermes Telegram Sales Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram_sales_bot
ExecStart=/opt/telegram_sales_bot/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Kích hoạt dịch vụ:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram_bot
sudo systemctl start telegram_bot
sudo systemctl status telegram_bot
```

### Cách 2: Thiết lập trên macOS (Launchd Daemon)
Tạo file `~/Library/LaunchAgents/com.hermes.telegramsaledbot.plist` trỏ vào file thực thi Python và `bot.py` để bot tự động khởi chạy cùng máy Mac.

---

## 5. Tùy Biến Sản Phẩm & Giá Bán

Toàn bộ thông tin sản phẩm được khai báo trong từ điển `PRODUCTS` ngay đầu file [bot.py](file:///Volumes/Storage-1/Hermes/outputs/monetization/packages/telegram_sales_bot/bot.py):

```python
PRODUCTS = {
    "P01": {
        "id": "P01",
        "category": "🏸 Vợt Cầu Lông",
        "name": "Tên Sản Phẩm Của Bạn",
        "price": 390000,
        "desc": "Mô tả điểm mạnh sản phẩm...",
        "gift": "Quà khuyến mãi...",
    },
    ...
}
```
*Chỉ cần chỉnh sửa danh sách này và khởi động lại bot, menu trên Telegram sẽ tự động cập nhật ngay lập tức.*

---
**Bộ phận triển khai**: Hermes Commerce Engine  
**Hỗ trợ kỹ thuật**: Liên hệ quản trị viên nội bộ `@tuananh_hermes`
