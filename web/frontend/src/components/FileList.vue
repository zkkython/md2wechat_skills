<template>
  <div class="file-list" v-if="files.length > 0">
    <div class="list-header">
      <h4>待上传文件 ({{ files.length }})</h4>
      <button class="clear-btn" @click="$emit('clear-all')">清空全部</button>
    </div>

    <div class="files">
      <div v-for="(entry, index) in files" :key="entry.mdFile.name" class="file-entry">
        <div class="file-item">
          <div class="file-info">
            <span class="file-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </span>
            <span class="file-name">{{ entry.mdFile.name }}</span>
            <span class="file-size">{{ formatSize(entry.mdFile.size) }}</span>
            <span
              v-if="entry.requiredImages.length > 0"
              class="image-badge"
              :class="{ 'all-matched': matchedCount(entry) === entry.requiredImages.length }"
            >
              {{ matchedCount(entry) }}/{{ entry.requiredImages.length }} 图片已匹配
            </span>
          </div>
          <button class="remove-btn" @click="$emit('remove-file', index)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Image requirements section -->
        <div v-if="entry.requiredImages.length > 0" class="image-section">
          <div class="image-list">
            <div
              v-for="(img, imgIdx) in entry.requiredImages"
              :key="imgIdx"
              class="image-item"
              :class="{ matched: img.status === 'matched' }"
            >
              <span class="image-status-icon">{{ img.status === 'matched' ? '\u2713' : '\u2717' }}</span>
              <span class="image-name">{{ img.fileName }}</span>
              <span class="image-path">{{ img.relativePath }}</span>
            </div>
          </div>
          <label class="attach-btn">
            <input
              type="file"
              accept="image/*"
              multiple
              class="hidden-input"
              @change="onImagesSelected(index, $event)"
            />
            添加图片
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  files: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['remove-file', 'clear-all', 'images-attached'])

const matchedCount = (entry) => {
  return entry.requiredImages.filter(img => img.status === 'matched').length
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const onImagesSelected = (fileIndex, event) => {
  const imageFiles = Array.from(event.target.files)
  if (imageFiles.length > 0) {
    emit('images-attached', fileIndex, imageFiles)
  }
  // Reset input so user can re-select the same files
  event.target.value = ''
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

.file-entry {
  background: #f8f9fa;
  border-radius: 6px;
  overflow: hidden;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  transition: background 0.2s;
}

.file-entry:hover .file-item {
  background: #f0f0f0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
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

.image-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #fff3e0;
  color: #e65100;
  flex-shrink: 0;
  font-weight: 500;
}

.image-badge.all-matched {
  background: #e8f5e9;
  color: #2e7d32;
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

/* Image section */
.image-section {
  padding: 8px 12px 10px 40px;
  border-top: 1px dashed #e0e0e0;
}

.image-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.image-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.image-item.matched {
  color: #2e7d32;
}

.image-status-icon {
  font-size: 13px;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.image-item:not(.matched) .image-status-icon {
  color: #e65100;
}

.image-name {
  font-weight: 500;
  flex-shrink: 0;
}

.image-path {
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attach-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #1976d2;
  cursor: pointer;
  padding: 4px 10px;
  border: 1px dashed #1976d2;
  border-radius: 4px;
  transition: all 0.2s;
}

.attach-btn:hover {
  background: #e3f2fd;
}

.hidden-input {
  display: none;
}
</style>
