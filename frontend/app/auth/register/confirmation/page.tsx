"use client"

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { CheckCircle2, Mail, Clock } from 'lucide-react'

export default function RegistrationConfirmationPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = searchParams.get('email')

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
      
      <div className="w-full max-w-2xl relative z-10">
        {/* Card */}
        <div className="bg-white rounded-3xl shadow-xl p-8 md:p-12 space-y-8 border border-gray-100 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-green-100 rounded-full blur-xl opacity-50"></div>
              <div className="relative bg-green-50 rounded-full p-6">
                <CheckCircle2 className="w-16 h-16 text-green-600" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="text-center space-y-4">
            <h1 className="text-3xl md:text-4xl font-black text-gray-900 tracking-tight">
              Inscription enregistrée
            </h1>
            <p className="text-base md:text-lg text-gray-600 max-w-xl mx-auto leading-relaxed">
              Vérifiez l'ensemble des informations renseignées
            </p>
          </div>

          {/* Info Box */}
          <div className="bg-gray-50 rounded-2xl p-6 md:p-8 space-y-6 border border-gray-100">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
                <Mail className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  Vérification en cours
                </h3>
                <p className="text-sm md:text-base text-gray-600 leading-relaxed">
                  {email ? (
                    <>
                      Nous avons bien reçu votre demande d'inscription pour <span className="font-semibold text-gray-900">{email}</span>. 
                      Notre équipe est en train de vérifier les informations que vous avez fournies.
                    </>
                  ) : (
                    <>
                      Nous avons bien reçu votre demande d'inscription. 
                      Notre équipe est en train de vérifier les informations que vous avez fournies.
                    </>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
                <Clock className="w-6 h-6 text-emerald-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  Notification de validation
                </h3>
                <p className="text-sm md:text-base text-gray-600 leading-relaxed">
                  Vous recevrez une notification une fois la validation terminée. 
                  Cela peut prendre quelques heures. Nous vous enverrons un email à l'adresse que vous avez renseignée.
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/login">
              <Button className="w-full sm:w-auto bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-300 rounded-xl px-8 py-6">
                Retour à la connexion
              </Button>
            </Link>
            <Link href="/">
              <Button className="w-full sm:w-auto bg-white border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 text-gray-900 font-semibold rounded-xl px-8 py-6 shadow-sm hover:shadow-md transition-all duration-300">
                Retour à l'accueil
              </Button>
            </Link>
          </div>

          {/* Additional Info */}
          <div className="text-center pt-4">
            <p className="text-xs md:text-sm text-gray-500">
              Des questions ? Contactez-nous à{' '}
              <a href="mailto:support@revenux.com" className="text-gray-900 font-semibold hover:underline">
                support@revenux.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

