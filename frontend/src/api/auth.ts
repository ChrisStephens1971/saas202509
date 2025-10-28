import client from './client'
import type { LoginRequest, LoginResponse } from '../types/api'

export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await client.post<LoginResponse>('/api/token/', credentials)
    return response.data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token')
  },

  getAccessToken: (): string | null => {
    return localStorage.getItem('access_token')
  },

  getRefreshToken: (): string | null => {
    return localStorage.getItem('refresh_token')
  },

  setTokens: (access: string, refresh: string): void => {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  },
}
