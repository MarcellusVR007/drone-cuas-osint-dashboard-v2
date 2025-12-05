# Drone CUAS OSINT Dashboard V2

Counter-UAS Intelligence System - Clean Architecture Rewrite

## Overview

V2 is a complete rewrite of the OSINT CUAS Dashboard with:
- Clean separation of concerns (domain, services, API, LLM)
- PostgreSQL with proper schema design
- AI-first architecture for enrichment and operator analysis
- Strict architecture boundaries

## Project Status

**Sprint 0/1: Foundation** ✅
- PostgreSQL + SQLAlchemy + Alembic
- Domain models: Incident, Site, Evidence
- Basic CRUD API endpoints
- Docker Compose setup

**Sprint 2: Intelligence Layer** ✅
- Evidence Stack Builder (aggregation, deduplication, scoring)
- LLM Evidence Enrichment (drone type, flight dynamics, altitude)
- Operator Hideout Engine (OPSEC-TTP analysis)
- Intelligence API endpoint (`/incidents/{id}/intelligence`)

**Sprint 3: Frontend Application** ✅
- Vue 3 + TypeScript + Vite
- Incidents list and detail pages
- Interactive Leaflet maps with operator hotspots
- Drone profile, flight dynamics, and evidence visualization
- Docker integration

**Future Sprints:**
- Sprint 4: Styling & UX improvements (Tailwind CSS)
- Sprint 5: Data ingestion pipeline (scrapers, feeds)
- Sprint 6: Authentication & authorization
- Sprint 7: Real-time updates & notifications

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture rules.

```
drone-cuas-osint-dashboard-v2/
├── backend/
│   └── app/
│       ├── domain/       # ORM models only
│       ├── services/     # Business logic
│       ├── llm/          # LLM prompts & schemas
│       ├── db/           # Database session/engine
│       └── api/          # FastAPI routes
├── frontend/
│   └── src/
│       ├── api/          # API client layer
│       ├── components/   # Vue components
│       ├── pages/        # Route pages
│       ├── App.vue       # Root component
│       ├── main.ts       # Entry point
│       └── router.ts     # Route definitions
├── docker-compose.yml    # Multi-service orchestration
└── scripts/              # Utility scripts
```

## Quick Start

### Using Docker (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Start PostgreSQL (or use Docker)
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Start backend
uvicorn backend.app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /incidents` - List incidents (paginated)
- `GET /incidents/{id}` - Get incident detail
- `GET /sites` - List sites

### Intelligence Endpoint (Sprint 2)
- `GET /incidents/{id}/intelligence` - Full intelligence analysis
  - Drone profile (type, size, lights, confidence)
  - Flight dynamics (vectors, altitude, speed, patterns)
  - Operator hotspots (OPSEC-TTP predicted locations)
  - Evidence stack (sources, credibility, locality scores)

### Frontend Routes (Sprint 3)
- `/` - Redirects to incidents list
- `/incidents` - Incidents list page (table with pagination)
- `/incidents/:id` - Incident detail page (intelligence visualization)

## Tech Stack

### Backend
- **Framework:** FastAPI 0.115+
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **LLM:** Anthropic Claude (optional, falls back to mock)

### Frontend
- **Framework:** Vue 3.4+ (Composition API)
- **Language:** TypeScript 5.3+
- **Build Tool:** Vite 5.0+
- **Routing:** Vue Router 4.2+
- **HTTP Client:** Axios 1.6+
- **Maps:** Leaflet 1.9+

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Orchestration:** docker-compose.yml (3 services)
- **Ports:**
  - Frontend: 5173
  - Backend: 8000
  - PostgreSQL: 5432

## Rules

1. All LLM calls must go through `backend/app/llm/`
2. No direct database access from API routes (use services)
3. Domain models are pure SQLAlchemy ORM
4. Follow the architecture boundaries strictly

See [docs/LLM_RULES.md](docs/LLM_RULES.md) for LLM integration rules.
