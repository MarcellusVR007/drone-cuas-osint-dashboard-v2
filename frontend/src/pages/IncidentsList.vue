<template>
  <div class="container">
    <div class="card">
      <h2>Drone Incidents</h2>

      <div v-if="loading" class="loading">Loading incidents...</div>

      <div v-else-if="error" class="error">
        <strong>Error:</strong> {{ error }}
      </div>

      <div v-else-if="incidents.length === 0" class="loading">
        No incidents found.
      </div>

      <table v-else>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Country</th>
            <th>Date</th>
            <th>Site</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="incident in incidents" :key="incident.id">
            <td>{{ incident.id }}</td>
            <td>{{ incident.title }}</td>
            <td>{{ incident.country_code }}</td>
            <td>{{ formatDate(incident.occurred_at) }}</td>
            <td>{{ incident.location_name || '-' }}</td>
            <td>
              <router-link
                :to="`/incidents/${incident.id}`"
                class="btn btn-primary"
              >
                View
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="pagination.total_pages > 1" class="pagination">
        <button
          class="btn btn-primary"
          :disabled="pagination.page === 1"
          @click="loadPage(pagination.page - 1)"
        >
          Previous
        </button>
        <span class="page-info">
          Page {{ pagination.page }} of {{ pagination.total_pages }}
          ({{ pagination.total }} total)
        </span>
        <button
          class="btn btn-primary"
          :disabled="pagination.page === pagination.total_pages"
          @click="loadPage(pagination.page + 1)"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { incidentsApi } from '@/api/incidents'
import type { Incident } from '@/api/types'

const incidents = ref<Incident[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const pagination = ref({
  page: 1,
  page_size: 50,
  total: 0,
  total_pages: 0
})

const loadPage = async (page: number) => {
  loading.value = true
  error.value = null

  try {
    const response = await incidentsApi.getIncidents(page, pagination.value.page_size)
    incidents.value = response.items
    pagination.value = {
      page: response.page,
      page_size: response.page_size,
      total: response.total,
      total_pages: response.total_pages
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load incidents'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadPage(1)
})
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.page-info {
  color: #666;
  font-size: 0.9rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
