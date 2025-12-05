<template>
  <div class="card">
    <h2>Drone Profile</h2>

    <div class="field-row">
      <div class="field-label">Primary Type:</div>
      <div class="field-value">{{ droneProfile.type_primary || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Type Confidence:</div>
      <div class="field-value">
        <div class="confidence-bar">
          <div
            class="confidence-bar-fill"
            :style="{ width: `${droneProfile.type_confidence * 100}%` }"
          ></div>
        </div>
        <span class="confidence-text">{{ Math.round(droneProfile.type_confidence * 100) }}%</span>
      </div>
    </div>

    <div v-if="droneProfile.type_alternatives && droneProfile.type_alternatives.length > 0" class="field-row">
      <div class="field-label">Alternative Types:</div>
      <div class="field-value">
        <span
          v-for="alt in droneProfile.type_alternatives"
          :key="alt"
          class="tag"
        >
          {{ alt }}
        </span>
      </div>
    </div>

    <div class="field-row">
      <div class="field-label">Size Estimate:</div>
      <div class="field-value">{{ droneProfile.size_estimate || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Sound Signature:</div>
      <div class="field-value">{{ droneProfile.sound_signature || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Visual Description:</div>
      <div class="field-value">{{ droneProfile.visual_description || 'Unknown' }}</div>
    </div>

    <div class="field-row">
      <div class="field-label">Lights Observed:</div>
      <div class="field-value">{{ droneProfile.lights_observed ? 'Yes' : 'No' }}</div>
    </div>

    <div v-if="droneProfile.light_pattern" class="field-row">
      <div class="field-label">Light Pattern:</div>
      <div class="field-value">{{ droneProfile.light_pattern }}</div>
    </div>

    <div v-if="droneProfile.summary" class="reasoning">
      <h3>Analysis Summary:</h3>
      <p>{{ droneProfile.summary }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DroneProfile } from '@/api/types'

defineProps<{
  droneProfile: DroneProfile
}>()
</script>

<style scoped>
.confidence-text {
  display: inline-block;
  margin-top: 0.25rem;
  font-size: 0.9rem;
  color: #555;
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
