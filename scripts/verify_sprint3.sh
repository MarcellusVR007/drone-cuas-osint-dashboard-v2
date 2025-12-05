#!/bin/bash
# Sprint 3 Verification Script

echo "=== CUAS OSINT Dashboard V2 - Sprint 3 Verification ==="
echo ""

echo "✅ Backend Health:"
curl -s http://localhost:8000/health | jq '.'
echo ""

echo "✅ Incidents API:"
curl -s http://localhost:8000/incidents | jq '{total: .total, items: .items | length}'
echo ""

echo "✅ Intelligence API:"
curl -s http://localhost:8000/incidents/1/intelligence | jq '{
  incident: .incident.title,
  drone_type: .drone_profile.type_primary,
  hotspots: (.operator_hotspots | length),
  evidence: (.evidence | length)
}'
echo ""

echo "✅ Frontend:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173)
if [ "$HTTP_CODE" == "200" ]; then
  echo "Frontend: HTTP $HTTP_CODE ✓"
else
  echo "Frontend: HTTP $HTTP_CODE ✗"
fi
echo ""

echo "✅ Docker Services:"
docker-compose ps

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
