import axios from 'axios'

const API_BASE = '/api'

export const uploadFile = async (file, config) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('style', config.style)
  formData.append('article_type', config.articleType)
  formData.append('comment', config.comment)
  formData.append('fans_only_comment', config.fansOnlyComment)
  formData.append('author', config.author)

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
