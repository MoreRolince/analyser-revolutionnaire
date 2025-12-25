"use client"

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  TrendingUp, 
  Store, 
  Zap, 
  BarChart3, 
  Search, 
  Star, 
  Trophy,
  Package,
  ExternalLink,
  ArrowUp,
  ArrowDown,
  Filter,
  Download,
  Target,
  X,
  ChevronDown
} from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency, formatNumber } from '@/lib/utils'
import { User } from '@/lib/auth'

interface MarketInsights {
  topProducts: Array<{
    id: number
    product_name: string
    product_url?: string
    product_image?: string
    score_winner: number
    marketplace: string
    price?: number
    revenue_est_min?: number
    revenue_est_max?: number
    shop_name?: string
    category?: string
    last_scraped_at?: string
  }>
  topShops: Array<{
    id: number
    shop_name: string
    shop_url?: string
    score_global: number
    marketplace: string
    revenue_est_min?: number
    revenue_est_max?: number
  }>
}

interface DashboardStats {
  market_opportunity_score: number
  remaining_analyses: number
  tracked_shops: number
  trending_products: Array<{
    id: number
    name: string
    score: number
    marketplace: string
  }>
  daily_recommendation: string
  market_stats: {
    total_shops: number
    total_products: number
    top_shops: Array<{
      id: number
      name: string
      score: number
      marketplace: string
    }>
    top_products: Array<{
      id: number
      name: string
      score: number
      marketplace: string
    }>
  }
}

type PresetFilter = 'recommandé' | 'top-facebook' | 'nouvelles-boutiques' | 'grosses-ventes' | 'forte-croissance' | null
type SortOption = 'recommandé' | 'score-desc' | 'score-asc' | 'prix-desc' | 'prix-asc' | 'revenu-desc' | 'revenu-asc'

interface FilterState {
  priceMin?: number
  priceMax?: number
  marketplace?: string
  category?: string
  minScore?: number
  minRevenue?: number
}

export default function DashboardContent({ user }: { user: User }) {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [insights, setInsights] = useState<MarketInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [presetFilter, setPresetFilter] = useState<PresetFilter>('recommandé')
  const [sortOption, setSortOption] = useState<SortOption>('recommandé')
  const [filters, setFilters] = useState<FilterState>({})
  const [showFilterDialog, setShowFilterDialog] = useState<string | null>(null)
  const [allProducts, setAllProducts] = useState<any[]>([])

  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        fetchDashboardStats(),
        fetchInsights()
      ])
    }
    loadData()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      const response = await api.get('/dashboard/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchInsights = async () => {
    try {
      const [productsRes, shopsRes] = await Promise.all([
        api.get('/winners/products?limit=500'),
        api.get('/winners/shops?limit=10')
      ])
      
      const products = productsRes.data || []
      const shops = shopsRes.data || []
      
      // Filtres moins stricts : on garde les produits qui ont au moins un nom et une URL
      const realProducts = products.filter((p: any) => {
        // Exclure uniquement les exemples explicites
        const name = (p.product_name || '').toLowerCase()
        if (name.includes('exemple') || name.includes('produit winner exemple') || name.includes('test') || name.includes('demo')) {
          return false
        }
        
        // Au minimum, il faut un nom ET une URL pour afficher le produit
        const hasName = p.product_name && p.product_name.trim() !== ''
        const hasUrl = p.product_url && p.product_url.trim() !== ''
        
        return hasName && hasUrl
      })
      
      console.log(`Produits reçus de l'API: ${products.length}`)
      console.log(`Produits après filtrage: ${realProducts.length}`)
      console.log(`Premiers produits:`, realProducts.slice(0, 3).map(p => ({ id: p.id, name: p.product_name, url: p.product_url })))
      
      const realShops = shops.filter((s: any) => {
        const name = s.shop_name?.toLowerCase() || ''
        return !name.includes('exemple') && 
               !name.includes('test') && 
               !name.includes('demo') &&
               s.shop_name && 
               s.shop_name.trim() !== ''
      })
      
      console.log(`Produits chargés: ${realProducts.length} sur ${products.length} totaux`)
      
      setAllProducts(realProducts)
      setInsights({
        topProducts: realProducts.slice(0, 10),
        topShops: realShops.slice(0, 10)
      })
    } catch (error) {
      console.error('Erreur lors du chargement des insights:', error)
    }
  }

  const applyPresetFilter = (products: any[], preset: PresetFilter): any[] => {
    if (!preset) return products

    switch (preset) {
      case 'recommandé':
        return [...products].sort((a, b) => b.score_winner - a.score_winner)
      case 'top-facebook':
        return products.filter(p => p.marketplace?.toLowerCase() === 'maketou' || p.marketplace?.toLowerCase() === 'chariow')
      case 'nouvelles-boutiques':
        return products.filter(p => {
          if (!p.last_scraped_at) return false
          const scrapedDate = new Date(p.last_scraped_at)
          const daysAgo = (Date.now() - scrapedDate.getTime()) / (1000 * 60 * 60 * 24)
          return daysAgo <= 30
        })
      case 'grosses-ventes':
        return products.filter(p => (p.revenue_est_min || 0) >= 500000).sort((a, b) => 
          (b.revenue_est_min || 0) - (a.revenue_est_min || 0)
        )
      case 'forte-croissance':
        return products.filter(p => p.score_winner >= 70).sort((a, b) => b.score_winner - a.score_winner)
      default:
        return products
    }
  }

  const applyFilters = (products: any[]): any[] => {
    let filtered = [...products]

    // Filtre de recherche
    if (searchQuery) {
      filtered = filtered.filter(p => 
        p.product_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.shop_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.category?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Filtre par prix
    if (filters.priceMin !== undefined) {
      filtered = filtered.filter(p => (p.price || 0) >= filters.priceMin!)
    }
    if (filters.priceMax !== undefined) {
      filtered = filtered.filter(p => (p.price || 0) <= filters.priceMax!)
    }

    // Filtre par marketplace
    if (filters.marketplace) {
      filtered = filtered.filter(p => p.marketplace?.toLowerCase() === filters.marketplace?.toLowerCase())
    }

    // Filtre par catégorie
    if (filters.category) {
      filtered = filtered.filter(p => p.category?.toLowerCase() === filters.category?.toLowerCase())
    }

    // Filtre par score minimum
    if (filters.minScore !== undefined) {
      filtered = filtered.filter(p => p.score_winner >= filters.minScore!)
    }

    // Filtre par revenu minimum
    if (filters.minRevenue !== undefined) {
      filtered = filtered.filter(p => (p.revenue_est_min || 0) >= filters.minRevenue!)
    }

    return filtered
  }

  const applySort = (products: any[]): any[] => {
    const sorted = [...products]

    switch (sortOption) {
      case 'recommandé':
        return sorted.sort((a, b) => b.score_winner - a.score_winner)
      case 'score-desc':
        return sorted.sort((a, b) => b.score_winner - a.score_winner)
      case 'score-asc':
        return sorted.sort((a, b) => a.score_winner - b.score_winner)
      case 'prix-desc':
        return sorted.sort((a, b) => (b.price || 0) - (a.price || 0))
      case 'prix-asc':
        return sorted.sort((a, b) => (a.price || 0) - (b.price || 0))
      case 'revenu-desc':
        return sorted.sort((a, b) => (b.revenue_est_min || 0) - (a.revenue_est_min || 0))
      case 'revenu-asc':
        return sorted.sort((a, b) => (a.revenue_est_min || 0) - (b.revenue_est_min || 0))
      default:
        return sorted
    }
  }

  const getFilteredAndSortedProducts = () => {
    let products = [...allProducts]
    
    // Appliquer le filtre prédéfini
    products = applyPresetFilter(products, presetFilter)
    
    // Appliquer les filtres avancés
    products = applyFilters(products)
    
    // Appliquer le tri
    products = applySort(products)
    
    return products
  }

  const handleFilterClick = (filterName: string) => {
    setShowFilterDialog(filterName)
  }

  const handleFilterChange = (filterName: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }))
    setShowFilterDialog(null)
  }

  const clearFilter = (filterName: string) => {
    setFilters(prev => {
      const newFilters = { ...prev }
      delete newFilters[filterName as keyof FilterState]
      return newFilters
    })
  }

  const clearAllFilters = () => {
    setFilters({})
    setPresetFilter('recommandé')
    setSearchQuery('')
    setSortOption('recommandé')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
          <p className="text-lg font-semibold text-gray-900">Chargement...</p>
        </div>
      </div>
    )
  }

  const filteredProducts = getFilteredAndSortedProducts()
  const uniqueMarketplaces = [...new Set(allProducts.map(p => p.marketplace).filter(Boolean))]
  const uniqueCategories = [...new Set(allProducts.map(p => p.category).filter(Boolean))]

  return (
    <div className="p-6 md:p-8 space-y-6 bg-white">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Package className="h-6 w-6 text-gray-900" />
          <h1 className="text-3xl md:text-4xl font-black text-gray-900 tracking-tight">Top Produits</h1>
        </div>
        <p className="text-gray-600 text-base">
          Découvrez les meilleurs produits avec un fort potentiel identifiés par notre IA
        </p>
      </div>

      {/* Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <Input
            placeholder="Rechercher par mots-clés"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 rounded-xl"
          />
        </div>
        <Button 
          className="h-12 px-6 bg-gray-900 hover:bg-gray-800 text-white rounded-xl"
          onClick={() => {}} // La recherche se fait automatiquement via le state
        >
          Rechercher
        </Button>
        {(Object.keys(filters).length > 0 || presetFilter !== 'recommandé' || searchQuery) && (
          <Button 
            className="h-12 px-4 bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-900 rounded-xl"
            onClick={clearAllFilters}
          >
            <X className="h-4 w-4 mr-2" />
            Réinitialiser
          </Button>
        )}
      </div>

      {/* Smart Preset Filters */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          FILTRES PRÉDÉFINIS INTELLIGENTS
        </p>
        <div className="flex flex-wrap gap-2">
          <Button 
            className={`rounded-xl transition-all duration-200 font-medium ${
              presetFilter === 'recommandé' 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setPresetFilter(presetFilter === 'recommandé' ? null : 'recommandé')}
          >
            <Star className="h-4 w-4 mr-2" />
            Recommandé
          </Button>
          <Button 
            className={`rounded-xl transition-all duration-200 font-medium ${
              presetFilter === 'top-facebook' 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setPresetFilter(presetFilter === 'top-facebook' ? null : 'top-facebook')}
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Top Facebook
          </Button>
          <Button 
            className={`rounded-xl transition-all duration-200 font-medium ${
              presetFilter === 'nouvelles-boutiques' 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setPresetFilter(presetFilter === 'nouvelles-boutiques' ? null : 'nouvelles-boutiques')}
          >
            <Zap className="h-4 w-4 mr-2" />
            Nouvelles Boutiques
          </Button>
          <Button 
            className={`rounded-xl transition-all duration-200 font-medium ${
              presetFilter === 'grosses-ventes' 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setPresetFilter(presetFilter === 'grosses-ventes' ? null : 'grosses-ventes')}
          >
            <Trophy className="h-4 w-4 mr-2" />
            Grosses Ventes
          </Button>
          <Button 
            className={`rounded-xl transition-all duration-200 font-medium ${
              presetFilter === 'forte-croissance' 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setPresetFilter(presetFilter === 'forte-croissance' ? null : 'forte-croissance')}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            Forte Croissance
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            FILTRES
          </p>
          {Object.keys(filters).length > 0 && (
            <Button className="text-sm text-gray-600 hover:text-gray-900 bg-transparent hover:bg-gray-50" onClick={clearAllFilters}>
              <X className="h-3 w-3 mr-1" />
              Effacer ({Object.keys(filters).length})
            </Button>
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
          <Button 
            className={`justify-between rounded-xl transition-all duration-200 font-medium text-sm ${
              filters.priceMin || filters.priceMax 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => handleFilterClick('price')}
          >
            <span>Prix produit</span>
            {filters.priceMin || filters.priceMax ? (
              <X className="h-3 w-3 ml-2 flex-shrink-0" onClick={(e) => { e.stopPropagation(); clearFilter('priceMin'); clearFilter('priceMax') }} />
            ) : (
              <Filter className="h-4 w-4 ml-2 flex-shrink-0 text-gray-500" />
            )}
          </Button>
          <Button 
            className={`justify-between rounded-xl transition-all duration-200 font-medium text-sm ${
              filters.minRevenue 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => handleFilterClick('revenue')}
          >
            <span>Revenu minimum</span>
            {filters.minRevenue ? (
              <X className="h-3 w-3 ml-2 flex-shrink-0" onClick={(e) => { e.stopPropagation(); clearFilter('minRevenue') }} />
            ) : (
              <Filter className="h-4 w-4 ml-2 flex-shrink-0 text-gray-500" />
            )}
          </Button>
          <Button 
            className={`justify-between rounded-xl transition-all duration-200 font-medium text-sm ${
              filters.minScore 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => handleFilterClick('score')}
          >
            <span>Score minimum</span>
            {filters.minScore ? (
              <X className="h-3 w-3 ml-2 flex-shrink-0" onClick={(e) => { e.stopPropagation(); clearFilter('minScore') }} />
            ) : (
              <Filter className="h-4 w-4 ml-2 flex-shrink-0 text-gray-500" />
            )}
          </Button>
          <Button 
            className={`justify-between rounded-xl transition-all duration-200 font-medium text-sm ${
              filters.marketplace 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => handleFilterClick('marketplace')}
          >
            <span>Marché</span>
            {filters.marketplace ? (
              <X className="h-3 w-3 ml-2 flex-shrink-0" onClick={(e) => { e.stopPropagation(); clearFilter('marketplace') }} />
            ) : (
              <Filter className="h-4 w-4 ml-2 flex-shrink-0 text-gray-500" />
            )}
          </Button>
          <Button 
            className={`justify-between rounded-xl transition-all duration-200 font-medium text-sm ${
              filters.category 
                ? "bg-gray-900 text-white shadow-sm" 
                : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => handleFilterClick('category')}
          >
            <span>Niche</span>
            {filters.category ? (
              <X className="h-3 w-3 ml-2 flex-shrink-0" onClick={(e) => { e.stopPropagation(); clearFilter('category') }} />
            ) : (
              <Filter className="h-4 w-4 ml-2 flex-shrink-0 text-gray-500" />
            )}
          </Button>
        </div>
      </div>

      {/* Filter Dialogs */}
      {showFilterDialog === 'price' && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowFilterDialog(null)}>
          <Card className="w-96 bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl border border-gray-200" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="border-b border-gray-200">
              <CardTitle className="text-gray-900 font-black text-lg">Filtrer par prix</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div>
                <label className="text-sm font-semibold text-gray-900 mb-2 block">Prix minimum (FCFA)</label>
                <Input
                  type="number"
                  placeholder="0"
                  value={filters.priceMin || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, priceMin: e.target.value ? Number(e.target.value) : undefined }))}
                  className="bg-white border-2 border-gray-200 text-gray-900 focus:border-gray-900 rounded-xl h-11"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-900 mb-2 block">Prix maximum (FCFA)</label>
                <Input
                  type="number"
                  placeholder="1000000"
                  value={filters.priceMax || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, priceMax: e.target.value ? Number(e.target.value) : undefined }))}
                  className="bg-white border-2 border-gray-200 text-gray-900 focus:border-gray-900 rounded-xl h-11"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button className="flex-1 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-11 shadow-sm" onClick={() => setShowFilterDialog(null)}>Appliquer</Button>
                <Button className="bg-white border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-11 shadow-sm" onClick={() => { clearFilter('priceMin'); clearFilter('priceMax'); setShowFilterDialog(null) }}>Effacer</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showFilterDialog === 'marketplace' && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowFilterDialog(null)}>
          <Card className="w-96 bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl border border-gray-200" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="border-b border-gray-200">
              <CardTitle className="text-gray-900 font-black text-lg">Filtrer par marketplace</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pt-4">
              {uniqueMarketplaces.map((mp) => (
                <Button
                  key={mp}
                  className={`w-full justify-start rounded-xl transition-all duration-200 font-medium h-11 ${
                    filters.marketplace === mp 
                      ? "bg-gray-900 text-white shadow-sm" 
                      : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                  onClick={() => handleFilterChange('marketplace', mp)}
                >
                  {mp?.toUpperCase()}
                </Button>
              ))}
              <Button className="w-full bg-white border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-11 shadow-sm mt-2" onClick={() => { clearFilter('marketplace'); setShowFilterDialog(null) }}>
                Tous les marketplaces
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {showFilterDialog === 'category' && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowFilterDialog(null)}>
          <Card className="w-96 max-h-96 overflow-y-auto bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl border border-gray-200" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="border-b border-gray-200 sticky top-0 bg-gradient-to-br from-white to-gray-50 z-10">
              <CardTitle className="text-gray-900 font-black text-lg">Filtrer par catégorie</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pt-4">
              {uniqueCategories.filter(Boolean).map((cat) => (
                <Button
                  key={cat}
                  className={`w-full justify-start rounded-xl transition-all duration-200 font-medium h-11 ${
                    filters.category === cat 
                      ? "bg-gray-900 text-white shadow-sm" 
                      : "bg-white border-2 border-gray-200 text-gray-900 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                  onClick={() => handleFilterChange('category', cat)}
                >
                  {cat}
                </Button>
              ))}
              <Button className="w-full bg-white border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-11 shadow-sm mt-2" onClick={() => { clearFilter('category'); setShowFilterDialog(null) }}>
                Toutes les catégories
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {showFilterDialog === 'score' && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowFilterDialog(null)}>
          <Card className="w-96 bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl border border-gray-200" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="border-b border-gray-200">
              <CardTitle className="text-gray-900 font-black text-lg">Filtrer par score minimum</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div>
                <label className="text-sm font-semibold text-gray-900 mb-2 block">Score minimum (0-100)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="0"
                  value={filters.minScore || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, minScore: e.target.value ? Number(e.target.value) : undefined }))}
                  className="bg-white border-2 border-gray-200 text-gray-900 focus:border-gray-900 rounded-xl h-11"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button className="flex-1 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-11 shadow-sm" onClick={() => setShowFilterDialog(null)}>Appliquer</Button>
                <Button className="bg-white border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-11 shadow-sm" onClick={() => { clearFilter('minScore'); setShowFilterDialog(null) }}>Effacer</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showFilterDialog === 'revenue' && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowFilterDialog(null)}>
          <Card className="w-96 bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl border border-gray-200" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="border-b border-gray-200">
              <CardTitle className="text-gray-900 font-black text-lg">Filtrer par revenu minimum</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div>
                <label className="text-sm font-semibold text-gray-900 mb-2 block">Revenu minimum (FCFA/mois)</label>
                <Input
                  type="number"
                  placeholder="0"
                  value={filters.minRevenue || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, minRevenue: e.target.value ? Number(e.target.value) : undefined }))}
                  className="bg-white border-2 border-gray-200 text-gray-900 focus:border-gray-900 rounded-xl h-11"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button className="flex-1 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-11 shadow-sm" onClick={() => setShowFilterDialog(null)}>Appliquer</Button>
                <Button className="bg-white border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-11 shadow-sm" onClick={() => { clearFilter('minRevenue'); setShowFilterDialog(null) }}>Effacer</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Products Count and Sort */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <p className="text-gray-600 text-sm font-medium">
          {filteredProducts.length} Produits Disponibles
        </p>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">TRIER:</span>
          <div className="relative">
            <Button 
              className="min-w-[200px] sm:min-w-[300px] justify-between bg-white border-2 border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50 rounded-xl"
              onClick={() => {
                const options: SortOption[] = ['recommandé', 'score-desc', 'score-asc', 'prix-desc', 'prix-asc', 'revenu-desc', 'revenu-asc']
                const currentIndex = options.indexOf(sortOption)
                const nextIndex = (currentIndex + 1) % options.length
                setSortOption(options[nextIndex])
              }}
            >
              {sortOption === 'recommandé' && 'Recommandé - Classement IA pour produits à fort potentiel'}
              {sortOption === 'score-desc' && 'Score décroissant'}
              {sortOption === 'score-asc' && 'Score croissant'}
              {sortOption === 'prix-desc' && 'Prix décroissant'}
              {sortOption === 'prix-asc' && 'Prix croissant'}
              {sortOption === 'revenu-desc' && 'Revenu décroissant'}
              {sortOption === 'revenu-asc' && 'Revenu croissant'}
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Produit
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Nom de la Boutique
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Ventes Mensuelles Estimées
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Prix
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredProducts.length > 0 ? filteredProducts.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      {product.product_image ? (
                        <img 
                          src={product.product_image} 
                          alt={product.product_name}
                          className="w-16 h-16 object-cover rounded-xl border border-gray-200"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none'
                          }}
                        />
                      ) : (
                        <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center">
                          <Package className="h-8 w-8 text-gray-400" />
                        </div>
                      )}
                      <div>
                        <p className="font-semibold text-gray-900">
                          {product.product_name}
                        </p>
                        <a 
                          href={product.product_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-gray-600 hover:text-gray-900 hover:underline inline-flex items-center gap-1"
                        >
                          Voir le produit <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Store className="h-4 w-4 text-gray-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {product.shop_name || 'Boutique'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {product.marketplace?.toUpperCase()}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {product.revenue_est_min && product.revenue_est_max ? (
                      <div className="flex items-center gap-1">
                        <span className="font-semibold text-gray-900">
                          {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                        </span>
                        <ArrowUp className="h-4 w-4 text-green-600" />
                      </div>
                    ) : (
                      <span className="text-gray-500">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {product.price ? (
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(product.price)}
                      </span>
                    ) : (
                      <span className="text-gray-500">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-lg text-gray-900">
                        {Math.round(product.score_winner)}
                      </span>
                      <span className="text-xs text-gray-500">/100</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Button 
                      size="sm" 
                      asChild
                      className="gap-2 bg-gray-900 hover:bg-gray-800 text-white rounded-xl"
                    >
                      <Link href={`/analyse?url=${encodeURIComponent(product.product_url || '')}`}>
                        <Target className="h-4 w-4" />
                        Analyser
                      </Link>
                    </Button>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    Aucun produit trouvé avec les filtres sélectionnés
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

