<template>
  <div
    class="uploader"
    :class="{ dragover: isDragOver }"
    @click="triggerFileInput"
    @dragenter.prevent="isDragOver = true"
    @dragleave.prevent="isDragOver = false"
    @dragover.prevent
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".md,.markdown"
      multiple
      @change="handleFileChange"
      hidden
    />

    <div class="uploader-content">
      <div class="icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>
      <p class="main-text">
        <span v-if="isDragOver">松开以上传文件</span>
        <span v-else>点击或拖拽 Markdown 文件到此处</span>
      </p>
      <p class="sub-text">支持 .md 和 .markdown 格式</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['files-selected'])
const fileInput = ref(null)
const isDragOver = ref(false)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = (e) => {
  const files = Array.from(e.target.files || [])
  if (files.length > 0) {
    emit('files-selected', files)
    fileInput.value.value = ''
  }
}

const handleDrop = (e) => {
  isDragOver.value = false
  const files = Array.from(e.dataTransfer.files || [])
  if (files.length > 0) {
    emit('files-selected', files)
  }
}
</script>

<style scoped>
.uploader {
  background: white;
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.uploader:hover {
  border-color: #07c160;
}

.uploader.dragover {
  border-color: #07c160;
  background: #f0faf4;
}

.uploader-content {
  pointer-events: none;
}

.icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #999;
}

.icon svg {
  width: 100%;
  height: 100%;
}

.uploader:hover .icon,
.uploader.dragover .icon {
  color: #07c160;
}

.main-text {
  font-size: 16px;
  color: #333;
  margin-bottom: 8px;
}

.sub-text {
  font-size: 13px;
  color: #999;
}
</style>
