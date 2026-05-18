import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [accountNumber, setAccountNumber] = useState('')
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(accountNumber.trim(), pin)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your account number and PIN.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-box">
        <div className="login-logo">
          <h1>ATM Banking</h1>
          <p>Secure internet banking</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Account Number</label>
            <input
              type="text"
              placeholder="ACC0000001"
              value={accountNumber}
              onChange={e => setAccountNumber(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>PIN</label>
            <input
              type="password"
              placeholder="Enter your PIN"
              value={pin}
              onChange={e => setPin(e.target.value)}
              required
              maxLength={8}
            />
          </div>
          <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>


      </div>
    </div>
  )
}
