"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/dashboard/dashboard-layout'
import DashboardContent from '@/components/dashboard/dashboard-content'
import { User } from '@/lib/auth'
import api from '@/lib/api'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      
      if (!token) {
        router.push('/auth/login')
        return
      }

      try {
        // Vérifier que le token est valide en récupérant les infos utilisateur
        const response = await api.get('/users/me')
        setUser(response.data)
      } catch (error) {
        // Token invalide ou expiré
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/auth/login')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [router])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
          <p className="text-lg font-semibold text-gray-900">Chargement...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <DashboardLayout>
      <DashboardContent user={user} />
    </DashboardLayout>
  )
}
