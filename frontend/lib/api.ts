import axios from 'axios'

// Configuration de l'URL de l'API
// En développement, utiliser localhost:8000 (port du backend FastAPI)
// En production, utiliser la variable d'environnement NEXT_PUBLIC_API_URL
export const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // Côté client, vérifier les variables d'environnement
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
  // Côté serveur
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

const API_URL = getApiUrl()

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 180 secondes pour couvrir scraping multi-pages volumineux
})

// Log de la configuration en développement
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('API Configuration:', {
    baseURL: `${API_URL}/api/v1`,
    apiUrl: API_URL
  })
}

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log des erreurs pour le débogage
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      console.error('API Error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        baseURL: error.config?.baseURL
      })
    }
    
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api

