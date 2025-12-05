<template>
  <div class="container">
    <!-- Back button -->
    <div class="breadcrumb">
      <router-link to="/incidents" class="btn btn-back">← Back to Incidents</router-link>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">Loading incident intelligence...</div>

    <!-- Error state -->
    <div v-else-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Main content -->
    <div v-else-if="intelligence">
      <!-- Incident header -->
      <div class="card incident-header">
        <h1>{{ intelligence.incident.title }}</h1>
        <div class="incident-meta">
          <div class="meta-item">
            <strong>Country:</strong> {{ intelligence.incident.country_code }}
          </div>
          <div class="meta-item">
            <strong>Location:</strong> {{ intelligence.incident.location_name }}
          </div>
          <div class="meta-item">
            <strong>Date:</strong> {{ formatDate(intelligence.incident.occurred_at) }}
          </div>
          <div class="meta-item">
            <strong>ID:</strong> {{ intelligence.incident.id }}
          </div>
          <div class="meta-item">
            <strong>Analyzed:</strong> {{ formatDate(intelligence.meta.analyzed_at) }}
          </div>
          <div class="meta-item">
            <strong>LLM Mode:</strong> {{ intelligence.meta.llm_mode }}
          </div>
        </div>
      </div>

      <!-- Two column layout -->
      <div class="detail-layout">
        <!-- Left column: Drone profile and flight dynamics -->
        <div class="left-column">
          <DroneProfileCard :drone-profile="intelligence.drone_profile" />
          <FlightDynamicsCard :flight-dynamics="intelligence.flight_dynamics" />
        </div>

        <!-- Right column: Map -->
        <div class="right-column">
          <OperatorHotspotsMap
            :target-lat="targetCoords.lat"
            :target-lon="targetCoords.lon"
            :hotspots="intelligence.operator_hotspots"
          />

          <!-- Operator Analysis Summary -->
          <div class="card operator-summary">
            <h2>Operator Analysis Summary</h2>
            <div class="field-row">
              <div class="field-label">Search Radius:</div>
              <div class="field-value">{{ intelligence.meta.search_radius_m }}m</div>
            </div>
            <div class="field-row">
              <div class="field-label">Perimeter Radius:</div>
              <div class="field-value">{{ intelligence.meta.perimeter_radius_m }}m</div>
            </div>
            <div class="field-row">
              <div class="field-label">Top Hotspots:</div>
              <div class="field-value">{{ intelligence.operator_hotspots.length }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom section: Evidence table -->
      <EvidenceTable
        :summary="intelligence.evidence_summary"
        :items="intelligence.evidence"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { incidentsApi } from '@/api/incidents'
import type { IntelligenceResponse } from '@/api/types'
import DroneProfileCard from '@/components/DroneProfileCard.vue'
import FlightDynamicsCard from '@/components/FlightDynamicsCard.vue'
import OperatorHotspotsMap from '@/components/OperatorHotspotsMap.vue'
import EvidenceTable from '@/components/EvidenceTable.vue'

const props = defineProps<{
  id: number
}>()

const router = useRouter()
const loading = ref(true)
const error = ref<string | null>(null)
const intelligence = ref<IntelligenceResponse | null>(null)

// Extract target coordinates from incident
const targetCoords = computed(() => {
  if (intelligence.value?.incident) {
    return {
      lat: intelligence.value.incident.latitude,
      lon: intelligence.value.incident.longitude
    }
  }

  // Default fallback (Volkel Air Base)
  return {
    lat: 51.6565,
    lon: 5.7085
  }
})

const loadIntelligence = async () => {
  loading.value = true
  error.value = null

  try {
    // Call the intelligence endpoint which returns everything we need
    intelligence.value = await incidentsApi.getIncidentIntelligence(props.id)
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load incident intelligence'
    console.error('Intelligence load error:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadIntelligence()
})
</script>

<style scoped>
.breadcrumb {
  margin-bottom: 1.5rem;
}

.btn-back {
  background: #555;
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  display: inline-block;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #333;
}

.incident-header h1 {
  font-size: 1.75rem;
  margin-bottom: 1rem;
  color: #1a1a1a;
}

.incident-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.meta-item {
  font-size: 0.9rem;
  color: #555;
}

.meta-item strong {
  color: #333;
  margin-right: 0.25rem;
}

.incident-summary {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #e74c3c;
}

.incident-summary p {
  margin: 0;
  line-height: 1.6;
  color: #555;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 1024px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
}

.operator-summary {
  margin-top: 1.5rem;
}
</style>
