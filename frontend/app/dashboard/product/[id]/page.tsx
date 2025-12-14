"use client"

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
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
        className="font-semibold text-neon-blue hover:underline"
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
      <div className="container mx-auto p-6">
        <div className="text-center">Chargement...</div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="container mx-auto p-6">
        <Card className="glass">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Produit introuvable.</p>
            <Button variant="outline" className="mt-4" asChild>
              <Link href="/dashboard/winners">Retour aux winners</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header avec bouton retour */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold neon-blue mb-2 flex items-center gap-2">
            <Package className="h-8 w-8" />
            {product.product_name}
          </h1>
          <p className="text-muted-foreground">
            {product.shop_name} • {product.marketplace.toUpperCase()}
            {product.category && ` • ${product.category}`}
          </p>
        </div>
      </div>

      {/* Informations principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-neon-blue" />
              Score Winner
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-neon-blue">
              {Math.round(product.score_winner * 10) / 10}
            </p>
            <p className="text-sm text-muted-foreground mt-1">sur 100</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-neon-green" />
              Prix
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.price ? (
              <p className="text-3xl font-bold text-neon-green">
                {formatCurrency(product.price)}
              </p>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-neon-purple" />
              Ventes Estimées
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.sales_est_min && product.sales_est_max ? (
              <div>
                <p className="text-2xl font-bold text-neon-purple">
                  {product.sales_est_min} - {product.sales_est_max}
                </p>
                <p className="text-sm text-muted-foreground mt-1">par mois</p>
              </div>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-yellow-500" />
              CA Estimé
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.revenue_est_min && product.revenue_est_max ? (
              <div>
                <p className="text-2xl font-bold text-yellow-500">
                  {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                </p>
                <p className="text-sm text-muted-foreground mt-1">par mois</p>
              </div>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Informations détaillées */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Informations produit */}
        <Card className="glass">
          <CardHeader>
            <CardTitle>Informations du Produit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Nom du produit</p>
              <p className="font-semibold">{product.product_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Boutique</p>
              <Link 
                href={`/dashboard/shop/${product.id}`}
                className="font-semibold text-neon-blue hover:underline"
              >
                {product.shop_name}
              </Link>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Marketplace</p>
              <p className="font-semibold">{product.marketplace.toUpperCase()}</p>
            </div>
            {product.category && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Catégorie</p>
                <span className="inline-block px-3 py-1 rounded bg-accent font-semibold">
                  {product.category}
                </span>
              </div>
            )}
            {product.last_scraped_at && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Dernière mise à jour</p>
                <p className="font-semibold">
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
        <Card className="glass">
          <CardHeader>
            <CardTitle>Statistiques de Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
              <span className="text-sm text-muted-foreground">Score Winner</span>
              <span className="text-2xl font-bold text-neon-blue">
                {Math.round(product.score_winner * 10) / 10}
              </span>
            </div>
            {product.price && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                <span className="text-sm text-muted-foreground">Prix unitaire</span>
                <span className="text-xl font-bold text-neon-green">
                  {formatCurrency(product.price)}
                </span>
              </div>
            )}
            {product.sales_est_min && product.sales_est_max && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                <span className="text-sm text-muted-foreground">Ventes mensuelles</span>
                <span className="text-xl font-bold text-neon-purple">
                  {product.sales_est_min} - {product.sales_est_max}
                </span>
              </div>
            )}
            {product.revenue_est_min && product.revenue_est_max && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                <span className="text-sm text-muted-foreground">CA mensuel estimé</span>
                <span className="text-xl font-bold text-yellow-500">
                  {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button variant="neon" className="w-full" asChild>
          <Link href={`/analyse?url=${encodeURIComponent(product.product_url)}`}>
            Analyser ce produit
          </Link>
        </Button>
        <Button variant="outline" className="w-full" asChild>
          <a href={product.product_url} target="_blank" rel="noopener noreferrer">
            Voir sur le marketplace
          </a>
        </Button>
        <Button variant="outline" className="w-full" asChild>
          <Link href="/dashboard/winners">
            Retour aux winners
          </Link>
        </Button>
      </div>
    </div>
  )
}


import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
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
        className="font-semibold text-neon-blue hover:underline"
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
      <div className="container mx-auto p-6">
        <div className="text-center">Chargement...</div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="container mx-auto p-6">
        <Card className="glass">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Produit introuvable.</p>
            <Button variant="outline" className="mt-4" asChild>
              <Link href="/dashboard/winners">Retour aux winners</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header avec bouton retour */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold neon-blue mb-2 flex items-center gap-2">
            <Package className="h-8 w-8" />
            {product.product_name}
          </h1>
          <p className="text-muted-foreground">
            {product.shop_name} • {product.marketplace.toUpperCase()}
            {product.category && ` • ${product.category}`}
          </p>
        </div>
      </div>

      {/* Informations principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-neon-blue" />
              Score Winner
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-neon-blue">
              {Math.round(product.score_winner * 10) / 10}
            </p>
            <p className="text-sm text-muted-foreground mt-1">sur 100</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-neon-green" />
              Prix
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.price ? (
              <p className="text-3xl font-bold text-neon-green">
                {formatCurrency(product.price)}
              </p>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-neon-purple" />
              Ventes Estimées
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.sales_est_min && product.sales_est_max ? (
              <div>
                <p className="text-2xl font-bold text-neon-purple">
                  {product.sales_est_min} - {product.sales_est_max}
                </p>
                <p className="text-sm text-muted-foreground mt-1">par mois</p>
              </div>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-yellow-500" />
              CA Estimé
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product.revenue_est_min && product.revenue_est_max ? (
              <div>
                <p className="text-2xl font-bold text-yellow-500">
                  {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                </p>
                <p className="text-sm text-muted-foreground mt-1">par mois</p>
              </div>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Informations détaillées */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Informations produit */}
        <Card className="glass">
          <CardHeader>
            <CardTitle>Informations du Produit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Nom du produit</p>
              <p className="font-semibold">{product.product_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Boutique</p>
              <Link 
                href={`/dashboard/shop/${product.id}`}
                className="font-semibold text-neon-blue hover:underline"
              >
                {product.shop_name}
              </Link>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Marketplace</p>
              <p className="font-semibold">{product.marketplace.toUpperCase()}</p>
            </div>
            {product.category && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Catégorie</p>
                <span className="inline-block px-3 py-1 rounded bg-accent font-semibold">
                  {product.category}
                </span>
              </div>
            )}
            {product.last_scraped_at && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Dernière mise à jour</p>
                <p className="font-semibold">
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
        <Card className="glass">
          <CardHeader>
            <CardTitle>Statistiques de Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
              <span className="text-sm text-muted-foreground">Score Winner</span>
              <span className="text-2xl font-bold text-neon-blue">
                {Math.round(product.score_winner * 10) / 10}
              </span>
            </div>
            {product.price && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                <span className="text-sm text-muted-foreground">Prix unitaire</span>
                <span className="text-xl font-bold text-neon-green">
                  {formatCurrency(product.price)}
                </span>
              </div>
            )}
            {product.sales_est_min && product.sales_est_max && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                <span className="text-sm text-muted-foreground">Ventes mensuelles</span>
                <span className="text-xl font-bold text-neon-purple">
                  {product.sales_est_min} - {product.sales_est_max}
                </span>
              </div>
            )}
            {product.revenue_est_min && product.revenue_est_max && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                <span className="text-sm text-muted-foreground">CA mensuel estimé</span>
                <span className="text-xl font-bold text-yellow-500">
                  {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button variant="neon" className="w-full" asChild>
          <Link href={`/analyse?url=${encodeURIComponent(product.product_url)}`}>
            Analyser ce produit
          </Link>
        </Button>
        <Button variant="outline" className="w-full" asChild>
          <a href={product.product_url} target="_blank" rel="noopener noreferrer">
            Voir sur le marketplace
          </a>
        </Button>
        <Button variant="outline" className="w-full" asChild>
          <Link href="/dashboard/winners">
            Retour aux winners
          </Link>
        </Button>
      </div>
    </div>
  )
}

