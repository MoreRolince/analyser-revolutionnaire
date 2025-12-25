"use client"

import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { 
  LayoutDashboard, 
  Package, 
  Store, 
  TrendingUp, 
  Search, 
  FileDown, 
  ShoppingCart,
  Settings,
  Zap,
  BarChart3,
  Shield
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, exact: true },
  { name: 'Top Produits', href: '/dashboard/winners?tab=products', icon: Package, pathMatch: '/dashboard/winners' },
  { name: 'Top Boutiques', href: '/dashboard/winners?tab=shops', icon: Store, pathMatch: '/dashboard/winners' },
  { name: 'Radar du Marché', href: '/market-radar', icon: TrendingUp, exact: true },
]

const researchNav = [
  { name: 'Analyser une URL', href: '/analyse', icon: Search, exact: true },
]

export default function Sidebar() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const [isAdmin, setIsAdmin] = useState(false)
  
  // Vérifier si l'utilisateur est admin (uniquement côté client après le montage)
  useEffect(() => {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const user = JSON.parse(userStr)
        setIsAdmin(user.role === 'admin')
      }
    } catch {
      setIsAdmin(false)
    }
  }, [])

  return (
    <div className="flex flex-col h-screen w-64 bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <span className="text-xl font-black bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
          Revenux
        </span>
        <Settings className="h-4 w-4 text-gray-400 cursor-pointer hover:text-gray-900 transition-colors" />
      </div>

      {/* Navigation principale */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {navigation.map((item) => {
          const itemPath = item.href.split('?')[0]
          const itemTab = item.href.includes('?tab=') ? item.href.split('?tab=')[1] : null
          const currentTab = searchParams?.get('tab')
          
          let isActive = false
          if (item.exact) {
            // Pour les pages exactes, vérifier uniquement le pathname
            isActive = pathname === itemPath
          } else if (item.pathMatch) {
            // Pour les pages avec pathMatch (comme winners), vérifier le pathname ET le tab
            const pathMatches = pathname?.startsWith(item.pathMatch) || pathname === itemPath
            if (itemTab) {
              // Si l'item a un tab spécifique, vérifier que le tab actuel correspond
              isActive = pathMatches && (currentTab === itemTab || (!currentTab && itemTab === 'products'))
            } else {
              isActive = pathMatches
            }
          } else {
            isActive = pathname === itemPath || pathname?.startsWith(itemPath + '/')
          }
          
          const Icon = item.icon
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gray-900 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}

        {/* Section Admin (si admin) */}
        {isAdmin && (
          <div className="pt-6 mt-6 border-t border-gray-200">
            <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Administration
            </p>
            <Link
              href="/admin"
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                pathname === '/admin'
                  ? "bg-gray-900 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Shield className="h-5 w-5" />
              Panel Admin
            </Link>
          </div>
        )}

        {/* Section Research & Tracking */}
        <div className="pt-6 mt-6 border-t border-gray-200">
          <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Recherche & Suivi
          </p>
          {researchNav.map((item) => {
            const itemPath = item.href.split('?')[0]
            const isActive = item.exact 
              ? pathname === itemPath
              : pathname === itemPath || pathname?.startsWith(itemPath + '/')
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-gray-900 text-white shadow-sm"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.name}
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

