# CUAS OSINT Dashboard V2 - Frontend

Vue 3 + TypeScript + Vite frontend for the Counter-UAS OSINT Intelligence System.

## Tech Stack

- **Framework**: Vue 3 with Composition API
- **Language**: TypeScript
- **Build Tool**: Vite 5
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Maps**: Leaflet

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client layer
│   │   ├── client.ts     # Axios instance & interceptors
│   │   ├── incidents.ts  # Incidents API endpoints
│   │   └── types.ts      # TypeScript interfaces
│   ├── components/       # Vue components
│   │   ├── DroneProfileCard.vue
│   │   ├── FlightDynamicsCard.vue
│   │   ├── OperatorHotspotsMap.vue
│   │   └── EvidenceTable.vue
│   ├── pages/            # Route pages
│   │   ├── IncidentsList.vue
│   │   └── IncidentDetail.vue
│   ├── App.vue           # Root component
│   ├── main.ts           # App entry point
│   └── router.ts         # Route definitions
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Quick Start

### Development (Local)

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start dev server:**
   ```bash
   npm run dev
   ```

3. **Access:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000 (must be running)

### Development (Docker)

```bash
# From project root
docker-compose up -d
```

Frontend will be available at http://localhost:5173

## Environment Variables

Create a `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Features

### Incidents List Page (`/incidents`)
- Paginated table of all drone incidents
- Shows: ID, Title, Country, Date, Location
- Click "View" to see incident intelligence

### Incident Detail Page (`/incidents/:id`)
- **Header**: Incident metadata (title, location, date, analysis info)
- **Left Column**:
  - Drone Profile Card: type, confidence, size, sound, lights
  - Flight Dynamics Card: vectors, altitude, speed, patterns
- **Right Column**:
  - Operator Hotspots Map (Leaflet): target marker + 3 predicted hotspots
  - Operator Analysis Summary: search radius, perimeter, methodology
- **Bottom**:
  - Evidence Table: sources, credibility scores, expandable rows

## API Integration

The frontend communicates with the backend via:

- `GET /incidents` - List incidents (paginated)
- `GET /incidents/{id}/intelligence` - Full intelligence analysis

See `src/api/types.ts` for the complete TypeScript interface definitions.

## Map Component

`OperatorHotspotsMap.vue` uses Leaflet to display:
- **Target marker**: Incident location (crosshair icon)
- **Hotspot markers**: Ranked 1-3 (red, orange, yellow)
- **Circles**: Score-based radius around each hotspot
- **Popups**: Score, distance, cover type, terrain, reasoning

## Styling

- Minimal custom CSS (no framework)
- Clean, professional design
- Responsive layout (2-column grid on desktop, stacks on mobile)
- Color scheme: Dark header (#1a1a1a) with red accent (#e74c3c)

## Build for Production

```bash
npm run build
```

Output in `dist/` directory.

## TODOs

- [ ] Add unit tests (Vitest)
- [ ] Add E2E tests (Playwright)
- [ ] Implement error boundaries
- [ ] Add loading skeletons
- [ ] Implement real-time updates (WebSocket)
- [ ] Add data export features (CSV, JSON)
- [ ] Implement filters/search on incidents list
- [ ] Add authentication/authorization
