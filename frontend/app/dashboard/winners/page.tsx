"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Package, Store, Grid, Filter, TrendingUp } from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface WinnerProduct {
  id: number
  marketplace: string
  product_name: string
  shop_name: string
  product_url: string
  price: number | null
  sales_est_min: number | null
  sales_est_max: number | null
  revenue_est_min: number | null
  revenue_est_max: number | null
  score_winner: number
  category: string | null
}

interface WinnerShop {
  id: number
  marketplace: string
  shop_name: string
  shop_url: string
  score_global: number
  revenue_est_min: number | null
  revenue_est_max: number | null
  winners_count: number
}

export default function WinnersPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [products, setProducts] = useState<WinnerProduct[]>([])
  const [shops, setShops] = useState<WinnerShop[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  
  // Récupérer le tab depuis les query params
  const activeTab = searchParams.get('tab') || 'products'
  
  // Filtres
  const [marketplaceFilter, setMarketplaceFilter] = useState<string>('')
  const [minScoreFilter, setMinScoreFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  
  const handleTabChange = (value: string) => {
    router.push(`/dashboard/winners?tab=${value}`)
  }

  useEffect(() => {
    fetchWinners()
    fetchCategories()
  }, [])

  const fetchWinners = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (marketplaceFilter) params.marketplace = marketplaceFilter
      if (minScoreFilter) params.min_score = parseFloat(minScoreFilter)
      if (categoryFilter) params.category = categoryFilter

      // Augmenter la limite pour avoir plus de résultats
      // Ne pas inclure les paramètres vides (chaînes vides ou null)
      const paramsWithLimit: any = { limit: 200 }
      if (marketplaceFilter && marketplaceFilter.trim() !== '') {
        paramsWithLimit.marketplace = marketplaceFilter.trim()
      }
      if (minScoreFilter && minScoreFilter.trim() !== '') {
        const score = parseFloat(minScoreFilter)
        if (!isNaN(score)) {
          paramsWithLimit.min_score = score
        }
      }
      if (categoryFilter && categoryFilter.trim() !== '') {
        paramsWithLimit.category = categoryFilter.trim()
      }
      
      const shopsParams: any = { limit: 200 }
      if (marketplaceFilter && marketplaceFilter.trim() !== '') {
        shopsParams.marketplace = marketplaceFilter.trim()
      }
      if (minScoreFilter && minScoreFilter.trim() !== '') {
        const score = parseFloat(minScoreFilter)
        if (!isNaN(score)) {
          shopsParams.min_score = score
        }
      }
      
      console.log('🔍 Paramètres envoyés au backend:', paramsWithLimit)
      
      const [productsRes, shopsRes] = await Promise.all([
        api.get('/winners/products', { params: paramsWithLimit }),
        api.get('/winners/shops', { params: shopsParams })
      ])
      
      console.log('📡 Réponse du backend - Status:', productsRes.status)
      
      // Le backend retourne maintenant directement les vraies données depuis Facebook Ads
      // Les exemples codés en dur ne sont retournés que s'il n'y a vraiment aucune donnée en base
      const products = productsRes.data || []
      const shops = shopsRes.data || []
      
      console.log('📦 Produits reçus du backend:', products.length)
      console.log('📦 Premiers produits:', products.slice(0, 3).map((p: any) => ({
        id: p.id,
        name: p.product_name?.substring(0, 50),
        score: p.score_winner
      })))
      
      // Filtrer uniquement les exemples si présents (sécurité supplémentaire)
      // Normalement le backend ne devrait pas les retourner s'il y a des données réelles
      const realProducts = products.filter((p: any) => {
        const name = (p.product_name || '').toLowerCase()
        const isExample = name.includes('produit winner exemple') || name.includes('boutique exemple')
        if (isExample) {
          console.log('❌ Produit exclu (exemple):', p.product_name)
        }
        return !isExample
      })
      
      const realShops = shops.filter((s: any) => {
        const name = (s.shop_name || '').toLowerCase()
        return !name.includes('boutique winner exemple') && !name.includes('boutique exemple')
      })
      
      console.log('✅ Produits après filtrage:', realProducts.length)
      console.log('✅ Produits finaux à afficher:', realProducts.map((p: any) => ({
        id: p.id,
        name: p.product_name?.substring(0, 50),
        score: p.score_winner
      })))
      
      // Utiliser les vraies données (normalement toutes les données sont réelles maintenant)
      const finalProducts = realProducts.length > 0 ? realProducts : products
      setProducts(finalProducts)
      setShops(realShops.length > 0 ? realShops : shops)
      
      console.log(`✅ ${finalProducts.length} produits winners chargés depuis Facebook Ads`)
      console.log(`✅ ${realShops.length} boutiques winners chargées`)
    } catch (error: any) {
      console.error('Erreur lors du chargement des winners:', error)
      console.error('Détails erreur:', error.response?.data || error.message)
      // En cas d'erreur, initialiser avec des tableaux vides pour éviter les erreurs d'affichage
      setProducts([])
      setShops([])
    } finally {
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const response = await api.get('/winners/categories')
      setCategories(response.data.categories || [])
    } catch (error) {
      console.error('Erreur lors du chargement des catégories:', error)
    }
  }

  const handleFilterChange = () => {
    fetchWinners()
  }

  if (loading && products.length === 0) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="text-center">Chargement...</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
    <div className="p-6 md:p-8 space-y-6 bg-white">
      <div>
        <h1 className="text-3xl md:text-4xl font-black text-gray-900 tracking-tight mb-2 flex items-center gap-3">
          <TrendingUp className="h-7 w-7 md:h-8 md:w-8 text-gray-900" />
          Catalog Winners
        </h1>
        <p className="text-gray-600 text-base">
          Découvrez les produits et boutiques winners extraits automatiquement des marketplaces
        </p>
      </div>

      {/* Filtres */}
      <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-gray-900 font-bold text-base">
            <Filter className="h-5 w-5 text-gray-700" />
            Filtres
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-2 block">Marketplace</label>
              <select
                className="w-full h-12 rounded-xl border border-gray-300 bg-white text-gray-900 px-4 py-2 text-sm focus:border-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-400 cursor-pointer shadow-sm"
                value={marketplaceFilter}
                onChange={(e) => setMarketplaceFilter(e.target.value)}
              >
                <option value="">Toutes</option>
                <option value="chariow">CHARIOW</option>
                <option value="maketou">Maketou</option>
                <option value="systemio">System.io</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-2 block">Score minimum</label>
              <Input
                type="number"
                placeholder="70"
                value={minScoreFilter}
                onChange={(e) => setMinScoreFilter(e.target.value)}
                min="0"
                max="100"
                className="h-12 bg-white border border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 rounded-xl shadow-sm"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-2 block">Catégorie</label>
              <select
                className="w-full h-12 rounded-xl border border-gray-300 bg-white text-gray-900 px-4 py-2 text-sm focus:border-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-400 cursor-pointer shadow-sm"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="">Toutes</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <Button onClick={handleFilterChange} className="w-full h-12 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold shadow-md hover:shadow-lg transition-all duration-300">
                Appliquer
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList className="bg-gray-100 rounded-xl p-1 border border-gray-200">
          <TabsTrigger value="products" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600">
            <Package className="mr-2 h-4 w-4" />
            Top Produits Winners
          </TabsTrigger>
          <TabsTrigger value="shops" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600">
            <Store className="mr-2 h-4 w-4" />
            Top Boutiques Winners
          </TabsTrigger>
          <TabsTrigger value="categories" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600">
            <Grid className="mr-2 h-4 w-4" />
            Explorer par Catégorie
          </TabsTrigger>
        </TabsList>

        {/* Produits */}
        <TabsContent value="products" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((product) => (
              <Card key={product.id} className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 hover:border-gray-300 hover:-translate-y-1">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start gap-3">
                    <CardTitle className="text-lg font-bold text-gray-900 line-clamp-2 flex-1">{product.product_name}</CardTitle>
                    <div className="text-right flex-shrink-0">
                      <div className="text-2xl font-black text-gray-900">{Math.round(product.score_winner)}</div>
                      <div className="text-xs text-gray-500 font-medium">Score</div>
                    </div>
                  </div>
                  <CardDescription className="text-gray-500 text-sm mt-1">{product.shop_name} • {product.marketplace.toUpperCase()}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  {product.price && (
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600 font-medium">Prix</span>
                      <span className="font-bold text-gray-900">{formatCurrency(product.price)}</span>
                    </div>
                  )}
                  {product.revenue_est_min && product.revenue_est_max && (
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600 font-medium">CA estimé</span>
                      <span className="font-bold text-gray-900 text-sm text-right">
                        {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}/mois
                      </span>
                    </div>
                  )}
                  {product.category && (
                    <div>
                      <span className="text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 font-semibold">{product.category}</span>
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button className="flex-1 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-10" asChild>
                      <Link href={`/dashboard/product/${product.id}`}>
                        Voir les détails
                      </Link>
                    </Button>
                    <Button className="flex-1 bg-white border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-10" asChild>
                      <a href={product.product_url} target="_blank" rel="noopener noreferrer">
                        Ouvrir
                      </a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {products.length === 0 && (
            <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
              <CardContent className="py-16 text-center">
                <p className="text-gray-600 text-base">Aucun produit trouvé avec ces filtres.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Boutiques */}
        <TabsContent value="shops" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {shops.map((shop) => (
              <Card key={shop.id} className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 hover:border-gray-300 hover:-translate-y-1">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start gap-3">
                    <CardTitle className="text-lg font-bold text-gray-900 flex-1">{shop.shop_name}</CardTitle>
                    <div className="text-right flex-shrink-0">
                      <div className="text-2xl font-black text-gray-900">{Math.round(shop.score_global)}</div>
                      <div className="text-xs text-gray-500 font-medium">Score</div>
                    </div>
                  </div>
                  <CardDescription className="text-gray-500 text-sm mt-1">{shop.marketplace.toUpperCase()}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600 font-medium">Winners</span>
                    <span className="font-bold text-gray-900">{shop.winners_count}</span>
                  </div>
                  {shop.revenue_est_min && shop.revenue_est_max && (
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600 font-medium">CA estimé</span>
                      <span className="font-bold text-gray-900 text-sm text-right">
                        {formatCurrency(shop.revenue_est_min)} - {formatCurrency(shop.revenue_est_max)}/mois
                      </span>
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button className="flex-1 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-10" asChild>
                      <Link href={`/dashboard/shop/${shop.id}`}>
                        Voir les détails
                      </Link>
                    </Button>
                    <Button className="flex-1 bg-white border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-10" asChild>
                      <a href={shop.shop_url} target="_blank" rel="noopener noreferrer">
                        Ouvrir
                      </a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {shops.length === 0 && (
            <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
              <CardContent className="py-16 text-center">
                <p className="text-gray-600 text-base">Aucune boutique trouvée avec ces filtres.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Catégories */}
        <TabsContent value="categories" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {categories.map((category) => (
              <Card
                key={category}
                className="bg-white border-2 border-gray-200 rounded-2xl shadow-sm hover:shadow-md hover:border-gray-300 transition-all duration-300 cursor-pointer"
                onClick={() => {
                  setCategoryFilter(category)
                  handleFilterChange()
                }}
              >
                <CardContent className="p-6 text-center">
                  <p className="font-semibold text-gray-900">{category}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
    </DashboardLayout>
  )
}

