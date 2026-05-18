import { useState } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function DepositWithdraw() {
  const { accountNumber } = useAuth()
  const [tab, setTab] = useState('deposit')
  const [amount, setAmount] = useState('')
  const [status, setStatus] = useState(null) // { type: 'success'|'error', msg }
  const [loading, setLoading] = useState(false)
  const [confirm, setConfirm] = useState(false)

  function reset() {
    setAmount('')
    setStatus(null)
    setConfirm(false)
  }

  function handleTabChange(t) {
    setTab(t)
    reset()
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!confirm) { setConfirm(true); return }

    setLoading(true)
    setStatus(null)
    try {
      await api.post(`/transaction/${tab}`, {
        account_number: accountNumber,
        amount: parseFloat(amount),
      })
      setStatus({ type: 'success', msg: `${tab === 'deposit' ? 'Deposit' : 'Withdrawal'} of $${parseFloat(amount).toFixed(2)} completed.` })
      setAmount('')
      setConfirm(false)
    } catch (err) {
      setStatus({ type: 'error', msg: err.response?.data?.detail || 'Transaction failed.' })
      setConfirm(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h1>Deposit / Withdraw</h1>
      <h2>Manage your funds</h2>

      <div className="card">
        <div className="tabs">
          <button className={`tab-btn${tab === 'deposit' ? ' active' : ''}`} onClick={() => handleTabChange('deposit')}>Deposit</button>
          <button className={`tab-btn${tab === 'withdraw' ? ' active' : ''}`} onClick={() => handleTabChange('withdraw')}>Withdraw</button>
        </div>

        {status && (
          <div className={`alert alert-${status.type}`}>{status.msg}</div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Account</label>
            <input type="text" value={accountNumber} disabled />
          </div>
          <div className="form-group">
            <label>Amount (USD)</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="0.00"
              value={amount}
              onChange={e => { setAmount(e.target.value); setConfirm(false) }}
              required
            />
          </div>

          {confirm && (
            <div className="alert alert-warn">
              Confirm {tab} of <strong>${parseFloat(amount || 0).toFixed(2)}</strong>? Click again to proceed.
            </div>
          )}

          <div className="row">
            <button
              type="submit"
              className={`btn ${tab === 'deposit' ? 'btn-success' : 'btn-danger'}`}
              disabled={loading || !amount}
            >
              {loading ? 'Processing…' : confirm ? `Confirm ${tab}` : tab === 'deposit' ? 'Deposit' : 'Withdraw'}
            </button>
            {confirm && (
              <button type="button" className="btn btn-ghost" onClick={reset}>Cancel</button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
