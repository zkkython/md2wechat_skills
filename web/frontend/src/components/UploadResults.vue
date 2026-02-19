<template>
  <div class="results">
    <h4 class="results-title">上传结果</h4>

    <div class="summary">
      <span class="success-count">成功: {{ successCount }}</span>
      <span class="fail-count">失败: {{ failCount }}</span>
    </div>

    <div class="result-list">
      <div
        v-for="(result, index) in results"
        :key="index"
        class="result-item"
        :class="{ success: result.success, failed: !result.success }"
      >
        <div class="result-status">
          <span v-if="result.success" class="status-icon success">✓</span>
          <span v-else class="status-icon failed">✗</span>
        </div>

        <div class="result-info">
          <div class="result-file">{{ result.fileName }}</div>
          <div v-if="result.success" class="result-detail">
            Media ID: <code>{{ result.mediaId }}</code>
          </div>
          <div v-else class="result-error">
            {{ result.error }}
            <span v-if="result.code" class="error-code">({{ result.code }})</span>
          </div>
        </div>
      </div>
    </div>

    <div class="actions" v-if="failCount > 0">
      <button class="retry-btn" @click="retryFailed">重试失败项</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  results: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['retry-failed'])

const successCount = computed(() => props.results.filter(r => r.success).length)
const failCount = computed(() => props.results.filter(r => !r.success).length)

const retryFailed = () => {
  emit('retry-failed')
}
</script>

<style scoped>
.results {
  margin-top: 16px;
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.results-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.summary {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.success-count {
  color: #07c160;
  font-weight: 500;
}

.fail-count {
  color: #f44336;
  font-weight: 500;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  background: #f8f9fa;
}

.result-item.success {
  background: #f0faf4;
  border-left: 3px solid #07c160;
}

.result-item.failed {
  background: #fff5f5;
  border-left: 3px solid #f44336;
}

.status-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
}

.status-icon.success {
  background: #07c160;
  color: white;
}

.status-icon.failed {
  background: #f44336;
  color: white;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-file {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  word-break: break-all;
}

.result-detail {
  font-size: 12px;
  color: #666;
}

.result-detail code {
  background: #e8e8e8;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

.result-error {
  font-size: 12px;
  color: #f44336;
}

.error-code {
  color: #999;
}

.actions {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.retry-btn {
  padding: 8px 20px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #d32f2f;
}
</style>
