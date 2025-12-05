<template>
  <div class="card">
    <h2>Flight Dynamics</h2>

    <div class="field-row">
      <div class="field-label">Approach Vector:</div>
      <div class="field-value">{{ flightDynamics.approach_vector || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Exit Vector:</div>
      <div class="field-value">{{ flightDynamics.exit_vector || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Flight Pattern:</div>
      <div class="field-value">{{ flightDynamics.pattern || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Altitude Range:</div>
      <div class="field-value">
        <template v-if="flightDynamics.altitude_min_m && flightDynamics.altitude_max_m">
          {{ flightDynamics.altitude_min_m }}m - {{ flightDynamics.altitude_max_m }}m
          <span class="confidence">
            ({{ Math.round(flightDynamics.altitude_confidence * 100) }}% confidence)
          </span>
        </template>
        <template v-else>Unknown</template>
      </div>
    </div>

    <div class="field-row">
      <div class="field-label">Speed Estimate:</div>
      <div class="field-value">{{ flightDynamics.speed_estimate || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Maneuverability:</div>
      <div class="field-value">{{ flightDynamics.maneuverability || 'Unknown' }}</div>
    </div>

    <div v-if="flightDynamics.duration_seconds" class="field-row">
      <div class="field-label">Duration:</div>
      <div class="field-value">{{ flightDynamics.duration_seconds }}s</div>
    </div>

    <div v-if="flightDynamics.summary" class="reasoning">
      <h3>Analysis Summary:</h3>
      <p>{{ flightDynamics.summary }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FlightDynamics } from '@/api/types'

defineProps<{
  flightDynamics: FlightDynamics
}>()
</script>

<style scoped>
.confidence {
  color: #888;
  font-size: 0.85rem;
}

.reasoning {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #e74c3c;
}

.reasoning h3 {
  margin-top: 0;
  font-size: 0.9rem;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.reasoning p {
  margin: 0.5rem 0 0 0;
  color: #666;
  line-height: 1.6;
}
</style>
