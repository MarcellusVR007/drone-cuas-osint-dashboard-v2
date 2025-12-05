<template>
  <div class="card">
    <h2>Evidence & Sources</h2>

    <!-- Summary statistics -->
    <div class="evidence-summary">
      <div class="summary-stat">
        <strong>Total Items:</strong> {{ summary.total_items }}
      </div>
      <div class="summary-stat">
        <strong>Avg Credibility:</strong> {{ (summary.avg_credibility * 100).toFixed(0) }}%
      </div>
      <div class="summary-stat">
        <strong>Duplicates Removed:</strong> {{ summary.duplicates_removed }}
      </div>
    </div>

    <!-- Channel breakdown -->
    <div class="channel-breakdown">
      <span v-if="summary.official_reports_count > 0" class="channel-tag">
        Official Reports: {{ summary.official_reports_count }}
      </span>
      <span v-if="summary.news_articles_count > 0" class="channel-tag">
        News: {{ summary.news_articles_count }}
      </span>
      <span v-if="summary.social_media_count > 0" class="channel-tag">
        Social Media: {{ summary.social_media_count }}
      </span>
      <span v-if="summary.telegram_count > 0" class="channel-tag">
        Telegram: {{ summary.telegram_count }}
      </span>
      <span v-if="summary.youtube_count > 0" class="channel-tag">
        YouTube: {{ summary.youtube_count }}
      </span>
      <span v-if="summary.forum_posts_count > 0" class="channel-tag">
        Forums: {{ summary.forum_posts_count }}
      </span>
      <span v-if="summary.witness_statements_count > 0" class="channel-tag">
        Witnesses: {{ summary.witness_statements_count }}
      </span>
    </div>

    <!-- Evidence items table -->
    <table v-if="items.length > 0">
      <thead>
        <tr>
          <th>Type</th>
          <th>Source</th>
          <th>Preview</th>
          <th>Credibility</th>
          <th>Locality</th>
          <th>Published</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(item, index) in items" :key="item.source_id">
          <tr
            @click="expandedIndex === index ? collapseRow() : expandRow(index)"
            class="evidence-row"
          >
            <td>
              <span class="channel-badge" :class="`channel-${item.source_type}`">
                {{ formatSourceType(item.source_type) }}
              </span>
            </td>
            <td>{{ item.source_name }}</td>
            <td class="text-preview">{{ item.text_preview || '(no preview)' }}</td>
            <td>
              <div class="score-bar">
                <div
                  class="score-bar-fill"
                  :style="{ width: `${item.credibility_score * 100}%` }"
                ></div>
              </div>
              <span class="score-text">{{ (item.credibility_score * 100).toFixed(0) }}%</span>
            </td>
            <td>
              <div class="score-bar">
                <div
                  class="score-bar-fill"
                  :style="{ width: `${item.locality_score * 100}%` }"
                ></div>
              </div>
              <span class="score-text">{{ (item.locality_score * 100).toFixed(0) }}%</span>
            </td>
            <td>{{ formatDate(item.published_at) }}</td>
            <td>
              <button class="btn-expand">
                {{ expandedIndex === index ? '▲' : '▼' }}
              </button>
            </td>
          </tr>
          <tr v-if="expandedIndex === index" class="evidence-details">
            <td colspan="7">
              <div class="details-content">
                <div v-if="item.text_preview" class="detail-section">
                  <h4>Full Text:</h4>
                  <p>{{ item.text_preview }}</p>
                </div>

                <div v-if="item.url" class="detail-section">
                  <h4>URL:</h4>
                  <a :href="item.url" target="_blank" rel="noopener">{{ item.url }}</a>
                </div>

                <div v-if="item.language" class="detail-section">
                  <h4>Language:</h4>
                  <p>{{ item.language.toUpperCase() }}</p>
                </div>

                <div class="detail-section">
                  <h4>Adversary Intent Score:</h4>
                  <p>{{ (item.adversary_intent_score * 100).toFixed(0) }}%</p>
                </div>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <div v-else class="no-evidence">
      No evidence items available.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { EvidenceSummary, EvidenceItem } from '@/api/types'

defineProps<{
  summary: EvidenceSummary
  items: EvidenceItem[]
}>()

const expandedIndex = ref<number | null>(null)

const expandRow = (index: number) => {
  expandedIndex.value = index
}

const collapseRow = () => {
  expandedIndex.value = null
}

const formatSourceType = (type: string): string => {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

const formatDate = (dateStr?: string | null): string => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch {
    return dateStr
  }
}
</script>

<style scoped>
.evidence-summary {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.summary-stat {
  font-size: 0.9rem;
  color: #555;
}

.channel-breakdown {
  margin-bottom: 1rem;
}

.channel-tag {
  display: inline-block;
  padding: 0.5rem 0.75rem;
  background: #e8e8e8;
  border-radius: 4px;
  font-size: 0.85rem;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.channel-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.channel-verified_news,
.channel-local_news {
  background: #34a853;
  color: white;
}

.channel-social_media_verified,
.channel-social_media_unverified {
  background: #1da1f2;
  color: white;
}

.channel-telegram_channel {
  background: #0088cc;
  color: white;
}

.channel-forum_post {
  background: #ff9800;
  color: white;
}

.channel-youtube_video {
  background: #ff0000;
  color: white;
}

.channel-official_report {
  background: #6b46c1;
  color: white;
}

.channel-witness_statement {
  background: #2c5282;
  color: white;
}

.text-preview {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-row {
  cursor: pointer;
  transition: background 0.2s;
}

.evidence-row:hover {
  background: #f5f5f5;
}

.score-bar {
  height: 6px;
  background: #eee;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 2px;
}

.score-bar-fill {
  height: 100%;
  background: linear-gradient(to right, #e74c3c, #27ae60);
  transition: width 0.3s;
}

.score-text {
  font-size: 0.8rem;
  color: #666;
}

.btn-expand {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  color: #555;
}

.evidence-details {
  background: #fafafa;
}

.details-content {
  padding: 1.5rem;
}

.detail-section {
  margin-bottom: 1.5rem;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-section p {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

.detail-section a {
  color: #e74c3c;
  text-decoration: none;
}

.detail-section a:hover {
  text-decoration: underline;
}

.no-evidence {
  text-align: center;
  padding: 2rem;
  color: #888;
}
</style>
