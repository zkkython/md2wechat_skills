<template>
  <div class="file-list" v-if="files.length > 0">
    <div class="list-header">
      <h4>待上传文件 ({{ files.length }})</h4>
      <button class="clear-btn" @click="$emit('clear-all')">清空全部</button>
    </div>

    <div class="files">
      <div v-for="(file, index) in files" :key="file.name" class="file-item">
        <div class="file-info">
          <span class="file-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </span>
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ formatSize(file.size) }}</span>
        </div>
        <button class="remove-btn" @click="$emit('remove-file', index)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  files: {
    type: Array,
    required: true
  }
})

defineEmits(['remove-file', 'clear-all'])

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.file-list {
  margin-top: 16px;
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.list-header h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.clear-btn {
  font-size: 12px;
  color: #f44336;
  background: none;
  border: none;
  cursor: pointer;
}

.clear-btn:hover {
  text-decoration: underline;
}

.files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: background 0.2s;
}

.file-item:hover {
  background: #f0f0f0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.file-icon {
  width: 18px;
  height: 18px;
  color: #07c160;
  flex-shrink: 0;
}

.file-icon svg {
  width: 100%;
  height: 100%;
}

.file-name {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: #999;
  flex-shrink: 0;
}

.remove-btn {
  width: 24px;
  height: 24px;
  padding: 4px;
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  border-radius: 4px;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: #ffeaea;
  color: #f44336;
}

.remove-btn svg {
  width: 100%;
  height: 100%;
}
</style>
