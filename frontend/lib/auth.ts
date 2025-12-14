import { cookies } from 'next/headers'

export interface User {
  id: number
  email: string
  name: string
  role: 'user' | 'admin'
  plan: 'trial' | '3months' | '6months' | null
  quota: {
    analyses: number
    aiRequests: number
    trackedShops: number
  }
}

export async function getServerSession(): Promise<User | null> {
  const cookieStore = await cookies()
  const token = cookieStore.get('token')?.value
  
  if (!token) {
    return null
  }
  
  try {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      return null
    }
    
    return await response.json()
  } catch {
    return null
  }
}

