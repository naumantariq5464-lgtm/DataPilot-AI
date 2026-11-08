import { create } from 'zustand'
import type { AppUser } from '../types/auth'

interface AuthState {
  user:        AppUser | null
  loading:     boolean
  setUser:     (user: AppUser | null) => void
  setLoading:  (loading: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user:       null,
  loading:    true, // true until Firebase resolves initial auth state
  setUser:    (user) => set({ user }),
  setLoading: (loading) => set({ loading }),
}))
