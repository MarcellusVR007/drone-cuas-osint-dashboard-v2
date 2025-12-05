import { apiClient } from './client'
import type {
  Incident,
  PaginatedIncidents,
  IntelligenceResponse
} from './types'

export const incidentsApi = {
  /**
   * Get paginated list of incidents
   */
  async getIncidents(page: number = 1, pageSize: number = 50): Promise<PaginatedIncidents> {
    const response = await apiClient.get('/incidents', {
      params: { page, page_size: pageSize }
    })
    return response.data
  },

  /**
   * Get single incident by ID
   */
  async getIncident(id: number): Promise<Incident> {
    const response = await apiClient.get(`/incidents/${id}`)
    return response.data
  },

  /**
   * Get full intelligence analysis for an incident
   */
  async getIncidentIntelligence(id: number): Promise<IntelligenceResponse> {
    const response = await apiClient.get(`/incidents/${id}/intelligence`)
    return response.data
  }
}
