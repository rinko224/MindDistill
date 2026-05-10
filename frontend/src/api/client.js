import axios from 'axios'

const client = axios.create({
  baseURL: '',
  timeout: 60000,
})

client.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.error || err.message || '请求失败'
    return Promise.reject(msg)
  }
)

export default client

export const uploadFile = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/api/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const listBooks = () => client.get('/api/upload/')
export const deleteBook = (bookId) => client.delete(`/api/upload/${bookId}`)
export const parseBook = (bookId) => client.post(`/api/parse/${bookId}`)
export const getParseStatus = (bookId) => client.get(`/api/parse/${bookId}/status`)

export const buildGraph = (bookId) => client.post(`/api/graph/build/${bookId}`)
export const getGraph = (bookId) => client.get(`/api/graph/${bookId}`)
export const getMergedGraph = () => client.get('/api/graph/merged')

export const runMerge = () => client.post('/api/merge/')
export const getMergeDecisions = () => client.get('/api/merge/decisions')
export const getMergeResult = () => client.get('/api/merge/result')

export const indexRAG = () => client.post('/api/rag/index')
export const queryRAG = (question, topK = 5) => client.post('/api/rag/query', { question, top_k: topK })
export const getRAGStatus = () => client.get('/api/rag/status')
export const resetRAGIndex = () => client.post('/api/rag/reset')
export const runRAGBenchmark = () => client.post('/api/rag/benchmark', {}, { timeout: 180000 })

export const sendChat = (messages) => client.post('/api/chat/', { messages })

export const generateReport = () => client.post('/api/report/generate')
