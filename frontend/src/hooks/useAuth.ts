// Auth hook
import { useState, useCallback, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

interface User {
  id: string
  email: string
  name?: string
  role: string
  credits_balance: number
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
  })

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setAuth({ token, isAuthenticated: true })
    }
  }, [])

  const login = useCallback((token: string) => {
    localStorage.setItem('token', token)
    setAuth({ token, isAuthenticated: true })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setAuth({ user: null, token: null, isAuthenticated: false })
  }, [])

  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: () => api.get('/auth/me').then(r => r.data),
    enabled: auth.isAuthenticated,
    staleTime: 30000,
  })

  return {
    user: userData?.data || auth.user,
    token: auth.token,
    isAuthenticated: auth.isAuthenticated,
    login,
    logout,
  }
}
