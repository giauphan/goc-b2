# Gốc.B2 — Học Tiếng Anh Cho Người Việt (Mất Gốc → B2)

Website/app học tiếng Anh dành cho người Việt mất gốc và người mới bắt đầu từ A1 tới B2.

## Tính năng

- **🇻🇳 Giải thích bằng tiếng Việt** — Ngữ pháp, phát âm giải thích bằng tiếng Việt
- **🧠 SM-2 Spaced Repetition** — Thuật toán ghi nhớ thông minh (Anki-like)
- **🎯 Lộ trình A1→B2** — 5 chủ đề A1 (125 từ), hơn 500+ từ sắp ra mắt
- **🗣️ Phát âm trọng tâm** — /θ/, /ð/, /ʃ/, /tʃ/, phụ âm cuối
- **📸 Học qua hình ảnh** — Mỗi từ có image hint + IPA + audio + ví dụ
- **📊 Theo dõi tiến trình** — Streak, XP, SRS analytics
- **⚡ PWA** — Học offline trên mobile

## Công nghệ

| Layer | Công nghệ |
|-------|-----------|
| Frontend | Next.js + Tailwind CSS |
| SRS Engine | Python (SM-2+) |
| Cache/Queue | Redis (SRS queue, session) |
| Database | PostgreSQL (user data, content) |
| TTS | Amazon Polly / Google Cloud TTS |
| Auth | NextAuth.js |

## Cấu trúc thư mục

```
goc-b2/
├── research/              # Tài liệu nghiên cứu
│   └── english-learning-brief.md
├── src/
│   ├── srs/               # SRS Engine
│   │   ├── sm2.py         # SM-2+ algorithm
│   │   └── redis_client.py # Redis integration
│   ├── content/           # Curriculum data
│   │   ├── curriculum.json # A1: 125 cards, 5 topics
│   │   └── grammar.json   # Vietnamese-focused grammar
│   └── web/               # Frontend
│       ├── index.html     # Landing page (prototype)
│       ├── pages/         # Next.js pages (coming)
│       ├── components/    # React components (coming)
│       └── styles/        # CSS
├── assets/                # Images & audio
│   ├── images/
│   └── audio/
└── README.md
```

## Quick Start

```bash
cd ~/goc-b2

# Setup Python SRS engine
python3 -m venv venv
source venv/bin/activate
pip install pytest

# Set Upstash Redis credentials
source .env

# Test SRS engine
python3 -c "
from src.srs.sm2 import CardState, sm2
card = CardState()
card = sm2(card, 4)  # Quality 4/5
print(f'Next review in {card.interval} days, EF={card.ef:.2f}')
"

# Run SRS with Upstash Redis
python3 -c "
from src.srs.redis_client import SRSRedisClient
client = SRSRedisClient()
print(client.health_check())
"
```

## Quick Start (Frontend)

Landing page prototype là file HTML tĩnh — mở trực tiếp trong browser:

```bash
# Open landing page
open src/web/index.html
# Hoặc: xdg-open src/web/index.html
# Hoặc copy đường dẫn vào browser
```

Khi sẵn sàng build Next.js:

```bash
npx create-next-app@latest . --typescript --tailwind
# Copy components từ src/web/components vào app/
```

## Phát triển

### Thêm từ vựng mới

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

### Thêm chủ đề ngữ pháp

Sửa file `src/content/grammar.json`, thêm topic mới.

## Nghiên cứu thêm

Xem `research/english-learning-brief.md` — nghiên cứu đầy đủ về:
- Hệ thống học ngôn ngữ hiệu quả (Duolingo, Memrise, Anki)
- Thuật toán SM-2+ trên Redis
- Khó khăn đặc thù của người Việt (phát âm, ngữ pháp)
- Phân tích đối thủ cạnh tranh
- Chiến lược nội dung theo CEFR
- Kiến trúc kỹ thuật đề xuất

## License

MIT
