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

**Future Sprints:**
- Sprint 2: LLM enrichment layer
- Sprint 3: Operator hideout engine
- Sprint 4: Evidence stacking
- Sprint 5: Data ingestion pipeline
- Sprint 6: Frontend integration

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture rules.

```
backend/
├── app/
│   ├── domain/       # ORM models only
│   ├── services/     # Business logic
│   ├── llm/          # LLM prompts & schemas
│   ├── db/           # Database session/engine
│   └── api/          # FastAPI routes
```

## Quick Start

1. **Start services:**
   ```bash
   ./scripts/run_local.sh
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. **Test endpoints:**
   ```bash
   python scripts/check_sanity.py
   ```

## API Endpoints

- `GET /health` - Health check
- `GET /incidents` - List incidents (paginated)
- `GET /incidents/{id}` - Get incident detail
- `GET /sites` - List sites

## Development

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL 15
- **Migrations:** Alembic
- **Docker:** `docker-compose.yml` for local dev

## Rules

1. All LLM calls must go through `backend/app/llm/`
2. No direct database access from API routes (use services)
3. Domain models are pure SQLAlchemy ORM
4. Follow the architecture boundaries strictly

See [docs/LLM_RULES.md](docs/LLM_RULES.md) for LLM integration rules.
