"use client"

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Package, TrendingUp, DollarSign, Trophy, Store, BarChart3 } from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

function ShopNameLink({ shopName }: { shopName: string }) {
  const [shopId, setShopId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchShopId = async () => {
      if (!shopName || shopName.trim() === '') {
        setLoading(false)
        return
      }
      
      try {
        const response = await api.get(`/winners/shop-by-name?shop_name=${encodeURIComponent(shopName.trim())}`)
        if (response?.data && response.data.id) {
          setShopId(response.data.id)
        }
      } catch (error: any) {
        console.error('Erreur lors de la récupération de la boutique:', error)
        console.log(`Boutique recherchée: "${shopName}"`)
        if (error.response?.data) {
          console.log('Détails erreur:', error.response.data)
        }
      } finally {
        setLoading(false)
      }
    }
    
    fetchShopId()
  }, [shopName])

  if (loading) {
    return <p className="font-semibold">{shopName}</p>
  }

  if (shopId) {
    return (
      <Link 
        href={`/dashboard/shop/${shopId}`}
        className="font-semibold text-gray-900 hover:text-gray-700 hover:underline"
      >
        {shopName}
      </Link>
    )
  }

  return <p className="font-semibold">{shopName}</p>
}

interface ProductDetails {
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
  last_scraped_at: string | null
}

export default function ProductDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const productId = params.id as string
  const [product, setProduct] = useState<ProductDetails | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (productId) {
      fetchProductDetails()
    }
  }, [productId])

  const fetchProductDetails = async () => {
    try {
      const response = await api.get(`/winners/products/${productId}`)
      setProduct(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement du produit:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <div className="text-center text-gray-600">Chargement...</div>
        </div>
      </DashboardLayout>
    )
  }

  if (!product) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
            <CardContent className="py-12 text-center">
              <p className="text-gray-600">Produit introuvable.</p>
              <Button className="mt-4 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold" asChild>
                <Link href="/dashboard/winners">Retour aux winners</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6 space-y-6">
      {/* Header avec bouton retour */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()} className="hover:bg-gray-100">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-2">
            <Package className="h-8 w-8 text-gray-700" />
            {product.product_name}
          </h1>
          <p className="text-gray-600">
            {product.shop_name} • {product.marketplace.toUpperCase()}
            {product.category && ` • ${product.category}`}
          </p>
        </div>
      </div>

      {/* Informations principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
              <Trophy className="h-5 w-5 text-gray-700" />
              Score Winner
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-black text-gray-900">
              {Math.round(product.score_winner * 10) / 10}
            </p>
            <p className="text-sm text-gray-500 mt-1">sur 100</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
              <DollarSign className="h-5 w-5 text-gray-700" />
              Prix
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.price ? (
              <p className="text-3xl font-black text-gray-900">
                {formatCurrency(product.price)}
              </p>
            ) : (
              <p className="text-gray-500">Non disponible</p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
              <BarChart3 className="h-5 w-5 text-gray-700" />
              Ventes Estimées
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.sales_est_min && product.sales_est_max ? (
              <div>
                <p className="text-2xl font-black text-gray-900">
                  {product.sales_est_min} - {product.sales_est_max}
                </p>
                <p className="text-sm text-gray-500 mt-1">par mois</p>
              </div>
            ) : (
              <p className="text-gray-500">Non disponible</p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-900 font-bold">
              <TrendingUp className="h-5 w-5 text-gray-700" />
              CA Estimé
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.revenue_est_min && product.revenue_est_max ? (
              <div>
                <p className="text-2xl font-black text-gray-900">
                  {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                </p>
                <p className="text-sm text-gray-500 mt-1">par mois</p>
              </div>
            ) : (
              <p className="text-gray-500">Non disponible</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Informations détaillées */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Informations produit */}
        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-gray-900 font-bold">Informations du Produit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-1 font-medium">Nom du produit</p>
              <p className="font-semibold text-gray-900">{product.product_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1 font-medium">Boutique</p>
              <ShopNameLink shopName={product.shop_name} />
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1 font-medium">Marketplace</p>
              <p className="font-semibold text-gray-900">{product.marketplace.toUpperCase()}</p>
            </div>
            {product.category && (
              <div>
                <p className="text-sm text-gray-600 mb-1 font-medium">Catégorie</p>
                <span className="inline-block px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 font-semibold text-sm">
                  {product.category}
                </span>
              </div>
            )}
            {product.last_scraped_at && (
              <div>
                <p className="text-sm text-gray-600 mb-1 font-medium">Dernière mise à jour</p>
                <p className="font-semibold text-gray-900">
                  {new Date(product.last_scraped_at).toLocaleDateString('fr-FR', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Statistiques de performance */}
        <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-gray-900 font-bold">Statistiques de Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600 font-medium">Score Winner</span>
              <span className="text-2xl font-black text-gray-900">
                {Math.round(product.score_winner * 10) / 10}
              </span>
            </div>
            {product.price && (
              <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600 font-medium">Prix unitaire</span>
                <span className="text-xl font-black text-gray-900">
                  {formatCurrency(product.price)}
                </span>
              </div>
            )}
            {product.sales_est_min && product.sales_est_max && (
              <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600 font-medium">Ventes mensuelles</span>
                <span className="text-xl font-black text-gray-900">
                  {product.sales_est_min} - {product.sales_est_max}
                </span>
              </div>
            )}
            {product.revenue_est_min && product.revenue_est_max && (
              <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600 font-medium">CA mensuel estimé</span>
                <span className="text-xl font-black text-gray-900">
                  {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button className="w-full bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-semibold h-12 shadow-md hover:shadow-lg transition-all duration-300" asChild>
          <Link href={`/analyse?url=${encodeURIComponent(product.product_url)}`}>
            Analyser ce produit
          </Link>
        </Button>
        <Button className="w-full bg-white border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-12 transition-all duration-300" asChild>
          <a href={product.product_url} target="_blank" rel="noopener noreferrer">
            Voir sur le marketplace
          </a>
        </Button>
        <Button className="w-full bg-white border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 text-gray-900 rounded-xl font-semibold h-12 transition-all duration-300" asChild>
          <Link href="/dashboard/winners">
            Retour aux winners
          </Link>
        </Button>
      </div>
      </div>
    </DashboardLayout>
  )
}
