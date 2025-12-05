<template>
  <div class="card">
    <h2>Predicted Operator Hotspots</h2>
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import L from 'leaflet'
import type { OperatorHotspot } from '@/api/types'

const props = defineProps<{
  targetLat: number
  targetLon: number
  hotspots: OperatorHotspot[]
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null

const initMap = () => {
  if (!mapContainer.value) return

  // Create map centered on target
  map = L.map(mapContainer.value).setView([props.targetLat, props.targetLon], 13)

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map)

  // Add target marker (incident location)
  const targetIcon = L.divIcon({
    className: 'target-marker',
    html: '<div class="target-marker-inner">⊕</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  })

  L.marker([props.targetLat, props.targetLon], { icon: targetIcon })
    .addTo(map)
    .bindPopup('<strong>Incident Target Location</strong>')

  // Add hotspot markers
  props.hotspots.forEach((hotspot) => {
    const color = getHotspotColor(hotspot.rank)
    const markerIcon = L.divIcon({
      className: 'hotspot-marker',
      html: `<div class="hotspot-marker-inner" style="background: ${color};">${hotspot.rank}</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    })

    const marker = L.marker([hotspot.latitude, hotspot.longitude], { icon: markerIcon })
      .addTo(map!)
      .bindPopup(createHotspotPopup(hotspot))

    // Add circle to show coverage area (score-based radius)
    const radius = hotspot.total_score * 200 // Scale radius by score
    L.circle([hotspot.latitude, hotspot.longitude], {
      color: color,
      fillColor: color,
      fillOpacity: 0.15,
      radius: radius,
      weight: 2
    }).addTo(map!)
  })

  // Fit bounds to show all markers
  const bounds = L.latLngBounds([
    [props.targetLat, props.targetLon],
    ...props.hotspots.map(h => [h.latitude, h.longitude] as [number, number])
  ])
  map.fitBounds(bounds, { padding: [50, 50] })
}

const getHotspotColor = (rank: number): string => {
  switch (rank) {
    case 1:
      return '#e74c3c' // Red for #1
    case 2:
      return '#f39c12' // Orange for #2
    case 3:
      return '#f1c40f' // Yellow for #3
    default:
      return '#95a5a6' // Gray for others
  }
}

const createHotspotPopup = (hotspot: OperatorHotspot): string => {
  return `
    <div class="hotspot-popup">
      <h4>Hotspot #${hotspot.rank}</h4>
      <p><strong>Total Score:</strong> ${(hotspot.total_score * 100).toFixed(1)}%</p>
      <p><strong>Distance:</strong> ${Math.round(hotspot.distance_to_target_m)}m from target</p>
      <p><strong>Cover:</strong> ${hotspot.cover_type.replace(/_/g, ' ')}</p>
      <p><strong>Terrain:</strong> ${hotspot.terrain_suitability}</p>
      <p><strong>Nearest Road:</strong> ${hotspot.nearest_road_type.replace(/_/g, ' ')} (${Math.round(hotspot.nearest_road_distance_m)}m)</p>
      <p class="reasoning"><strong>Reasoning:</strong><br/>${hotspot.reasoning}</p>
    </div>
  `
}

onMounted(() => {
  initMap()
})

// Cleanup on unmount
watch(() => props.hotspots, () => {
  if (map) {
    map.remove()
    map = null
  }
  initMap()
})
</script>

<style>
/* Leaflet marker overrides - must be global */
.target-marker {
  background: transparent;
  border: none;
}

.target-marker-inner {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #2c3e50;
  background: white;
  border: 3px solid #2c3e50;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}

.hotspot-marker {
  background: transparent;
  border: none;
}

.hotspot-marker-inner {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: white;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0,0,0,0.4);
  border: 2px solid white;
}

.hotspot-popup h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.hotspot-popup p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
}

.hotspot-popup .reasoning {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
  font-size: 0.85rem;
  color: #666;
}
</style>

<style scoped>
.map-container {
  width: 100%;
  height: 500px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ddd;
}
</style>
