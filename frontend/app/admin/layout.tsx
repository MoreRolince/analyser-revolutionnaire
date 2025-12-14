import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Administration - MarketPulse Africa',
  description: 'Panneau d\'administration MarketPulse Africa',
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-white">
      {children}
    </div>
  )
}




export const metadata: Metadata = {
  title: 'Administration - MarketPulse Africa',
  description: 'Panneau d\'administration MarketPulse Africa',
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-white">
      {children}
    </div>
  )
}



