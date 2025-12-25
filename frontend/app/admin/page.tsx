"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'
import { User } from '@/lib/auth'
import { Users, CreditCard, FileText, CheckCircle, XCircle, Clock, BarChart3, TrendingUp, UserCheck, UserX, Package } from 'lucide-react'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import { getApiUrl } from '@/lib/api'

// Fonction helper pour construire l'URL complète des fichiers uploadés
const getPaymentProofUrl = (proofUrl: string | null) => {
  if (!proofUrl) return null
  // Si l'URL commence déjà par http, la retourner telle quelle
  if (proofUrl.startsWith('http://') || proofUrl.startsWith('https://')) {
    return proofUrl
  }
  // Sinon, construire l'URL complète vers le backend
  const apiUrl = getApiUrl()
  return `${apiUrl}${proofUrl}`
}

interface PendingUser {
  id: number
  email: string
  name: string
  status: string
  created_at: string
}

interface PendingPayment {
  id: number
  user_id: number
  user_email: string
  plan: string
  amount: number
  proof_url: string
  status: string
  created_at: string
}

interface AdminStats {
  total_users: number
  active_users: number
  pending_users: number
  users_by_status: Record<string, number>
  users_by_plan: Record<string, number>
  pending_payments: number
}

interface ActiveUser {
  id: number
  email: string
  name: string
  status: string
  plan: string | null
  created_at: string
}

interface ProductCheck {
  total_products: number
  products_with_name_and_url: number
  products_complete: number
  valid_products_count: number
  marketplace_stats?: Array<{
    marketplace: string
    total: number
    avec_nom_url: number
  }>
  sample_products?: Array<{
    id: number
    name: string
    url: string
  }>
}

export default function AdminPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [user, setUser] = useState<User | null>(null)
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([])
  const [pendingPayments, setPendingPayments] = useState<PendingPayment[]>([])
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([])
  const [productCheck, setProductCheck] = useState<ProductCheck | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté et est admin
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    
    if (!storedUser || !token) {
      router.push('/admin/login')
      return
    }

    const userData = JSON.parse(storedUser)
    if (userData.role !== 'admin') {
      toast({
        title: 'Accès refusé',
        description: 'Vous devez être administrateur pour accéder à cette page.',
        variant: 'destructive',
      })
      router.push('/admin/login')
      return
    }

    setUser(userData)
    fetchAdminData()
  }, [router, toast])

  const fetchAdminData = async () => {
    try {
      const [usersRes, paymentsRes, statsRes, activeUsersRes, productCheckRes] = await Promise.all([
        api.get('/admin/users/pending'),
        api.get('/admin/payments/pending'),
        api.get('/admin/stats'),
        api.get('/admin/users?status=approved'),
        api.get('/winners/check-products').catch(() => ({ data: null }))
      ])
      
      // S'assurer que les données sont des tableaux
      const users = Array.isArray(usersRes.data) ? usersRes.data : []
      const payments = Array.isArray(paymentsRes.data) ? paymentsRes.data : []
      const activeUsersData = Array.isArray(activeUsersRes.data) ? activeUsersRes.data : []
      
      setPendingUsers(users)
      setPendingPayments(payments)
      setStats(statsRes.data)
      setActiveUsers(activeUsersData.map((u: any) => ({
        id: u.id,
        email: u.email,
        name: u.name,
        status: u.status,
        plan: u.plan,
        created_at: u.created_at
      })))
      if (productCheckRes.data) {
        setProductCheck(productCheckRes.data)
      }
    } catch (error: any) {
      console.error('Erreur lors du chargement des données admin:', error)
      
      // Gérer les erreurs de validation
      let errorMessage = 'Impossible de charger les données admin.'
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || err.message).join(', ')
        } else if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        }
      }
      
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleApproveUser = async (userId: number, approve: boolean) => {
    try {
      await api.post(`/admin/users/${userId}/approve?approve=${approve}`)
      toast({
        title: approve ? 'Utilisateur approuvé' : 'Utilisateur rejeté',
        description: `L'utilisateur a été ${approve ? 'approuvé' : 'rejeté'} avec succès.`,
      })
      fetchAdminData()
    } catch (error: any) {
      let errorMessage = 'Une erreur est survenue.'
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join(', ')
        } else if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else {
          errorMessage = JSON.stringify(error.response.data.detail)
        }
      }
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive',
      })
    }
  }

  const handleApprovePayment = async (paymentId: number, approve: boolean) => {
    try {
      await api.post(`/admin/payments/${paymentId}/approve`, { approve })
      toast({
        title: approve ? 'Paiement approuvé' : 'Paiement rejeté',
        description: `Le paiement a été ${approve ? 'approuvé' : 'rejeté'} avec succès.`,
      })
      fetchAdminData()
    } catch (error: any) {
      let errorMessage = 'Une erreur est survenue.'
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join(', ')
        } else if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else {
          errorMessage = JSON.stringify(error.response.data.detail)
        }
      }
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive',
      })
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen bg-white">
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 border-4 border-gray-200 border-t-gray-600 rounded-full animate-spin"></div>
            <p className="text-lg font-semibold text-gray-900">Chargement...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-black text-gray-900 tracking-tight mb-2">Panneau Administrateur</h1>
            <p className="text-gray-600 text-base">Gestion des utilisateurs et paiements</p>
          </div>
          <Button 
            className="bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-900 rounded-xl font-semibold"
            onClick={() => {
              localStorage.removeItem('token')
              localStorage.removeItem('user')
              router.push('/admin/login')
            }}
          >
            Déconnexion
          </Button>
        </div>

        {/* Statistiques */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium mb-1">Total Utilisateurs</p>
                    <p className="text-3xl font-black text-gray-900">{stats.total_users}</p>
                  </div>
                  <Users className="h-10 w-10 text-gray-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium mb-1">Utilisateurs Actifs</p>
                    <p className="text-3xl font-black text-gray-900">{stats.active_users}</p>
                  </div>
                  <UserCheck className="h-10 w-10 text-green-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium mb-1">En Attente</p>
                    <p className="text-3xl font-black text-gray-900">{stats.pending_users}</p>
                  </div>
                  <Clock className="h-10 w-10 text-yellow-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-2xl shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium mb-1">Paiements en Attente</p>
                    <p className="text-3xl font-black text-gray-900">{stats.pending_payments}</p>
                  </div>
                  <CreditCard className="h-10 w-10 text-orange-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Stats par abonnement */}
        {stats && stats.users_by_plan && (
          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-gray-900 font-bold flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Utilisateurs par Abonnement
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(stats.users_by_plan).map(([plan, count]) => (
                  <div key={plan} className="p-4 rounded-xl bg-gray-50 border border-gray-200">
                    <p className="text-sm text-gray-600 font-medium mb-1">
                      {plan === 'trial' ? 'Essai gratuit' : plan === '3months' ? '3 mois' : plan === '6months' ? '6 mois' : plan}
                    </p>
                    <p className="text-2xl font-black text-gray-900">{count}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Vérification des produits */}
        {productCheck && (
          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-gray-900 font-bold flex items-center gap-2">
                <Package className="h-5 w-5" />
                Vérification des Produits
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-gray-50 border border-gray-200">
                  <p className="text-sm text-gray-600 font-medium mb-1">Total Produits</p>
                  <p className="text-2xl font-black text-gray-900">{productCheck.total_products}</p>
                </div>
                <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
                  <p className="text-sm text-blue-600 font-medium mb-1">Avec Nom + URL</p>
                  <p className="text-2xl font-black text-blue-900">{productCheck.products_with_name_and_url}</p>
                </div>
                <div className="p-4 rounded-xl bg-green-50 border border-green-200">
                  <p className="text-sm text-green-600 font-medium mb-1">Complets (avec image)</p>
                  <p className="text-2xl font-black text-green-900">{productCheck.products_complete}</p>
                </div>
                <div className="p-4 rounded-xl bg-orange-50 border border-orange-200">
                  <p className="text-sm text-orange-600 font-medium mb-1">Affichables</p>
                  <p className="text-2xl font-black text-orange-900">{productCheck.valid_products_count}</p>
                </div>
              </div>

              {productCheck.marketplace_stats && productCheck.marketplace_stats.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Par Marketplace</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {productCheck.marketplace_stats.map((stat) => (
                      <div key={stat.marketplace} className="p-3 rounded-xl bg-gray-50 border border-gray-200">
                        <p className="text-xs text-gray-500 uppercase font-semibold mb-1">{stat.marketplace}</p>
                        <p className="text-lg font-black text-gray-900">{stat.avec_nom_url} / {stat.total}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {productCheck.sample_products && productCheck.sample_products.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Exemples de produits valides</h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {productCheck.sample_products.map((product) => (
                      <div key={product.id} className="p-3 rounded-xl bg-gray-50 border border-gray-200">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-gray-900">{product.name}</p>
                            <p className="text-xs text-gray-500 mt-1">{product.url}</p>
                            <div className="flex items-center gap-3 mt-2">
                              <span className="text-xs text-gray-600">Marketplace: {product.marketplace}</span>
                              <span className="text-xs text-gray-600">Score: {product.score}</span>
                              {product.price && <span className="text-xs text-gray-600">Prix: {product.price} FCFA</span>}
                            </div>
                          </div>
                          <div className={`px-2 py-1 rounded text-xs font-semibold ${
                            product.has_image ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {product.has_image ? 'Image ✓' : 'Pas d\'image'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList className="bg-gray-100 rounded-xl p-1 border border-gray-200">
          <TabsTrigger value="active" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600">
            <UserCheck className="mr-2 h-4 w-4" />
            Utilisateurs Actifs ({activeUsers.length})
          </TabsTrigger>
          <TabsTrigger value="users" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600">
            <Users className="mr-2 h-4 w-4" />
            En Attente ({pendingUsers.length})
          </TabsTrigger>
          <TabsTrigger value="payments" className="rounded-lg data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600">
            <CreditCard className="mr-2 h-4 w-4" />
            Paiements ({pendingPayments.length})
          </TabsTrigger>
        </TabsList>

        {/* Utilisateurs Actifs */}
        <TabsContent value="active" className="space-y-4">
          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-gray-900 font-bold">Utilisateurs Actifs</CardTitle>
              <CardDescription className="text-gray-600">Liste des utilisateurs approuvés avec leur type d'abonnement</CardDescription>
            </CardHeader>
            <CardContent>
              {activeUsers.length === 0 ? (
                <div className="text-center text-gray-600 py-12">
                  Aucun utilisateur actif
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nom</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Abonnement</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date d'inscription</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {activeUsers.map((activeUser) => (
                        <tr key={activeUser.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4">
                            <p className="font-semibold text-gray-900">{activeUser.name}</p>
                          </td>
                          <td className="px-6 py-4">
                            <p className="text-gray-600">{activeUser.email}</p>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              activeUser.plan === '3months' 
                                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                : activeUser.plan === '6months'
                                ? 'bg-green-50 text-green-700 border border-green-200'
                                : 'bg-gray-100 text-gray-700 border border-gray-200'
                            }`}>
                              {activeUser.plan === '3months' ? '3 mois' : activeUser.plan === '6months' ? '6 mois' : 'Essai gratuit'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <p className="text-sm text-gray-600">
                              {activeUser.created_at ? new Date(activeUser.created_at).toLocaleDateString('fr-FR') : 'N/A'}
                            </p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-gray-900 font-bold">Utilisateurs en attente de validation</CardTitle>
              <CardDescription className="text-gray-600">
                Approuvez ou rejetez les demandes d'inscription
              </CardDescription>
            </CardHeader>
            <CardContent>
              {pendingUsers.length === 0 ? (
                <div className="text-center text-gray-600 py-12">
                  Aucun utilisateur en attente
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingUsers.map((pendingUser) => (
                    <div
                      key={pendingUser.id}
                      className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors gap-4"
                    >
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{pendingUser.name}</div>
                        <div className="text-sm text-gray-600">{pendingUser.email}</div>
                        {pendingUser.created_at && (
                          <div className="text-xs text-gray-500 mt-1">
                            Inscrit le {new Date(pendingUser.created_at).toLocaleDateString('fr-FR')}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          className="bg-green-100 hover:bg-green-200 text-green-700 border border-green-300 rounded-xl font-semibold"
                          size="sm"
                          onClick={() => handleApproveUser(pendingUser.id, true)}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Approuver
                        </Button>
                        <Button
                          className="bg-red-100 hover:bg-red-200 text-red-700 border border-red-300 rounded-xl font-semibold"
                          size="sm"
                          onClick={() => handleApproveUser(pendingUser.id, false)}
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          Rejeter
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments" className="space-y-4">
          <Card className="bg-white border border-gray-200 rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-gray-900 font-bold">Paiements en attente de validation</CardTitle>
              <CardDescription className="text-gray-600">
                Validez les preuves de paiement et activez les abonnements
              </CardDescription>
            </CardHeader>
            <CardContent>
              {pendingPayments.length === 0 ? (
                <div className="text-center text-gray-600 py-12">
                  Aucun paiement en attente
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingPayments.map((payment) => (
                    <div
                      key={payment.id}
                      className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors gap-4"
                    >
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{payment.user_email}</div>
                        <div className="text-sm text-gray-600">
                          Plan: {payment.plan === '3months' ? '3 mois' : payment.plan === '6months' ? '6 mois' : payment.plan} - Montant: {payment.amount} FCFA
                        </div>
                        {payment.proof_url && (
                          <a
                            href={getPaymentProofUrl(payment.proof_url) || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-gray-900 hover:text-gray-700 hover:underline flex items-center gap-1 mt-2 font-medium"
                          >
                            <FileText className="h-3 w-3" />
                            Voir la preuve de paiement
                          </a>
                        )}
                        {payment.created_at && (
                          <div className="text-xs text-gray-500 mt-1">
                            Reçu le {new Date(payment.created_at).toLocaleDateString('fr-FR')}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          className="bg-green-100 hover:bg-green-200 text-green-700 border border-green-300 rounded-xl font-semibold"
                          size="sm"
                          onClick={() => handleApprovePayment(payment.id, true)}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Approuver
                        </Button>
                        <Button
                          className="bg-red-100 hover:bg-red-200 text-red-700 border border-red-300 rounded-xl font-semibold"
                          size="sm"
                          onClick={() => handleApprovePayment(payment.id, false)}
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          Rejeter
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      </div>
    </DashboardLayout>
  )
}
