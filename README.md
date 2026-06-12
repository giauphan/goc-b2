# Gốc.B2 — Học Tiếng Anh Cho Người Việt (Mất Gốc → A2)

Website/app học tiếng Anh dành cho người Việt mất gốc và người mới bắt đầu từ A1 tới A2 — **hiện đã dùng được ngay** trên trình duyệt và terminal.

## 🚀 Dùng ngay

```bash
# Cách 1: Mở web app trong trình duyệt
xdg-open src/web/index.html
# hoặc mở file index.html bằng browser

# Cách 2: Học trong terminal (không cần cài gì thêm)
cd ~/goc-b2
python3 study.py
```

## 📚 Nội dung

| Cấp độ | Units | Từ vựng |
|--------|-------|---------|
| 🔵 **A1** | 5 units (Family, Colors, Food, Numbers, Body) | 125 từ |
| 🟢 **A2** | 5 units (Daily Routine, Weather, Work, Shopping, Travel) | 125 từ |
| **Tổng** | **10 units** | **250 từ** |

## 🎯 Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **📖 Học flashcard** | Lật thẻ, xem IPA + ví dụ, tự chấm điểm 0-5 |
| **🧠 SM-2 SRS** | Thuật toán ghi nhớ — tự động ôn đúng lúc bạn sắp quên |
| **🎯 Quiz** | Trắc nghiệm 4 đáp án, En→Vi và Vi→En |
| **📖 Ngữ pháp** | 9 chủ đề (A1+A2), giải thích bằng tiếng Việt |
| **📊 Tiến độ** | Thống kê học tập, lưu trên localStorage |
| **📱 PWA sẵn sàng** | Chạy offline, responsive mobile |

## Cách học

```
╔══════════════════════════════════╗
║  1. Chọn unit → học flashcard   ║
║  2. Nhấn lật thẻ → xem nghĩa    ║
║  3. Tự chấm 0-5 (sao nhớ?)      ║
║  4. SM-2 tự động lên lịch ôn    ║
║  5. Quiz kiểm tra định kỳ       ║
╚══════════════════════════════════╝
```

### CLI (Terminal)

```bash
# Menu chính
python3 study.py

# Học trực tiếp một cấp độ
python3 study.py --level A1
python3 study.py --level A2

# Quiz
python3 study.py --quiz

# Thống kê
python3 study.py --stats

# Ôn tập hôm nay
python3 study.py --review
```

### Web App

Mở `src/web/index.html` trong trình duyệt:
- **Tab Học**: chọn unit → flashcard → tự chấm điểm
- **Tab Quiz**: 10 câu trắc nghiệm ngẫu nhiên
- **Tab Ngữ pháp**: 9 chủ đề giải thích bằng tiếng Việt
- **Tab Tiến độ**: xem thống kê, reset progress

## Cấu trúc thư mục

```
goc-b2/
├── study.py                  # ✅ CLI study tool (dùng được ngay)
├── src/
│   ├── srs/
│   │   ├── sm2.py            # SM-2+ algorithm
│   │   └── redis_client.py   # Upstash Redis (cho server sau này)
│   ├── content/
│   │   ├── curriculum.json   # 250 từ (A1+A2, 10 units)
│   │   └── grammar.json      # 9 chủ đề ngữ pháp
│   └── web/
│       └── index.html        # ✅ Web app (PWA, localStorage SRS)
├── _scripts/
│   └── add_a2_*.py           # Scripts thêm nội dung (chạy 1 lần)
├── assets/                   # (chờ thêm images/audio)
└── README.md
```

## Thêm từ vựng mới

Sửa file `src/content/curriculum.json`, thêm card theo format:

```json
{
  "word": "example",
  "phonetic": "/ɪɡˈzæmpəl/",
  "vi": "ví dụ",
  "example": "This is an example.",
  "example_vi": "Đây là một ví dụ.",
  "part_of_speech": "noun",
  "image_hint": "mô tả hình ảnh"
}
```

## Công nghệ

| Layer | Công nghệ |
|-------|-----------|
| Frontend | HTML + Tailwind CSS (CDN) |
| SRS Engine | Python (SM-2+) / JS (localStorage) |
| CLI | Python3 (không cần cài thêm) |
| Cache/Queue | Upstash Redis REST API |
| Database | localStorage (offline) / PostgreSQL (future) |

## License

MIT
