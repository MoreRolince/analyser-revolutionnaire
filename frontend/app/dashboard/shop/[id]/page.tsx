"use client"

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Store, Package, DollarSign, Trophy, Loader2 } from 'lucide-react'
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

export default function ShopDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const shopId = params.id as string
  const [shop, setShop] = useState<ShopDetails | null>(null)
  const [products, setProducts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [productsLoading, setProductsLoading] = useState(false)

  useEffect(() => {
    if (shopId) {
      fetchShopDetails()
    }
  }, [shopId])

  useEffect(() => {
    if (shop) {
      fetchShopProductsFromAnalyse()
    }
  }, [shop])

  const fetchShopDetails = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/winners/shops/${shopId}`)
      setShop(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement de la boutique:', error)
      setShop(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchShopProductsFromAnalyse = async () => {
    if (!shop || !shopId) return
    setProductsLoading(true)
    
    try {
      // Utiliser le nouvel endpoint qui retourne uniquement les produits winners de la boutique
      const response = await api.get(`/winners/shops/${shopId}/products`)
      const winnerProducts = response.data || []
      
      console.log(`✅ ${winnerProducts.length} produits winners trouvés pour la boutique`, winnerProducts)
      
      // Mapper les produits au format attendu par l'affichage
      const mappedProducts = winnerProducts.map((p: any) => ({
        product_title: p.product_name,
        title: p.product_name,
        name: p.product_name,
        product_name: p.product_name,
        product_url: p.product_url,
        url: p.product_url,
        price: p.price,
        promotedPrice: p.price, // Utiliser le prix comme prix promo si pas de distinction
        promo_price: p.price,
        original_price: p.price,
        images: p.product_image ? [p.product_image] : [],
        image: p.product_image,
        product_image: p.product_image,
        featuredImage: p.product_image,
        description: p.product_description,
        slug: p.product_url?.split('/products/')[1]?.split('/')[0] || '',
        marketplace: p.marketplace,
        score_winner: p.score_winner
      }))
      
      setProducts(mappedProducts)
      setProductsLoading(false)
    } catch (error: any) {
      console.error('Erreur lors de la récupération des produits winners:', error)
      if (error.response?.status === 404) {
        console.log('⚠️ Aucun produit winner trouvé pour cette boutique')
        setProducts([])
      }
      setProductsLoading(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </DashboardLayout>
    )
  }

  if (!shop) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Boutique non trouvée</p>
          <Button className="mt-4" onClick={() => router.back()}>
            Retour
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{shop.shop_name}</h1>
              <p className="text-gray-600 mt-1">{shop.shop_url}</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-900">
                <Store className="h-5 w-5 text-gray-700" />
                Marketplace
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-gray-900 uppercase">{shop.marketplace}</p>
            </CardContent>
          </Card>

          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-900">
                <Trophy className="h-5 w-5 text-gray-700" />
                Score Global
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-black text-gray-900">{Math.round(shop.score_global * 10) / 10}</p>
              <p className="text-sm text-gray-500 mt-1">sur 100</p>
            </CardContent>
          </Card>

          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-900">
                <DollarSign className="h-5 w-5 text-gray-700" />
                CA Estimé
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-gray-900">
                {shop.revenue_est_min && shop.revenue_est_max
                  ? `${formatCurrency(shop.revenue_est_min)} - ${formatCurrency(shop.revenue_est_max)}`
                  : 'N/A'}
              </p>
              <p className="text-sm text-gray-500 mt-1">par mois</p>
            </CardContent>
          </Card>

          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-900">
                <Package className="h-5 w-5 text-gray-700" />
                Produits Winners
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-black text-gray-900">{shop.winners_count}</p>
              <p className="text-sm text-gray-500 mt-1">produits performants</p>
            </CardContent>
          </Card>
        </div>

        {/* CTA Analyse */}
        <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between gap-4 flex-col md:flex-row">
              <div className="text-left space-y-1">
                <h3 className="font-semibold text-gray-900">Analyser cette boutique</h3>
                <p className="text-sm text-gray-600">
                  Obtenez une analyse détaillée avec scores, estimations et insights IA
                </p>
              </div>
              <Button className="bg-gray-900 hover:bg-gray-800 text-white rounded-xl px-5" asChild>
                <Link href={`/analyse?url=${encodeURIComponent(shop.shop_url)}`}>
                  Lancer l'analyse
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Produits Winners */}
        <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-900">
              <Package className="h-5 w-5 text-gray-700" />
              Produits Winners
            </CardTitle>
            <CardDescription>
              {products.length} produit{products.length > 1 ? 's' : ''} winner{products.length > 1 ? 's' : ''} détecté{products.length > 1 ? 's' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {productsLoading && (
              <div className="flex items-center gap-3 text-gray-700 mb-4">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Chargement des produits winners...</span>
              </div>
            )}

            {products.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {products.map((product, idx) => {
                  // Extraire le titre - essayer tous les champs possibles
                  const title = product.product_title || product.title || product.name || product.product_name || 'Produit'
                  
                  // Extraire l'image - vérifier toutes les variantes
                  let imageSrc = null
                  if (product.images && Array.isArray(product.images) && product.images.length > 0) {
                    imageSrc = product.images[0]
                  } else if (product.image) {
                    imageSrc = product.image
                  } else if (product.product_image) {
                    imageSrc = product.product_image
                  } else if (product.featuredImage) {
                    imageSrc = product.featuredImage
                  }
                  
                  // Extraire le prix - vérifier tous les champs
                  let priceValue = product.promotedPrice || product.promo_price || product.price || product.original_price
                  // Si priceValue est 0, null ou undefined, essayer encore
                  if (!priceValue || priceValue === 0) {
                    priceValue = product.price || product.promotedPrice || product.promo_price || null
                  }
                  
                  // Extraire l'URL
                  let productUrl = product.product_url || product.url
                  // Si pas d'URL mais un slug, construire l'URL
                  if (!productUrl && product.slug && shop?.shop_url) {
                    productUrl = `${shop.shop_url}/fr/products/${product.slug}`
                  }
                  
                  // Debug pour le premier produit
                  if (idx === 0) {
                    console.log('🔍 Produit #0:', {
                      raw: product,
                      title,
                      imageSrc,
                      priceValue,
                      productUrl
                    })
                  }
                  
                  return (
                    <Card key={idx} className="border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all">
                      <CardHeader>
                        <CardTitle className="text-lg line-clamp-2 text-gray-900 font-semibold">
                          {title}
                        </CardTitle>
                        {product.score_winner && (
                          <CardDescription className="text-gray-600">
                            Score: <span className="font-semibold text-gray-900">{Math.round((product.score_winner || 0) * 10) / 10}</span>
                          </CardDescription>
                        )}
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {imageSrc && (
                          <img
                            src={imageSrc}
                            alt={title}
                            className="w-full h-40 object-cover rounded-lg border border-gray-200"
                            onError={(e) => {
                              console.log('❌ Image échouée:', imageSrc)
                              e.currentTarget.style.display = 'none'
                            }}
                          />
                        )}
                        {priceValue ? (
                          <div className="text-base font-bold text-gray-900">
                            <span className="text-gray-600 font-normal">Prix: </span>
                            {formatCurrency(priceValue)} FCFA
                          </div>
                        ) : (
                          <div className="text-sm text-gray-500 italic">Prix non disponible</div>
                        )}
                        {product.revenue_est_min && product.revenue_est_max && (
                          <div className="text-sm">
                            <span className="text-gray-600">CA estimé: </span>
                            <span className="font-semibold">
                              {formatCurrency(product.revenue_est_min)} - {formatCurrency(product.revenue_est_max)}/mois
                            </span>
                          </div>
                        )}
                        {product.category && (
                          <div>
                            <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-800">{product.category}</span>
                          </div>
                        )}
                        <div className="flex gap-2 pt-2">
                          {productUrl ? (
                            <>
                              <Button variant="outline" className="flex-1" asChild>
                                <a href={productUrl} target="_blank" rel="noopener noreferrer">
                                  Voir le produit
                                </a>
                              </Button>
                              <Button variant="outline" className="flex-1" asChild>
                                <Link href={`/analyse?url=${encodeURIComponent(productUrl)}`}>
                                  Analyser
                                </Link>
                              </Button>
                            </>
                          ) : (
                            <Button variant="outline" className="w-full" disabled>
                              URL non disponible
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-700">
                {productsLoading ? (
                  <p>Chargement des produits winners en cours...</p>
                ) : (
                  <p>Aucun produit winner trouvé pour cette boutique.</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
