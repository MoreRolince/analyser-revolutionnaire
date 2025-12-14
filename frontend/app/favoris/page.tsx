"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Star, Trash2, TrendingUp } from 'lucide-react'
import api from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { formatCurrency } from '@/lib/utils'

interface TrackedShop {
  id: number
  name: string
  url: string
  marketplace: string
  score: number
  estimated_revenue: number
  product_count: number
}

export default function FavorisPage() {
  const { toast } = useToast()
  const [shops, setShops] = useState<TrackedShop[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTrackedShops()
  }, [])

  const fetchTrackedShops = async () => {
    try {
      const response = await api.get('/favorites/shops')
      setShops(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement des boutiques:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (shopId: number) => {
    try {
      await api.delete(`/favorites/shops/${shopId}`)
      toast({
        title: 'Boutique retirée',
        description: 'La boutique a été retirée de vos favoris',
      })
      fetchTrackedShops()
    } catch (error: any) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Une erreur est survenue',
        variant: 'destructive',
      })
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">Chargement...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-4xl font-bold neon-blue mb-2 flex items-center gap-2">
          <Star className="h-8 w-8 fill-yellow-500 text-yellow-500" />
          Mes Boutiques Suivies
        </h1>
        <p className="text-muted-foreground">
          Suivez l'évolution de vos boutiques favorites
        </p>
      </div>

      {shops.length === 0 ? (
        <Card className="glass">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              Vous n'avez pas encore de boutiques suivies.
            </p>
            <Button className="mt-4" asChild>
              <a href="/analyse">Analyser une boutique</a>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shops.map((shop) => (
            <Card key={shop.id} className="glass">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{shop.name}</CardTitle>
                    <CardDescription>{shop.marketplace}</CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemove(shop.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Score</span>
                  <span className="text-2xl font-bold text-neon-blue">{shop.score}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">CA Estimé</span>
                  <span className="font-semibold">
                    {shop.estimated_revenue ? formatCurrency(shop.estimated_revenue) : 'N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Produits</span>
                  <span className="font-semibold">{shop.product_count}</span>
                </div>
                <Button variant="outline" className="w-full" asChild>
                  <a href={`/analyse?url=${encodeURIComponent(shop.url)}`}>
                    Voir l'analyse
                  </a>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

