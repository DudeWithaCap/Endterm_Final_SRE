import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import CardManagement from './pages/CardManagement'
import Dashboard from './pages/Dashboard'
import DepositWithdraw from './pages/DepositWithdraw'
import History from './pages/History'
import Login from './pages/Login'
import Transfer from './pages/Transfer'

function Layout({ children }) {
  return (
    <>
      <Navbar />
      {children}
    </>
  )
}

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/" element={
        <ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>
      } />
      <Route path="/deposit-withdraw" element={
        <ProtectedRoute><Layout><DepositWithdraw /></Layout></ProtectedRoute>
      } />
      <Route path="/transfer" element={
        <ProtectedRoute><Layout><Transfer /></Layout></ProtectedRoute>
      } />
      <Route path="/history" element={
        <ProtectedRoute><Layout><History /></Layout></ProtectedRoute>
      } />
      <Route path="/cards" element={
        <ProtectedRoute><Layout><CardManagement /></Layout></ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
