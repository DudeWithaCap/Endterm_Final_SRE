import { createContext, useContext, useState } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [accountNumber, setAccountNumber] = useState(() => localStorage.getItem('account_number'))

  async function login(accountNumber, pin) {
    const res = await api.post('/auth/login', { account_number: accountNumber, pin })
    const t = res.data.access_token
    localStorage.setItem('token', t)
    localStorage.setItem('account_number', accountNumber)
    setToken(t)
    setAccountNumber(accountNumber)
  }

  async function logout() {
    try { await api.post('/auth/logout') } catch (_) {}
    localStorage.removeItem('token')
    localStorage.removeItem('account_number')
    setToken(null)
    setAccountNumber(null)
  }

  return (
    <AuthContext.Provider value={{ token, accountNumber, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
