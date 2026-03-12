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
    <input
      ref="folderInput"
      type="file"
      webkitdirectory
      @change="handleFolderChange"
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
        <span v-if="isDragOver">松开以上传文件或文件夹</span>
        <span v-else>点击选择 Markdown 文件，或拖拽文件/文件夹到此处</span>
      </p>
      <p class="sub-text">支持 .md 和 .markdown 格式</p>
      <button class="folder-btn" @click.stop="triggerFolderInput">
        <svg class="folder-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        选择文件夹（自动匹配图片）
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['files-selected'])
const fileInput = ref(null)
const folderInput = ref(null)
const isDragOver = ref(false)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const triggerFolderInput = () => {
  folderInput.value?.click()
}

const handleFileChange = (e) => {
  const files = Array.from(e.target.files || [])
  if (files.length > 0) {
    emit('files-selected', files)
    fileInput.value.value = ''
  }
}

const handleFolderChange = (e) => {
  const files = Array.from(e.target.files || [])
  if (files.length > 0) {
    // Files from webkitdirectory already have webkitRelativePath set
    emit('files-selected', files)
    folderInput.value.value = ''
  }
}

/**
 * Read all entries from a FileSystemDirectoryReader,
 * handling the batch-read limitation.
 */
const readAllEntries = (reader) => {
  return new Promise((resolve) => {
    const allEntries = []
    const readBatch = () => {
      reader.readEntries((entries) => {
        if (entries.length === 0) {
          resolve(allEntries)
        } else {
          allEntries.push(...entries)
          readBatch()
        }
      })
    }
    readBatch()
  })
}

/**
 * Recursively read a FileSystemEntry into a flat file list,
 * attaching _relativePath to each file.
 */
const readEntryRecursive = async (entry, basePath = '') => {
  if (entry.isFile) {
    return new Promise((resolve) => {
      entry.file((file) => {
        file._relativePath = basePath + file.name
        resolve([file])
      })
    })
  } else if (entry.isDirectory) {
    const reader = entry.createReader()
    const entries = await readAllEntries(reader)
    const allFiles = []
    for (const e of entries) {
      const files = await readEntryRecursive(e, basePath + entry.name + '/')
      allFiles.push(...files)
    }
    return allFiles
  }
  return []
}

const handleDrop = async (e) => {
  isDragOver.value = false
  const items = Array.from(e.dataTransfer.items || [])

  // Check if any dropped item is a directory
  let hasDirectory = false
  const entries = []
  for (const item of items) {
    const entry = item.webkitGetAsEntry?.()
    if (entry) {
      entries.push(entry)
      if (entry.isDirectory) hasDirectory = true
    }
  }

  if (hasDirectory) {
    // Recursively read all files from dropped directories/files
    const allFiles = []
    for (const entry of entries) {
      const files = await readEntryRecursive(entry)
      allFiles.push(...files)
    }
    if (allFiles.length > 0) {
      emit('files-selected', allFiles)
    }
  } else {
    // Regular file drop
    const files = Array.from(e.dataTransfer.files || [])
    if (files.length > 0) {
      emit('files-selected', files)
    }
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

.folder-btn {
  pointer-events: auto;
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}

.folder-btn:hover {
  background: #e8f5e9;
  border-color: #07c160;
  color: #07c160;
}

.folder-icon {
  width: 16px;
  height: 16px;
}
</style>
