# Term Insurance Analyzer

An end-to-end AI-powered web app that scrapes term insurance plans from **PolicyBazaar** and **InsuranceDekho**, stores them in a database, and uses **Google Gemini AI** to recommend the best plan based on your age, budget, and preferences.

## Architecture

```
React Frontend (Vite + Tailwind)
        ↓  POST /api/recommend
FastAPI Backend (Python)
   ├── Playwright Scraper (PolicyBazaar + InsuranceDekho)
   ├── SQLite Database (plans refreshed every 24h)
   └── Gemini 1.5 Flash (AI recommendation engine)
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

## Setup

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

Add your Gemini API key to `backend/.env`:
```
GEMINI_API_KEY=your_key_here
```

Start the API server:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## How It Works

1. **On startup** — backend seeds the database with realistic plans for 10 major Indian insurers and attempts live scraping
2. **Every 24 hours** — APScheduler re-runs the scrapers to keep data fresh
3. **User submits profile** — age, sum assured, premium budget, policy term, min CSR
4. **Gemini AI** — receives all eligible plans and the user profile, ranks them with detailed reasoning
5. **Frontend** — displays ranked plan cards with pros/cons and an AI summary

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/plans` | List all plans |
| POST | `/api/recommend` | Get AI recommendation |
| POST | `/api/scrape` | Trigger manual scrape |
| GET | `/api/stats` | DB statistics |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| Scraping | Playwright + BeautifulSoup |
| Database | SQLite + SQLAlchemy |
| AI | Google Gemini 1.5 Flash |
| Scheduler | APScheduler |
