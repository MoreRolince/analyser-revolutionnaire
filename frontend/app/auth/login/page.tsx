"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Loader2 } from 'lucide-react'
import api from '@/lib/api'
import { Logo } from '@/components/logo'

export default function LoginPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // OAuth2PasswordRequestForm attend application/x-www-form-urlencoded
      const formDataEncoded = new URLSearchParams()
      formDataEncoded.append('username', email)
      formDataEncoded.append('password', password)
      
      const response = await api.post('/auth/login', formDataEncoded.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      const { access_token } = response.data

      // Stocker le token
      localStorage.setItem('token', access_token)

      // Récupérer les informations de l'utilisateur
      const userResponse = await api.get('/users/me')
      const user = userResponse.data
      
      localStorage.setItem('user', JSON.stringify(user))
      
      toast({
        title: 'Connexion réussie',
        description: `Bienvenue ${user.name} !`,
      })

      // Rediriger selon le rôle : admin vers /admin, autres vers /dashboard
      if (user.role === 'admin') {
        window.location.href = '/admin'
      } else {
        window.location.href = '/dashboard'
      }
    } catch (error: any) {
      console.error('Erreur connexion:', error)
      let errorMessage = 'Email ou mot de passe incorrect'
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((err: any) => err.msg || err.message).join(', ')
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
    <div className="min-h-screen flex items-center justify-center bg-white px-4 py-12 relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-white to-emerald-50/30" />
        <div className="absolute inset-0 opacity-[0.02]" style={{
          backgroundImage: 'linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)',
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Floating Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-20 right-20 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 left-20 w-80 h-80 bg-emerald-200/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </div>
      
      <div className="w-full max-w-md relative z-10">
        {/* Formulaire */}
        <div className="bg-white rounded-3xl shadow-xl p-8 md:p-10 space-y-6 border border-gray-100 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Logo avec animation */}
          <div className="flex justify-center mb-8">
            <span className="text-3xl md:text-4xl font-black bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Revenux
            </span>
          </div>

          {/* Titre avec animation */}
          <div className="text-center space-y-3 mb-8">
            <h1 className="text-3xl md:text-4xl font-black text-gray-900 tracking-tight">
              Se connecter
            </h1>
            <p className="text-sm md:text-base text-gray-600">
              Vous n'avez pas de compte ?{' '}
              <Link 
                href="/auth/register" 
                className="text-gray-900 hover:text-gray-700 font-semibold transition-colors duration-200 hover:underline inline-flex items-center gap-1 group"
              >
                Inscrivez-vous
                <span className="inline-block transform group-hover:translate-x-1 transition-transform duration-200">→</span>
              </Link>
            </p>
          </div>

          {/* Bouton Google */}
          <button
            type="button"
            onClick={() => {
              toast({
                title: 'Fonctionnalité à venir',
                description: 'La connexion Google sera disponible prochainement.',
              })
            }}
            className="w-full h-12 bg-white border-2 border-gray-200 rounded-xl hover:border-gray-300 hover:shadow-md flex items-center justify-center gap-3 transition-all duration-300 group"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span className="text-gray-700 font-medium">Se connecter avec Google</span>
          </button>

          {/* Séparateur */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-white text-gray-500 font-medium">ou</span>
            </div>
          </div>

          {/* Formulaire */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-900 mb-2">
                Adresse e-mail
              </label>
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-300 rounded-xl"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-900 mb-2">
                Mot de passe
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-300 rounded-xl"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember"
                  type="checkbox"
                  className="h-4 w-4 text-gray-900 focus:ring-gray-900 border-gray-300 rounded"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-gray-600">
                  Se souvenir de moi
                </label>
              </div>
              <Link href="/auth/forgot-password" className="text-sm text-gray-900 hover:text-gray-700 font-medium">
                Mot de passe oublié ?
              </Link>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-300 rounded-xl"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connexion en cours...
                </>
              ) : (
                'Se connecter'
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
