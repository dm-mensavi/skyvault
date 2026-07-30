# SkyVault — Developer Setup Guide

SkyVault is an AI-powered cloud vault built with **Django 5**, **PostgreSQL + pgvector**, and **django-q2** background task cluster.

---

## 1. Prerequisites

- **Docker Desktop** (with Docker Compose)
- **Git**
- **Python 3.12+** (optional if running exclusively in Docker)

---

## 2. Quick Start (Docker — Recommended)

### Step 1: Clone the repository
```bash
git clone https://github.com/dm-mensavi/skyvault.git
cd skyvault
```

### Step 2: Configure Environment Variables
Copy `.env.example` to create your local `.env` file:
```bash
cp .env.example .env
```
*(Optionally add your `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` to test AI features)*

### Step 3: Launch Containers with Docker Compose
```bash
docker-compose up --build -d
```
This starts:
- `db-skyvault`: PostgreSQL 16 with `pgvector` extension pre-initialized
- `web-skyvault`: Django application server on `http://localhost:8000`
- `qcluster`: Django-Q2 background worker cluster

### Step 4: Apply Database Migrations
```bash
docker-compose exec web-skyvault python manage.py migrate
```

### Step 5: Create a Superuser
```bash
docker-compose exec web-skyvault python manage.py createsuperuser
```

Now open **http://localhost:8000** in your browser!

---

## 3. Useful Commands

### Check system status
```bash
docker-compose exec web-skyvault python manage.py check
```

### View container logs
```bash
# View Django web logs
docker-compose logs -f web-skyvault

# View background worker logs
docker-compose logs -f qcluster
```

### Run Django shell
```bash
docker-compose exec web-skyvault python manage.py shell
```

### Stop containers
```bash
docker-compose down
```

---

## 4. Architecture Overview

- `vault/`: Core CRUD for files and folders, upload handling, storage context, and upload signals.
- `ai_features/`: AI models (`FileAnalysis`), background task pipeline (`tasks.py`), Claude tagging/summarization, and pgvector semantic search.
- `accounts/` & `settings/`: User profile management, theme settings, and authentication.
- `dashboard/` & `notifications/`: User dashboard widgets and notification system.
