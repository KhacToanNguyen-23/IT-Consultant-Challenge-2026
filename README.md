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

# 3. Khởi động cả 3 services (Frontend + Backend + PostgreSQL)
docker compose up --build
```

### 3. Địa chỉ truy cập
* 🌐 **Frontend (Web Counter UI):** [http://localhost:3000](http://localhost:3000)
* ⚡ **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* 🗄️ **PostgreSQL Database:** `localhost:5432` (`user: postgres`, `password: password123`, `db: sitedesk_db`)

---

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
