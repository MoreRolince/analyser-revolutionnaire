"use client"

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Search, Loader2, Download, TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, XCircle, BarChart3, DollarSign, Package, Store, Target, Zap, ExternalLink } from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface AnalysisResult {
  type: 'shop' | 'product'
  score: number
  data: any
  aiInsights?: string
}

export default function AnalysePage() {
  const router = useRouter()
  const { toast } = useToast()
  const searchParams = useSearchParams()
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [jobId, setJobId] = useState<string | null>(null)
  const [polling, setPolling] = useState(false)
  const [partialProducts, setPartialProducts] = useState<any[]>([])

  // Vérifier l'authentification au chargement
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      
      if (!token) {
        router.push('/auth/login')
        return
      }

      try {
        // Vérifier que le token est valide
        await api.get('/users/me')
        setIsAuthenticated(true)
      } catch (error) {
        // Token invalide ou expiré
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/auth/login')
      } finally {
        setCheckingAuth(false)
      }
    }

    checkAuth()
  }, [router])

  // Détecter l'URL depuis les query params et lancer l'analyse automatiquement
  // ATTENTION: Ne lancer l'analyse que si l'utilisateur est authentifié
  useEffect(() => {
    if (!isAuthenticated || checkingAuth) return
    
    const urlParam = searchParams.get('url')
    if (urlParam) {
      setUrl(decodeURIComponent(urlParam))
      // Lancer l'analyse automatiquement après un court délai
      setTimeout(() => {
        handleAnalyze(decodeURIComponent(urlParam))
      }, 500)
    }
  }, [searchParams, isAuthenticated, checkingAuth])

  const handleAnalyze = async (urlToAnalyze?: string) => {
    const urlToUse = urlToAnalyze || url.trim()
    
    if (!urlToUse) {
      toast({
        title: 'Erreur',
        description: 'Veuillez entrer une URL',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    setResult(null)
    setPartialProducts([])
    setJobId(null)
    setPolling(false)

    try {
      const response = await api.post('/analyse', { url: urlToUse })
      const data = response.data
      
      // Si le backend retourne un job_id, on démarre le polling
      if (data.job_id) {
        setJobId(data.job_id)
        setPolling(true)
        toast({
          title: 'Analyse démarrée',
          description: 'Les produits seront affichés progressivement...',
        })
        // Démarrer le polling
        startPolling(data.job_id)
      } else {
        // Pas de job_id, résultat immédiat (produits)
        setResult(data)
        toast({
          title: 'Analyse terminée',
          description: 'Votre analyse est prête !',
        })
        setLoading(false)
      }
    } catch (error: any) {
      console.error('Erreur analyse:', error)
      let errorMessage = 'Une erreur est survenue lors de l\'analyse'
      
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        errorMessage = 'Impossible de contacter le serveur. Vérifiez que le backend est démarré.'
      } else if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join(', ')
        } else if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else {
          errorMessage = JSON.stringify(error.response.data.detail)
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive',
      })
      setLoading(false)
      setPolling(false)
    }
  }

  const startPolling = async (jobId: string) => {
    let pollInterval: NodeJS.Timeout | null = null
    
    const poll = async () => {
      try {
        const response = await api.get(`/analyse/jobs/${jobId}`)
        const jobStatus = response.data
        
        // Afficher les produits partiels au fur et à mesure
        if (jobStatus.partial_result && jobStatus.partial_result.products) {
          setPartialProducts(jobStatus.partial_result.products)
        }
        
        // Si terminé, arrêter le polling et afficher le résultat final
        if (jobStatus.status === 'completed') {
          if (pollInterval) clearInterval(pollInterval)
          setPolling(false)
          setLoading(false)
          
          if (jobStatus.result) {
            // Vérifier si le résultat contient une erreur
            if (jobStatus.result.status === 'error' || jobStatus.result.error) {
              // Gérer les erreurs dans le résultat
              if (pollInterval) clearInterval(pollInterval)
              setPolling(false)
              setLoading(false)
              toast({
                title: 'Information',
                description: jobStatus.result.error || 'L\'analyse n\'a pas pu être effectuée',
                variant: 'destructive',
              })
              return
            }
            
            // Construire le résultat final au format AnalysisResult
            setResult({
              type: jobStatus.result.type || 'shop',
              score: jobStatus.result.score || 0,
              data: {
                ...jobStatus.result,
                products: jobStatus.result.products || []
              },
              ai_insights: `Analyse terminée: ${jobStatus.result.productCount || 0} produits trouvés`
            })
            
            toast({
              title: 'Analyse terminée',
              description: `${jobStatus.result.productCount || 0} produits analysés !`,
            })
          }
        } else if (jobStatus.status === 'failed') {
          if (pollInterval) clearInterval(pollInterval)
          setPolling(false)
          setLoading(false)
          toast({
            title: 'Erreur',
            description: jobStatus.error || 'L\'analyse a échoué',
            variant: 'destructive',
          })
        }
      } catch (error: any) {
        console.error('Erreur polling:', error)
        if (pollInterval) clearInterval(pollInterval)
        setPolling(false)
        setLoading(false)
      }
    }
    
    // Poller immédiatement puis toutes les 2 secondes
    await poll()
    pollInterval = setInterval(poll, 2000)
  }

  const handleExport = () => {
    if (!result) return
    
    const dataStr = JSON.stringify(result.data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analyse-${Date.now()}.json`
    link.click()
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600'
    if (score >= 75) return 'text-yellow-600'
    if (score >= 65) return 'text-orange-600'
    return 'text-red-600'
  }

  const getScoreBadge = (score: number) => {
    if (score >= 85) return { text: 'Excellent', color: 'bg-green-50 text-green-700 border-green-300' }
    if (score >= 75) return { text: 'Bon', color: 'bg-yellow-50 text-yellow-700 border-yellow-300' }
    if (score >= 65) return { text: 'Moyen', color: 'bg-orange-50 text-orange-700 border-orange-300' }
    return { text: 'Faible', color: 'bg-red-50 text-red-700 border-red-300' }
  }

  const getTrendIcon = (trend: string) => {
    if (trend?.toLowerCase().includes('montée')) return <TrendingUp className="h-5 w-5 text-green-600" />
    if (trend?.toLowerCase().includes('chute')) return <TrendingDown className="h-5 w-5 text-red-600" />
    return <Minus className="h-5 w-5 text-gray-400" />
  }

  if (checkingAuth) {
    return (
      <DashboardLayout>
        <div className="p-6 flex items-center justify-center min-h-[400px] bg-white">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-900" />
            <p className="text-gray-600">Vérification de l'authentification...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null // La redirection est gérée par useEffect
  }

  return (
    <DashboardLayout>
    <div className="p-6 md:p-8 space-y-6 bg-white">
      <div>
        <h1 className="text-3xl md:text-4xl font-black text-gray-900 tracking-tight mb-2 flex items-center gap-3">
          <Search className="h-7 w-7 md:h-8 md:w-8 text-gray-900" />
          Analyser une URL
        </h1>
        <p className="text-gray-600 text-base">
          Analysez une boutique ou un produit depuis CHARIOW, Maketou, System.io ou toute autre URL
        </p>
      </div>

      <Card className="!bg-gradient-to-br !from-white !to-gray-50 !border-gray-200 !text-gray-900 rounded-2xl shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="!text-gray-900 font-bold">Nouvelle Analyse</CardTitle>
          <CardDescription className="!text-gray-600">Collez l'URL de la boutique ou du produit à analyser</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="https://chariow.com/boutique/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 rounded-xl"
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <Button 
              onClick={() => handleAnalyze()} 
              disabled={loading}
              className="h-12 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold px-6"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Analyser
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Affichage des produits partiels pendant le polling */}
      {polling && partialProducts.length > 0 && (
        <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="!text-gray-900 font-bold">Produits trouvés ({partialProducts.length})</CardTitle>
            <CardDescription className="!text-gray-600">Les produits sont affichés au fur et à mesure de leur découverte...</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {partialProducts.map((product: any, idx: number) => (
                <div key={idx} className="p-4 border border-gray-200 rounded-xl bg-gray-50">
                  <h4 className="font-semibold text-gray-900 mb-2 line-clamp-2">{product.product_title || product.title || 'Produit'}</h4>
                  {product.images && product.images[0] && (
                    <img src={product.images[0]} alt={product.product_title} className="w-full h-32 object-cover rounded-lg mb-2" />
                  )}
                  {product.price && (
                    <p className="text-lg font-bold text-gray-900">{product.price.toLocaleString()} FCFA</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm">
          <CardContent className="py-16 text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-gray-900" />
            <p className="text-lg font-bold text-gray-900">Analyse en cours...</p>
            <p className="text-sm text-gray-600 mt-2">
              {polling ? `Scraping des produits... (${partialProducts.length} trouvés)` : 'Scraping des données et génération de l\'analyse...'}
            </p>
            {polling && partialProducts.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">Les produits s'affichent progressivement ci-dessous</p>
            )}
          </CardContent>
        </Card>
      )}

      {result && (
        <div className="space-y-6">
          {/* Header avec Score */}
          <Card className="!bg-gradient-to-br !from-white !to-gray-50 !border-gray-200 !text-gray-900 rounded-2xl shadow-sm">
            <CardHeader>
              <div className="flex flex-col md:flex-row justify-between items-start gap-6">
                <div className="flex-1">
                  {/* Image du produit si disponible */}
                  {result.type === 'product' && result.data.productImage && (
                    <div className="mb-6">
                      <img 
                        src={result.data.productImage} 
                        alt={result.data.productName || 'Produit'}
                        className="w-full max-w-md h-64 object-cover rounded-xl border border-gray-200"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none'
                        }}
                      />
                    </div>
                  )}
                  
                  <div className="flex items-center gap-3 mb-4">
                    {result.type === 'shop' ? (
                      <Store className="h-8 w-8 text-gray-700" />
                    ) : (
                      <Package className="h-8 w-8 text-gray-700" />
                    )}
                    <div>
                      <CardTitle className="text-2xl md:text-3xl font-black text-gray-900">
                        {result.type === 'product' && result.data.productName 
                          ? result.data.productName 
                          : `Analyse ${result.type === 'shop' ? 'Boutique' : 'Produit'}`}
                      </CardTitle>
                      <CardDescription className="text-base mt-1 text-gray-600">
                        {result.data.marketplace || 'Marketplace'}
                      </CardDescription>
                    </div>
                  </div>
                  
                  {/* Description du produit */}
                  {result.type === 'product' && result.data.productDescription && (
                    <div className="mt-4 p-4 rounded-xl bg-gray-50 border border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-2">Description :</p>
                      <p className="text-base text-gray-900 leading-relaxed">{result.data.productDescription}</p>
                      {result.data.url && (
                        <a 
                          href={result.data.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-gray-900 hover:text-gray-700 hover:underline inline-flex items-center gap-1 mt-3 text-sm font-medium"
                        >
                          Voir le produit sur le marketplace <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  )}
                </div>
                <div className="text-right flex-shrink-0">
                  <div className={`text-5xl md:text-6xl font-black mb-2 ${getScoreColor(result.score)}`}>
                    {Math.round(result.score)}
                  </div>
                  <div className={`px-4 py-1.5 rounded-full border-2 text-sm font-semibold ${getScoreBadge(result.score).color}`}>
                    {getScoreBadge(result.score).text}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Score / 100</p>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Métriques principales */}
          {result.type === 'shop' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">CA Mensuel Estimé</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.estimatedRevenue || 'N/A'}</p>
                    </div>
                    <DollarSign className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Ventes Mensuelles</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.estimatedSales || 'N/A'}</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Nombre de Produits</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.productCount || 'N/A'}</p>
                    </div>
                    <Package className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Ancienneté</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.age || 'N/A'}</p>
                    </div>
                    <Target className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {result.type === 'product' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Ventes/Jour Estimées</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.estimatedDailySales || 'N/A'}</p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Prix Idéal</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.idealPrice || 'N/A'}</p>
                    </div>
                    <DollarSign className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Niveau Concurrence</p>
                      <p className="text-2xl font-black text-gray-900">{result.data.competitionLevel || 'N/A'}</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:border-gray-300">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 font-medium mb-1">Tendance</p>
                      <div className="flex items-center gap-2">
                        {getTrendIcon(result.data.trend)}
                        <p className="text-2xl font-black text-gray-900">{result.data.trend || 'N/A'}</p>
                      </div>
                    </div>
                    <Zap className="h-8 w-8 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Points Forts / Faibles */}
          {result.type === 'shop' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.data.strengths && result.data.strengths.length > 0 && (
                <Card className="!bg-white !border-green-200 !text-gray-900 rounded-2xl shadow-sm border-2">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 !text-green-700 font-bold">
                      <CheckCircle className="h-5 w-5" />
                      Points Forts
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {result.data.strengths.map((strength: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-3">
                          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-900 leading-relaxed">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {result.data.weaknesses && result.data.weaknesses.length > 0 && (
                <Card className="!bg-white !border-red-200 !text-gray-900 rounded-2xl shadow-sm border-2">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 !text-red-700 font-bold">
                      <XCircle className="h-5 w-5" />
                      Points Faibles
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {result.data.weaknesses.map((weakness: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-3">
                          <XCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-900 leading-relaxed">{weakness}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Risques pour produits */}
          {result.type === 'product' && result.data.risks && result.data.risks.length > 0 && (
            <Card className="!bg-white !border-orange-200 !text-gray-900 rounded-2xl shadow-sm border-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 !text-orange-700 font-bold">
                  <AlertTriangle className="h-5 w-5" />
                  Risques Identifiés
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {result.data.risks.map((risk: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3">
                      <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-900 leading-relaxed">{risk}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Insights IA */}
          {result.aiInsights && (
            <Card className="bg-gradient-to-br from-white to-gray-50 border-2 border-gray-300 rounded-2xl shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
                  <Zap className="h-5 w-5 text-gray-700" />
                  Insights IA Stratégiques
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-base text-gray-900 leading-relaxed whitespace-pre-wrap">{result.aiInsights}</p>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <Card className="!bg-white !border-gray-200 !text-gray-900 rounded-2xl shadow-sm">
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  onClick={handleExport} 
                  className="flex-1 bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-900 rounded-xl font-semibold h-12"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Exporter en JSON
                </Button>
                {result.data.url && (
                  <Button 
                    asChild 
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-12"
                  >
                    <a href={result.data.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Voir sur le Marketplace
                    </a>
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
    </DashboardLayout>
  )
}
