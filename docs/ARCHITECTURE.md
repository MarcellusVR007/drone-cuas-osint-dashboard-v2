# Architecture Rules

## Overview

V2 follows a strict layered architecture with clear boundaries between concerns:

```
backend/app/
├── domain/       # Entity models (SQLAlchemy ORM)
├── services/     # Business logic layer
├── llm/          # LLM prompts, schemas, function-calling
├── db/           # Database session, engine, connection
└── api/          # FastAPI routes, request/response marshaling
```

## Layer Responsibilities

### 1. `domain/` - Entity Models

**Purpose:** Pure SQLAlchemy ORM models. No business logic.

**Rules:**
- ✅ Define database tables and relationships
- ✅ Use SQLAlchemy Column, ForeignKey, relationship
- ✅ Add indexes, constraints, validations at DB level
- ❌ NO business logic
- ❌ NO LLM calls
- ❌ NO external API calls

**Example:**
```python
# backend/app/domain/incident.py
from sqlalchemy import Column, Integer, String, TIMESTAMP
from backend.app.db.base import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    country_code = Column(String(2))
```

### 2. `services/` - Business Logic

**Purpose:** All business logic, data transformations, enrichment, operator analysis.

**Rules:**
- ✅ Process and enrich data
- ✅ Call LLM layer for AI reasoning
- ✅ Query database via SQLAlchemy
- ✅ Implement algorithms (hideout engine, evidence stacking)
- ❌ NO FastAPI dependencies (Request, Response, etc.)
- ❌ NO direct Anthropic/OpenAI API calls (use `llm/` layer)

**Example:**
```python
# backend/app/services/enrichment.py
from backend.app.llm.enrichment import enrich_incident_with_llm

def enrich_incident(incident: Incident, db: Session) -> Incident:
    # Business logic here
    llm_result = enrich_incident_with_llm(incident.title)
    incident.raw_metadata = llm_result
    db.commit()
    return incident
```

### 3. `llm/` - LLM Integration

**Purpose:** ALL LLM interaction logic. Prompts, schemas, function-calling helpers.

**Rules:**
- ✅ Define LLM prompts as Python functions
- ✅ Define Pydantic schemas for structured output
- ✅ Handle LLM API calls (Anthropic, OpenAI)
- ✅ Retry logic, error handling for LLM calls
- ❌ NO business logic (just LLM I/O)
- ❌ NO database access
- ❌ NO FastAPI dependencies

**Example:**
```python
# backend/app/llm/enrichment.py
from anthropic import Anthropic
from pydantic import BaseModel

class IncidentEnrichment(BaseModel):
    location_name: str
    site_type: str
    severity: str

def enrich_incident_with_llm(title: str) -> IncidentEnrichment:
    client = Anthropic()
    # ... LLM call logic
    return IncidentEnrichment(...)
```

### 4. `db/` - Database Layer

**Purpose:** Session management, engine configuration, connection pooling.

**Rules:**
- ✅ Create SQLAlchemy engine
- ✅ Session factory and dependency injection
- ✅ Database URL configuration
- ❌ NO business logic
- ❌ NO ORM models (those go in `domain/`)

**Example:**
```python
# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5. `api/` - FastAPI Routes

**Purpose:** HTTP request/response handling, marshaling, validation.

**Rules:**
- ✅ Define FastAPI routes (@router.get, @router.post)
- ✅ Request validation (Pydantic models)
- ✅ Response serialization
- ✅ Call `services/` layer for business logic
- ✅ Use dependency injection (Depends) for DB session
- ❌ NO business logic (delegate to `services/`)
- ❌ NO direct database queries (use `services/`)
- ❌ NO LLM calls (use `services/` → `llm/`)

**Example:**
```python
# backend/app/api/incidents.py
from fastapi import APIRouter, Depends
from backend.app.services.incident_service import get_incident_by_id
from backend.app.db.session import get_db

router = APIRouter()

@router.get("/incidents/{id}")
def read_incident(id: int, db: Session = Depends(get_db)):
    return get_incident_by_id(id, db)
```

## Data Flow

```
HTTP Request
    ↓
api/ (FastAPI routes)
    ↓
services/ (business logic)
    ↓              ↓
  llm/           db/ → domain/
(LLM calls)    (database)
    ↓              ↓
services/ (combine results)
    ↓
api/ (response)
    ↓
HTTP Response
```

## Migration Rules

- Use Alembic for all schema changes
- Never modify database directly
- Always create migrations for model changes
- Test migrations both up and down

## Import Rules

**Allowed imports:**
- `domain/` can import: `db/base.py` only
- `services/` can import: `domain/`, `llm/`, `db/session.py`
- `llm/` can import: nothing from backend (external libs only)
- `api/` can import: `services/`, `db/session.py`, `domain/` (for type hints)
- `db/` can import: `domain/` (for metadata)

**Forbidden imports:**
- `domain/` → `services/`, `llm/`, `api/`
- `llm/` → anything from `backend/app/`
- `api/` → `llm/` (must go through `services/`)

## Testing Strategy

- Unit tests for `services/` and `llm/`
- Integration tests for `api/` endpoints
- Use pytest with fixtures for DB session
- Mock LLM calls in tests

## Documentation Standards

Every module must have:
1. Docstring explaining purpose
2. Type hints on all functions
3. Comments for complex logic
4. Examples in docstrings
