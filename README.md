# SiteDesk · IT Consultant Challenge 2026 (Round 2: Build-a-thon)

> **From Raw Material List to Confirmed POS Order in < 2 Minutes**  
> Target: Company A (Denmark · Norway · Sweden) | In-Store Counter Assistant

---

## 🏗️ Architecture Stack
* **Frontend:** Next.js 14 (React, TypeScript, Tailwind CSS)
* **Backend:** Python FastAPI (REST API, Pydantic, SQLAlchemy)
* **Database:** PostgreSQL 15 (Docker container)
* **Orchestration:** Docker Compose

---

## 🚀 Quickstart for Team Members (Chạy 1 lệnh duy nhất)

### 1. Yêu cầu tiên quyết
* Máy tính đã cài đặt **Docker Desktop** (bật sẵn Docker Desktop).
* Không cần cài thêm Python, Node.js hay PostgreSQL trên máy cá nhân.

### 2. Khởi chạy toàn bộ hệ thống
```bash
# 1. Clone repository
git clone https://github.com/KhacToanNguyen-23/IT-Consultant-Challenge-2026.git
cd IT-Consultant-Challenge-2026

# 2. Tạo file cấu hình môi trường từ mẫu
cp .env.example .env

# 3. Khởi động cả 4 services (Frontend + Backend + PostgreSQL/pgvector + mock-pos)
docker compose up --build
```

### 3. Địa chỉ truy cập
* 🌐 **Frontend (Web Counter UI):** [http://localhost:3000](http://localhost:3000)
* ⚡ **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* 🧪 **mock-pos [simulated] POS/ERP:** [http://localhost:8001/docs](http://localhost:8001/docs)
* 🗄️ **PostgreSQL Database:** `localhost:5432` (`user: postgres`, `password: password123`, `db: sitedesk_db`)

---

## 🧭 Màn hình & luồng (branch `feat/ui-flow2`)
* `/` — nhận danh sách: **Tại quầy** (Luồng 1: paste/PDF/XLSX/CSV) hoặc **Email báo giá** (Luồng 2: dán email khách).
* `/sessions/[id]` — xem trước dòng đã đọc → Analyze → bảng rà soát (exceptions first, chip thuộc tính, quy đổi, tồn, thay thế) → Confirm (POS hoặc CSV fallback) / Lưu báo giá.
* `/quotes`, `/quotes/[id]` — Luồng 2: SAVED → SENT → ghi nhận khách xác nhận → Prepare (kiểm lại giá/tồn, diff trước→sau) → in báo giá / phiếu soạn → Confirm. Hết hạn tính khi mở, có Huỷ.
* Header có 2 công tắc demo **AI fail** / **POS fail** (MVP-FR-033). Trang báo giá có mục *Demo: đổi giá/tồn trên mock-pos* để quay cảnh diff.

> ⚠️ Matcher hiện là **placeholder theo luật + token overlap** (`backend/services/matcher.py::semantic_score`). AI owner thay bằng pgvector + multilingual-e5-small; phần hard rules/bands/gap giữ nguyên. Seed hiện có 16 SKU giả lập trong `mock-pos/seeds/` — data owner thay bằng bộ 60–80 SKU (SRS §6.3). Bảng DB tạo bằng `create_all` khi khởi động (chưa có Alembic).
>
> Nếu đã chạy bản cũ (image `postgres:15-alpine`), chạy `docker compose down -v` một lần để tạo lại volume với image pgvector.

## 📁 Cấu trúc thư mục (Monorepo)
```text
├── docker-compose.yml     # Khởi động toàn bộ FE + BE + DB
├── .env.example           # Biến môi trường mẫu
├── backend/               # Python FastAPI API & Core Engine
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py            # Entry point & CORS
│   └── db/                # SQLAlchemy database connection & models
└── frontend/              # Next.js App
    ├── Dockerfile
    ├── package.json
    └── src/app/           # Counter UI pages & components
```

---

## 📦 Deliverables Vòng 2 Checklist (Hạn 09/11/2026 - 22:00)
* [ ] `MVP.mp4`: Video Demo ứng dụng (dưới 7 phút, tiếng Anh)
* [ ] `User_Journey.pdf`: Sơ đồ hành trình người dùng (tối đa 2 trang)
* [ ] `System_Diagram.pdf`: Sơ đồ kiến trúc Inside/Outside theo C4 Model (tối đa 2 trang)
* [ ] `AI_Journal.pdf`: Nhật ký ứng dụng AI theo template của Netcompany
