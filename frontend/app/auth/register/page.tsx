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

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [plan, setPlan] = useState('3months')
  const [paymentProof, setPaymentProof] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast({
          title: 'Erreur',
          description: 'Le fichier est trop volumineux (max 5MB)',
          variant: 'destructive',
        })
        return
      }
      setPaymentProof(file)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (password !== confirmPassword) {
      toast({
        title: 'Erreur',
        description: 'Les mots de passe ne correspondent pas',
        variant: 'destructive',
      })
      return
    }

    if (!paymentProof) {
      toast({
        title: 'Erreur',
        description: 'Veuillez télécharger une preuve de paiement',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('email', email)
      formData.append('password', password)
      formData.append('plan', plan)
      if (paymentProof) {
        formData.append('payment_proof', paymentProof)
      }

      await api.post('/auth/register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      toast({
        title: 'Inscription réussie',
        description: 'Votre demande d\'inscription a été enregistrée.',
      })

      // Rediriger vers la page de confirmation
      router.push(`/auth/register/confirmation?email=${encodeURIComponent(email)}`)
    } catch (error: any) {
      console.error('Erreur inscription:', error)
      let errorMessage = 'Erreur lors de l\'inscription'
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || err.message).join(', ')
        }
      }
      
      toast({
        title: 'Erreur d\'inscription',
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
              S'inscrire
            </h1>
            <p className="text-sm md:text-base text-gray-600">
              Vous avez déjà un compte ?{' '}
              <Link 
                href="/auth/login" 
                className="text-gray-900 hover:text-gray-700 font-semibold transition-colors duration-200 hover:underline"
              >
                Connectez-vous
              </Link>
            </p>
          </div>

          {/* Formulaire */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-gray-900 mb-2">
                Nom et prénom
              </label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-300 rounded-xl"
              />
            </div>

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
                minLength={6}
                className="h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-300 rounded-xl"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-900 mb-2">
                Confirmer le mot de passe
              </label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
                className="h-12 bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-300 rounded-xl"
              />
            </div>

            <div>
              <label htmlFor="plan" className="block text-sm font-semibold text-gray-900 mb-2">
                Plan d'abonnement
              </label>
              <select
                id="plan"
                value={plan}
                onChange={(e) => setPlan(e.target.value)}
                className="w-full h-12 rounded-xl border-2 border-gray-200 bg-white text-gray-900 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900/20 transition-all duration-300 hover:border-gray-300 cursor-pointer"
                required
              >
                <option value="3months">3 mois</option>
                <option value="6months">6 mois</option>
              </select>
            </div>

            <div>
              <label htmlFor="paymentProof" className="block text-sm font-semibold text-gray-900 mb-2">
                Preuve de paiement <span className="text-red-500">*</span>
              </label>
              <Input
                id="paymentProof"
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileChange}
                required
                className="h-12 bg-white border-2 border-gray-200 text-gray-900 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 rounded-xl"
              />
              {paymentProof && (
                <p className="mt-2 text-sm text-gray-600">
                  Fichier sélectionné : {paymentProof.name}
                </p>
              )}
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-300 rounded-xl"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Inscription en cours...
                </>
              ) : (
                "S'inscrire"
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}

