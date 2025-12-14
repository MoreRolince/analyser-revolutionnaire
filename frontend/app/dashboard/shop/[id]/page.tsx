"use client"

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Store, Package, TrendingUp, DollarSign, Trophy } from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface ShopDetails {
  id: number
  marketplace: string
  shop_name: string
  shop_url: string
  score_global: number
  revenue_est_min: number | null
  revenue_est_max: number | null
  winners_count: number
  last_scraped_at: string | null
}

interface ShopProduct {
  id: number
  product_name: string
  product_url: string
  price: number | null
  sales_est_min: number | null
  sales_est_max: number | null
  revenue_est_min: number | null
  revenue_est_max: number | null
  score_winner: number
  category: string | null
}

export default function ShopDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const shopId = params.id as string
  const [shop, setShop] = useState<ShopDetails | null>(null)
  const [products, setProducts] = useState<ShopProduct[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (shopId) {
      fetchShopDetails()
    }
  }, [shopId])

  useEffect(() => {
    if (shop) {
      fetchShopProducts()
    }
  }, [shop])

  const fetchShopDetails = async () => {
    try {
      const response = await api.get(`/winners/shops/${shopId}`)
      setShop(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement de la boutique:', error)
    }
  }

  const fetchShopProducts = async () => {
    try {
      // Récupérer tous les produits et filtrer par shop_name côté client
      // Ou créer un endpoint spécifique pour les produits d'une boutique
      const response = await api.get('/winners/products?limit=100')
      if (shop) {
        const shopProducts = response.data.filter((p: any) => 
          p.shop_name === shop.shop_name
        )
        setProducts(shopProducts)
      } else {
        // Si shop pas encore chargé, on attend
        setTimeout(() => fetchShopProducts(), 500)
      }
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error)
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

  if (!shop) {
    return (
      <div className="container mx-auto p-6">
        <Card className="glass">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Boutique introuvable.</p>
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
        <div>
          <h1 className="text-4xl font-bold neon-blue mb-2 flex items-center gap-2">
            <Store className="h-8 w-8" />
            {shop.shop_name}
          </h1>
          <p className="text-muted-foreground">{shop.marketplace.toUpperCase()}</p>
        </div>
      </div>

      {/* Informations de la boutique */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-neon-purple" />
              Score Global
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-neon-purple">
              {Math.round(shop.score_global * 10) / 10}
            </p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-neon-blue" />
              CA Estimé
            </CardTitle>
          </CardHeader>
          <CardContent>
            {shop.revenue_est_min && shop.revenue_est_max ? (
              <p className="text-2xl font-bold text-neon-blue">
                {formatCurrency(shop.revenue_est_min)} - {formatCurrency(shop.revenue_est_max)}
              </p>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
            <p className="text-sm text-muted-foreground mt-1">par mois</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5 text-neon-green" />
              Produits Winners
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-neon-green">{shop.winners_count}</p>
            <p className="text-sm text-muted-foreground mt-1">produits performants</p>
          </CardContent>
        </Card>
      </div>

      {/* Bouton pour analyser la boutique */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold mb-1">Analyser cette boutique</h3>
              <p className="text-sm text-muted-foreground">
                Obtenez une analyse détaillée avec scores, estimations et insights IA
              </p>
            </div>
            <Button variant="neon" asChild>
              <Link href={`/analyse?url=${encodeURIComponent(shop.shop_url)}`}>
                Analyser
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Produits de la boutique */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Produits de la Boutique
          </CardTitle>
          <CardDescription>
            {products.length} produit{products.length > 1 ? 's' : ''} trouvé{products.length > 1 ? 's' : ''}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.map((product) => (
                <Card key={product.id} className="hover:glow-box transition-all">
                  <CardHeader>
                    <CardTitle className="text-lg line-clamp-2">{product.product_name}</CardTitle>
                    <CardDescription>
                      Score: <span className="font-bold text-neon-blue">{Math.round(product.score_winner * 10) / 10}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {product.price && (
                      <div>
                        <span className="text-sm text-muted-foreground">Prix: </span>
                        <span className="font-semibold">{formatCurrency(product.price)}</span>
                      </div>
                    )}
                    {product.revenue_est_min && product.revenue_est_max && (
                      <div>
                        <span className="text-sm text-muted-foreground">CA estimé: </span>
                        <span className="font-semibold text-sm">
                          {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}/mois
                        </span>
                      </div>
                    )}
                    {product.category && (
                      <div>
                        <span className="text-xs px-2 py-1 rounded bg-accent">{product.category}</span>
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button variant="outline" className="flex-1" asChild>
                        <a href={product.product_url} target="_blank" rel="noopener noreferrer">
                          Voir le produit
                        </a>
                      </Button>
                      <Button variant="outline" className="flex-1" asChild>
                        <Link href={`/analyse?url=${encodeURIComponent(product.product_url)}`}>
                          Analyser
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Aucun produit trouvé pour cette boutique.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}


import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Store, Package, TrendingUp, DollarSign, Trophy } from 'lucide-react'
import api from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface ShopDetails {
  id: number
  marketplace: string
  shop_name: string
  shop_url: string
  score_global: number
  revenue_est_min: number | null
  revenue_est_max: number | null
  winners_count: number
  last_scraped_at: string | null
}

interface ShopProduct {
  id: number
  product_name: string
  product_url: string
  price: number | null
  sales_est_min: number | null
  sales_est_max: number | null
  revenue_est_min: number | null
  revenue_est_max: number | null
  score_winner: number
  category: string | null
}

export default function ShopDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const shopId = params.id as string
  const [shop, setShop] = useState<ShopDetails | null>(null)
  const [products, setProducts] = useState<ShopProduct[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (shopId) {
      fetchShopDetails()
    }
  }, [shopId])

  useEffect(() => {
    if (shop) {
      fetchShopProducts()
    }
  }, [shop])

  const fetchShopDetails = async () => {
    try {
      const response = await api.get(`/winners/shops/${shopId}`)
      setShop(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement de la boutique:', error)
    }
  }

  const fetchShopProducts = async () => {
    try {
      // Récupérer tous les produits et filtrer par shop_name côté client
      // Ou créer un endpoint spécifique pour les produits d'une boutique
      const response = await api.get('/winners/products?limit=100')
      if (shop) {
        const shopProducts = response.data.filter((p: any) => 
          p.shop_name === shop.shop_name
        )
        setProducts(shopProducts)
      } else {
        // Si shop pas encore chargé, on attend
        setTimeout(() => fetchShopProducts(), 500)
      }
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error)
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

  if (!shop) {
    return (
      <div className="container mx-auto p-6">
        <Card className="glass">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Boutique introuvable.</p>
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
        <div>
          <h1 className="text-4xl font-bold neon-blue mb-2 flex items-center gap-2">
            <Store className="h-8 w-8" />
            {shop.shop_name}
          </h1>
          <p className="text-muted-foreground">{shop.marketplace.toUpperCase()}</p>
        </div>
      </div>

      {/* Informations de la boutique */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-neon-purple" />
              Score Global
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-neon-purple">
              {Math.round(shop.score_global * 10) / 10}
            </p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-neon-blue" />
              CA Estimé
            </CardTitle>
          </CardHeader>
          <CardContent>
            {shop.revenue_est_min && shop.revenue_est_max ? (
              <p className="text-2xl font-bold text-neon-blue">
                {formatCurrency(shop.revenue_est_min)} - {formatCurrency(shop.revenue_est_max)}
              </p>
            ) : (
              <p className="text-muted-foreground">Non disponible</p>
            )}
            <p className="text-sm text-muted-foreground mt-1">par mois</p>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5 text-neon-green" />
              Produits Winners
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-neon-green">{shop.winners_count}</p>
            <p className="text-sm text-muted-foreground mt-1">produits performants</p>
          </CardContent>
        </Card>
      </div>

      {/* Bouton pour analyser la boutique */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold mb-1">Analyser cette boutique</h3>
              <p className="text-sm text-muted-foreground">
                Obtenez une analyse détaillée avec scores, estimations et insights IA
              </p>
            </div>
            <Button variant="neon" asChild>
              <Link href={`/analyse?url=${encodeURIComponent(shop.shop_url)}`}>
                Analyser
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Produits de la boutique */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Produits de la Boutique
          </CardTitle>
          <CardDescription>
            {products.length} produit{products.length > 1 ? 's' : ''} trouvé{products.length > 1 ? 's' : ''}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.map((product) => (
                <Card key={product.id} className="hover:glow-box transition-all">
                  <CardHeader>
                    <CardTitle className="text-lg line-clamp-2">{product.product_name}</CardTitle>
                    <CardDescription>
                      Score: <span className="font-bold text-neon-blue">{Math.round(product.score_winner * 10) / 10}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {product.price && (
                      <div>
                        <span className="text-sm text-muted-foreground">Prix: </span>
                        <span className="font-semibold">{formatCurrency(product.price)}</span>
                      </div>
                    )}
                    {product.revenue_est_min && product.revenue_est_max && (
                      <div>
                        <span className="text-sm text-muted-foreground">CA estimé: </span>
                        <span className="font-semibold text-sm">
                          {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}/mois
                        </span>
                      </div>
                    )}
                    {product.category && (
                      <div>
                        <span className="text-xs px-2 py-1 rounded bg-accent">{product.category}</span>
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button variant="outline" className="flex-1" asChild>
                        <a href={product.product_url} target="_blank" rel="noopener noreferrer">
                          Voir le produit
                        </a>
                      </Button>
                      <Button variant="outline" className="flex-1" asChild>
                        <Link href={`/analyse?url=${encodeURIComponent(product.product_url)}`}>
                          Analyser
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Aucun produit trouvé pour cette boutique.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

