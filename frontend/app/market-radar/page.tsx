"use client"

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, Store, Package } from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface TopProduct {
  id: number
  name: string
  score: number
  marketplace: string
  trend: string
}

interface TopShop {
  id: number
  name: string
  estimated_revenue: number
  growth_rate: number
  product_count: number
}

export default function MarketRadarPage() {
  const [topProducts, setTopProducts] = useState<TopProduct[]>([])
  const [topShops, setTopShops] = useState<TopShop[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRadarData()
  }, [])

  const fetchRadarData = async () => {
    try {
      // Utiliser les endpoints winners qui contiennent les vraies données
      const [productsRes, shopsRes] = await Promise.all([
        api.get('/winners/products?limit=20'),
        api.get('/winners/shops?limit=20')
      ])
      
      // Adapter les données au format attendu
      setTopProducts(productsRes.data.map((p: any) => ({
        id: p.id,
        name: p.product_name,
        score: p.score_winner,
        marketplace: p.marketplace,
        trend: 'rising' // Par défaut, on peut calculer la tendance plus tard
      })))
      
      setTopShops(shopsRes.data.map((s: any) => ({
        id: s.id,
        name: s.shop_name,
        estimated_revenue: s.revenue_est_max || s.revenue_est_min || 0,
        growth_rate: 0, // À calculer si nécessaire
        product_count: s.winners_count || 0
      })))
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen bg-white">
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
            <p className="text-lg font-semibold text-gray-900">Chargement...</p>
          </div>
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
            Radar du Marché
          </h1>
          <p className="text-gray-600 text-base">
            Découvrez les top produits, boutiques et tendances du marché
          </p>
        </div>

        {/* Top Produits */}
        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
              <Package className="h-5 w-5 text-gray-700" />
              Top Produits
            </CardTitle>
            <CardDescription className="text-gray-600">Les produits les mieux notés sur toutes les marketplaces</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {topProducts.length > 0 ? topProducts.map((product, idx) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between p-4 rounded-xl border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all duration-200"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-2xl font-black text-gray-400 w-8">#{idx + 1}</span>
                    <div>
                      <p className="font-semibold text-gray-900">{product.name}</p>
                      <p className="text-sm text-gray-500">{product.marketplace.toUpperCase()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {product.trend === 'rising' && (
                      <TrendingUp className="h-5 w-5 text-green-600" />
                    )}
                    {product.trend === 'falling' && (
                      <TrendingDown className="h-5 w-5 text-red-600" />
                    )}
                    <span className="text-xl font-black text-gray-900">{Math.round(product.score * 10) / 10}</span>
                  </div>
                </div>
              )) : (
                <p className="text-center text-gray-600 py-12">Aucun produit disponible pour le moment.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Top Boutiques */}
        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
              <Store className="h-5 w-5 text-gray-700" />
              Top Boutiques
            </CardTitle>
            <CardDescription className="text-gray-600">Les boutiques les plus performantes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {topShops.length > 0 ? topShops.map((shop, idx) => (
                <div
                  key={shop.id}
                  className="flex items-center justify-between p-4 rounded-xl border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all duration-200"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-2xl font-black text-gray-400 w-8">#{idx + 1}</span>
                    <div>
                      <p className="font-semibold text-gray-900">{shop.name}</p>
                      <p className="text-sm text-gray-500">
                        {shop.product_count} produits winners
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-black text-gray-900">
                      {shop.estimated_revenue ? formatCurrency(shop.estimated_revenue) : 'N/A'}
                    </p>
                    <p className="text-sm text-gray-500">CA estimé/mois</p>
                  </div>
                </div>
              )) : (
                <p className="text-center text-gray-600 py-12">Aucune boutique disponible pour le moment.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

