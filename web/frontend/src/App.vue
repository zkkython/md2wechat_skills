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
          @images-attached="handleImagesAttached"
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

/**
 * Extract local image references from markdown content.
 * Filters out http/https URLs, returns only relative paths.
 */
const extractImages = (mdContent) => {
  const regex = /!\[[^\]]*\]\(([^)]+)\)/g
  const images = []
  let match
  while ((match = regex.exec(mdContent)) !== null) {
    const imgPath = match[1]
    // Skip remote URLs
    if (/^https?:\/\//i.test(imgPath)) continue
    // Skip data URIs
    if (imgPath.startsWith('data:')) continue
    const fileName = imgPath.split('/').pop()
    images.push({
      relativePath: imgPath,
      fileName,
      matchedFile: null,
      status: 'missing'
    })
  }
  return images
}

/**
 * Read a File as text and return a Promise.
 */
const readFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })
}

/**
 * Get the relative path of a file (from folder selection or drag-and-drop).
 */
const getRelativePath = (file) => file.webkitRelativePath || file._relativePath || ''

/**
 * Check if file is an image by extension.
 */
const isImageFile = (file) => /\.(png|jpe?g|gif|bmp|webp|svg|ico|tiff?)$/i.test(file.name)

const handleFilesSelected = async (selectedFiles) => {
  const allFiles = Array.from(selectedFiles)
  const mdFiles = allFiles.filter(f => f.name.endsWith('.md') || f.name.endsWith('.markdown'))
  const imageFiles = allFiles.filter(f => isImageFile(f))

  // Detect folder mode: files have relative path info
  const isFolderMode = allFiles.some(f => getRelativePath(f).includes('/'))

  const existingNames = new Set(files.value.map(f => f.mdFile.name))

  for (const file of mdFiles) {
    if (existingNames.has(file.name)) continue
    const content = await readFileAsText(file)
    const requiredImages = extractImages(content)

    // In folder mode, auto-match images by resolving relative paths
    if (isFolderMode && requiredImages.length > 0 && imageFiles.length > 0) {
      const mdRelPath = getRelativePath(file)
      // Get directory of the md file: "project/sub/README.md" -> "project/sub"
      const mdDir = mdRelPath.includes('/') ? mdRelPath.substring(0, mdRelPath.lastIndexOf('/')) : ''
      const prefix = mdDir ? mdDir + '/' : ''

      // Build a lookup map from relative path -> File for all image files
      const imagePathMap = new Map()
      for (const img of imageFiles) {
        imagePathMap.set(getRelativePath(img), img)
      }

      for (const req of requiredImages) {
        // Resolve: md dir + image relative path
        const expectedPath = prefix + req.relativePath
        const matched = imagePathMap.get(expectedPath)
        if (matched) {
          req.matchedFile = matched
          req.status = 'matched'
        }
      }

      // Fallback: match remaining by filename
      const usedFiles = new Set(requiredImages.filter(r => r.status === 'matched').map(r => r.matchedFile))
      for (const req of requiredImages) {
        if (req.status === 'matched') continue
        const matched = imageFiles.find(f => f.name === req.fileName && !usedFiles.has(f))
        if (matched) {
          req.matchedFile = matched
          req.status = 'matched'
          usedFiles.add(matched)
        }
      }
    }

    files.value.push({
      mdFile: file,
      requiredImages
    })
  }
}

const handleImagesAttached = (fileIndex, imageFiles) => {
  const entry = files.value[fileIndex]
  if (!entry) return

  for (const imgFile of imageFiles) {
    // Match by filename
    for (const req of entry.requiredImages) {
      if (req.status === 'matched') continue
      if (req.fileName === imgFile.name) {
        req.matchedFile = imgFile
        req.status = 'matched'
        break
      }
    }
  }
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
    const entry = files.value[i]

    try {
      const result = await uploadFile(entry.mdFile, entry.requiredImages, config.value)
      results.value.push({
        fileName: entry.mdFile.name,
        success: result.success,
        mediaId: result.data?.media_id,
        error: result.error,
        code: result.code
      })
    } catch (err) {
      results.value.push({
        fileName: entry.mdFile.name,
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
