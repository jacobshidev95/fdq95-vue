# FDQ95 - Vue 3 + FastAPI

前后端分离的登录注册门户。技术栈：

- Frontend: Vue 3 + Vite + TypeScript + Pinia + Vue Router
- Backend:  FastAPI + fastapi-users + SQLAlchemy 2.0 (async)
- Database: PostgreSQL 16
- 多语言:   LibreTranslate (自托管)
- 部署:     Docker Compose

## 快速开始

    cp .env.example .env
    docker compose up -d --build
    # 首次启动 LibreTranslate 会下载语言模型，需要几分钟
    # 访问 http://localhost:8080

## 本地开发

Backend:
    cd backend
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8080

Frontend:
    cd frontend
    npm install
    npm run dev   # http://localhost:5173

开发时前端通过 Vite proxy 把 /api /auth /users 转发到后端 8080。

## 目录

    backend/   FastAPI 应用
    frontend/  Vue 3 应用
