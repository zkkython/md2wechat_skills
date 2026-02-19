<template>
  <div class="app">
    <header class="header">
      <h1>MD2WeChat 批量发布工具</h1>
      <p class="subtitle">将 Markdown 文档批量发布到微信公众号草稿箱</p>
    </header>

    <main class="main">
      <div class="left-panel">
        <ConfigPanel v-model="config" />
      </div>

      <div class="right-panel">
        <FileUploader @files-selected="handleFilesSelected" />
        <FileList
          :files="files"
          @remove-file="removeFile"
          @clear-all="clearAll"
        />
        <UploadResults :results="results" v-if="results.length > 0" />
      </div>
    </main>

    <footer class="footer">
      <button
        class="upload-btn"
        :disabled="!canUpload"
        @click="startUpload"
      >
        <span v-if="uploading">
          <span class="spinner"></span>
          上传中 ({{ currentIndex + 1 }}/{{ files.length }})
        </span>
        <span v-else>
          开始批量上传
        </span>
      </button>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ConfigPanel from './components/ConfigPanel.vue'
import FileUploader from './components/FileUploader.vue'
import FileList from './components/FileList.vue'
import UploadResults from './components/UploadResults.vue'
import { uploadFile } from './api.js'

const files = ref([])
const uploading = ref(false)
const currentIndex = ref(0)
const results = ref([])

const config = ref({
  style: 'academic_gray',
  articleType: 'news',
  comment: false,
  fansOnlyComment: false,
  author: ''
})

const canUpload = computed(() => {
  return files.value.length > 0 && !uploading.value
})

const handleFilesSelected = (selectedFiles) => {
  const mdFiles = selectedFiles.filter(f => f.name.endsWith('.md') || f.name.endsWith('.markdown'))
  const existingNames = new Set(files.value.map(f => f.name))

  mdFiles.forEach(file => {
    if (!existingNames.has(file.name)) {
      files.value.push(file)
    }
  })
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const clearAll = () => {
  files.value = []
  results.value = []
}

const startUpload = async () => {
  if (files.value.length === 0) return

  uploading.value = true
  results.value = []
  currentIndex.value = 0

  for (let i = 0; i < files.value.length; i++) {
    currentIndex.value = i
    const file = files.value[i]

    try {
      const result = await uploadFile(file, config.value)
      results.value.push({
        fileName: file.name,
        success: result.success,
        mediaId: result.data?.media_id,
        error: result.error,
        code: result.code
      })
    } catch (err) {
      results.value.push({
        fileName: file.name,
        success: false,
        error: err.message
      })
    }
  }

  uploading.value = false
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: linear-gradient(135deg, #07c160 0%, #029f52 100%);
  color: white;
  padding: 24px;
  text-align: center;
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  margin-top: 8px;
  opacity: 0.9;
  font-size: 14px;
}

.main {
  flex: 1;
  display: flex;
  padding: 24px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.left-panel {
  width: 320px;
  flex-shrink: 0;
}

.right-panel {
  flex: 1;
  min-width: 0;
}

.footer {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: center;
}

.upload-btn {
  padding: 12px 48px;
  background: #07c160;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover:not(:disabled) {
  background: #06ad56;
}

.upload-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .main {
    flex-direction: column;
  }
  .left-panel {
    width: 100%;
  }
}
</style>
