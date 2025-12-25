"use client"

import { ReactNode } from 'react'
import Sidebar from './sidebar'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen bg-white">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="bg-white min-h-full">
          {children}
        </div>
      </main>
    </div>
  )
}

