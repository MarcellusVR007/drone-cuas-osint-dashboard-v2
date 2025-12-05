// Backend API types (matching actual Sprint 2 API response)

export interface Incident {
  id: number
  title: string
  location_name: string
  country_code: string
  occurred_at: string
  latitude: number
  longitude: number
}

export interface PaginatedIncidents {
  items: Incident[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Intelligence API types

export interface DroneProfile {
  type_primary: string
  type_confidence: number
  type_alternatives: string[]
  size_estimate?: string | null
  sound_signature?: string | null
  visual_description?: string | null
  lights_observed: boolean
  light_pattern?: string | null
  summary?: string | null
}

export interface FlightDynamics {
  approach_vector?: string | null
  exit_vector?: string | null
  pattern?: string | null
  altitude_min_m?: number | null
  altitude_max_m?: number | null
  altitude_confidence: number
  speed_estimate?: string | null
  maneuverability?: string | null
  duration_seconds?: number | null
  summary?: string | null
}

export interface OperatorHotspot {
  rank: number
  latitude: number
  longitude: number
  distance_to_target_m: number
  total_score: number
  cover_score: number
  distance_score: number
  exfil_score: number
  opsec_score: number
  terrain_score: number
  cover_type: string
  terrain_suitability: string
  nearest_road_type: string
  nearest_road_distance_m: number
  reasoning: string
}

export interface EvidenceSummary {
  total_items: number
  avg_credibility: number
  duplicates_removed: number
  official_reports_count: number
  news_articles_count: number
  social_media_count: number
  telegram_count: number
  youtube_count: number
  forum_posts_count: number
  witness_statements_count: number
  earliest_evidence?: string | null
  latest_evidence?: string | null
}

export interface EvidenceItem {
  source_id: string
  source_type: string
  source_name: string
  url?: string | null
  text_preview?: string | null
  language?: string | null
  published_at?: string | null
  credibility_score: number
  locality_score: number
  adversary_intent_score: number
}

export interface IntelligenceMeta {
  analyzed_at: string
  llm_mode: string
  llm_model?: string | null
  search_radius_m: number
  perimeter_radius_m: number
}

export interface IntelligenceResponse {
  incident: Incident
  drone_profile: DroneProfile
  flight_dynamics: FlightDynamics
  operator_hotspots: OperatorHotspot[]
  evidence_summary: EvidenceSummary
  evidence: EvidenceItem[]
  meta: IntelligenceMeta
}
