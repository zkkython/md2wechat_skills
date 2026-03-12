import axios from 'axios'

const API_BASE = '/api'

export const uploadFile = async (mdFile, requiredImages, config) => {
  const formData = new FormData()
  formData.append('file', mdFile)
  formData.append('style', config.style)
  formData.append('article_type', config.articleType)
  formData.append('comment', config.comment)
  formData.append('fans_only_comment', config.fansOnlyComment)
  formData.append('author', config.author)

  // Collect matched images and their relative paths
  const matchedImages = (requiredImages || []).filter(img => img.status === 'matched' && img.matchedFile)
  if (matchedImages.length > 0) {
    const paths = []
    for (const img of matchedImages) {
      formData.append('images', img.matchedFile)
      paths.push(img.relativePath)
    }
    formData.append('image_paths', JSON.stringify(paths))
  }

  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 120000
  })

  return response.data
}

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE}/health`)
  return response.data
}
