"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'
import { Shield } from 'lucide-react'

export default function AdminLoginPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // OAuth2PasswordRequestForm attend application/x-www-form-urlencoded
      const formDataEncoded = new URLSearchParams()
      formDataEncoded.append('username', formData.email)
      formDataEncoded.append('password', formData.password)
      
      const response = await api.post('/auth/login', formDataEncoded.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      const { access_token, token_type } = response.data

      // Stocker le token temporairement pour la requête /me
      const tempToken = localStorage.getItem('token')
      localStorage.setItem('token', access_token)

      // Récupérer les informations de l'utilisateur
      const userResponse = await api.get('/auth/me')
      const user = userResponse.data

      // Vérifier que l'utilisateur est admin
      if (user.role !== 'admin') {
        toast({
          title: 'Accès refusé',
          description: 'Cette interface est réservée aux administrateurs.',
          variant: 'destructive',
        })
        setLoading(false)
        return
      }

      // Stocker le token et les données utilisateur
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))

      toast({
        title: 'Connexion réussie',
        description: `Bienvenue ${user.name} !`,
      })

      // Forcer le rechargement pour que le serveur puisse vérifier le token
      window.location.href = '/admin'
    } catch (error: any) {
      let errorMessage = 'Email ou mot de passe incorrect'
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (detail.includes('attente') || detail.includes('validation')) {
          errorMessage = detail
        } else if (detail.includes('rejeté')) {
          errorMessage = detail
        } else {
          errorMessage = detail
        }
      }
      
      toast({
        title: 'Erreur de connexion',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:20px_20px]" />
      
      <Card className="w-full max-w-md glass border-purple-500/20 shadow-2xl shadow-purple-500/10 relative z-10">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full bg-purple-500/20 border border-purple-500/30">
              <Shield className="h-8 w-8 text-purple-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-center bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Administration
          </CardTitle>
          <CardDescription className="text-center text-muted-foreground">
            Accès réservé aux administrateurs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email administrateur
              </label>
              <Input
                id="email"
                type="email"
                placeholder="admin@revenux.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="bg-slate-900/50 border-purple-500/20 focus:border-purple-500"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Mot de passe
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                className="bg-slate-900/50 border-purple-500/20 focus:border-purple-500"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
              disabled={loading}
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Vous êtes un utilisateur ?{' '}
              <Link href="/auth/login" className="text-purple-400 hover:text-purple-300 underline">
                Connexion utilisateur
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import api from '@/lib/api'
import { Shield } from 'lucide-react'

export default function AdminLoginPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // OAuth2PasswordRequestForm attend application/x-www-form-urlencoded
      const formDataEncoded = new URLSearchParams()
      formDataEncoded.append('username', formData.email)
      formDataEncoded.append('password', formData.password)
      
      const response = await api.post('/auth/login', formDataEncoded.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      const { access_token, token_type } = response.data

      // Stocker le token temporairement pour la requête /me
      const tempToken = localStorage.getItem('token')
      localStorage.setItem('token', access_token)

      // Récupérer les informations de l'utilisateur
      const userResponse = await api.get('/auth/me')
      const user = userResponse.data

      // Vérifier que l'utilisateur est admin
      if (user.role !== 'admin') {
        toast({
          title: 'Accès refusé',
          description: 'Cette interface est réservée aux administrateurs.',
          variant: 'destructive',
        })
        setLoading(false)
        return
      }

      // Stocker le token et les données utilisateur
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))

      toast({
        title: 'Connexion réussie',
        description: `Bienvenue ${user.name} !`,
      })

      // Forcer le rechargement pour que le serveur puisse vérifier le token
      window.location.href = '/admin'
    } catch (error: any) {
      let errorMessage = 'Email ou mot de passe incorrect'
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (detail.includes('attente') || detail.includes('validation')) {
          errorMessage = detail
        } else if (detail.includes('rejeté')) {
          errorMessage = detail
        } else {
          errorMessage = detail
        }
      }
      
      toast({
        title: 'Erreur de connexion',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:20px_20px]" />
      
      <Card className="w-full max-w-md glass border-purple-500/20 shadow-2xl shadow-purple-500/10 relative z-10">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full bg-purple-500/20 border border-purple-500/30">
              <Shield className="h-8 w-8 text-purple-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-center bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Administration
          </CardTitle>
          <CardDescription className="text-center text-muted-foreground">
            Accès réservé aux administrateurs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email administrateur
              </label>
              <Input
                id="email"
                type="email"
                placeholder="admin@revenux.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="bg-slate-900/50 border-purple-500/20 focus:border-purple-500"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Mot de passe
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                className="bg-slate-900/50 border-purple-500/20 focus:border-purple-500"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
              disabled={loading}
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Vous êtes un utilisateur ?{' '}
              <Link href="/auth/login" className="text-purple-400 hover:text-purple-300 underline">
                Connexion utilisateur
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

