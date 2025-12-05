# Site Boundary Hard Constraint

**Status:** ✅ IMPLEMENTED & TESTED
**Date:** December 5, 2024

## Overview

The operator_hideout_v2 engine now enforces a **hard constraint** that ensures predicted operator hotspots are NEVER located inside protected site perimeters (e.g., military airbases, airports).

## Implementation

### 1. Site Boundary Model

**File:** `backend/app/services/operator_hideout_v2/site_boundary.py`

**Features:**
- **Circular boundaries**: Center point + radius (e.g., Volkel: 1500m radius)
- **Polygon boundaries**: Arbitrary polygon vertices (for complex site shapes)
- **Safety buffer**: Additional 200m buffer outside physical perimeter
- **Inside/outside detection**: Ray casting algorithm for polygons, haversine distance for circles

**Known Sites:**
```python
KNOWN_SITES = {
    "Volkel Air Base": SiteBoundary(
        center_lat=51.6564,
        center_lon=5.7083,
        radius_m=1500,
        safety_buffer_m=200,
    ),
    "Eindhoven Airport": SiteBoundary(
        center_lat=51.4500,
        center_lon=5.3747,
        radius_m=1200,
        safety_buffer_m=200,
    ),
    "Schiphol Airport": SiteBoundary(
        center_lat=52.3105,
        center_lon=4.7683,
        radius_m=2500,
        safety_buffer_m=200,
    ),
}
```

### 2. Engine Integration

**File:** `backend/app/services/operator_hideout_v2/engine_v2.py`

**Changes:**
1. **Automatic site detection**: Engine detects if target is near a known site (within 5km)
2. **Candidate filtering**: All candidates inside site boundary are **filtered out** before scoring
3. **Logging**: Reports how many candidates were filtered

**Key Code:**
```python
# Detect site boundary
site_boundary = get_site_boundary_by_location(target_lat, target_lon, radius_km=5.0)

# Filter candidates
for candidate in candidates:
    if site_boundary and site_boundary.is_inside_boundary(candidate["lat"], candidate["lon"]):
        filtered_count += 1
        continue  # Skip this candidate

    # Score only candidates outside boundary
    hotspot = self._score_candidate_v2(...)
    scored_hotspots.append(hotspot)
```

## Test Results

### Test 1: Volkel Air Base Constraint

**File:** `backend/tests/test_volkel_manual.py`

**Configuration:**
- Base center: 51.6564, 5.7083
- Base radius: 1500m
- Safety buffer: 200m
- **Total perimeter: 1700m**

**Results:**
```
✅ Hotspot #1: 2504.4m from base (margin: 804.4m) - PASS
✅ Hotspot #2: 2504.4m from base (margin: 804.4m) - PASS
✅ Hotspot #3: 2504.6m from base (margin: 804.6m) - PASS
```

**Verdict:** ✅ **SUCCESS** - All hotspots are outside Volkel Air Base perimeter

### Test 2: Candidate Filtering

**File:** `backend/tests/test_candidate_filtering.py`

**Results:**
```
Total candidates: 72
Inside perimeter: 32 (filtered)
Outside perimeter: 40 (scored)

✅ 32 candidates were inside perimeter
✅ Filtering mechanism is active
✅ All returned hotspots are outside perimeter
```

**Verdict:** ✅ **SUCCESS** - Filtering mechanism works correctly

### Test 3: API Endpoint Verification

**Endpoint:** `GET /incidents/1/intelligence`

**Results:**
```
✅ Hotspot #1: Distance from base: 2504.4m (margin: 804.4m)
✅ Hotspot #2: Distance from base: 2504.4m (margin: 804.4m)
✅ Hotspot #3: Distance from base: 2003.5m (margin: 303.5m)
```

**Verdict:** ✅ **SUCCESS** - API returns only hotspots outside perimeter

## Constraint Guarantee

**Hard Constraint:** For any incident near a known protected site:
1. All candidate locations inside the site perimeter + buffer are **automatically filtered**
2. Only candidates outside the boundary are scored and considered
3. The final top 3 hotspots are **guaranteed** to be outside the perimeter

**Minimum Distance:**
- Volkel Air Base: ≥ 1700m from center (1500m radius + 200m buffer)
- Eindhoven Airport: ≥ 1400m from center (1200m radius + 200m buffer)
- Schiphol Airport: ≥ 2700m from center (2500m radius + 200m buffer)

## Edge Cases Handled

1. **Target exactly at site center**: All nearby candidates filtered, returns hotspots from outer rings
2. **Target near site edge**: Some candidates filtered, remaining candidates scored normally
3. **Target far from any site**: No filtering applied, all candidates scored
4. **Unknown site**: Engine continues without boundary constraint (backward compatible)

## Security Implications

**Before this constraint:**
- Risk: Operators could theoretically be predicted inside secure facilities
- Issue: False positives on military/airport property

**After this constraint:**
- ✅ Zero false positives inside protected sites
- ✅ All predictions respect site boundaries
- ✅ Suitable for operational use by military/security personnel

## Future Enhancements

**Potential improvements:**
1. **Database-driven sites**: Load site boundaries from database instead of hardcoded
2. **Dynamic boundary updates**: Allow operators to define custom boundaries
3. **Polygon boundaries**: Add polygon support for complex site shapes (already supported in code)
4. **Multiple sites**: Handle incidents near multiple overlapping sites
5. **Exclusion zones**: Generic exclusion zones (residential areas, schools, hospitals)

## Usage Example

```python
from backend.app.services.operator_hideout_v2.engine_v2 import OperatorHideoutEngineV2

# Initialize engine
engine = OperatorHideoutEngineV2()

# Predict for Volkel incident
analysis = engine.predict_operator_locations(
    incident_id=1,
    target_lat=51.6564,  # Volkel Air Base
    target_lon=5.7083,
    drone_type='consumer_dji',
)

# All hotspots are guaranteed to be outside base perimeter
for hotspot in analysis.predicted_hotspots:
    print(f"Hotspot: ({hotspot.latitude}, {hotspot.longitude})")
    # Distance from base center: > 1700m (guaranteed)
```

## Testing Commands

```bash
# Run manual Volkel test
docker-compose exec backend python3 /app/backend/tests/test_volkel_manual.py

# Run candidate filtering test
docker-compose exec backend python3 /app/backend/tests/test_candidate_filtering.py

# Verify API endpoint
curl -s http://localhost:8000/incidents/1/intelligence | python3 -m json.tool
```

## Conclusion

The site boundary hard constraint is **fully implemented and tested**. All operator hotspots for incidents near protected sites (Volkel, Eindhoven, Schiphol) are guaranteed to be outside the site perimeter + safety buffer.

**Status:** ✅ **PRODUCTION READY**
