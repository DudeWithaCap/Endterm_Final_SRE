import { useState } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function Transfer() {
  const { accountNumber } = useAuth()
  const [toAccount, setToAccount] = useState('')
  const [amount, setAmount] = useState('')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [confirm, setConfirm] = useState(false)

  function reset() {
    setToAccount('')
    setAmount('')
    setStatus(null)
    setConfirm(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!confirm) { setConfirm(true); return }

    setLoading(true)
    setStatus(null)
    try {
      await api.post('/transaction/transfer', {
        from_account: accountNumber,
        to_account: toAccount.trim(),
        amount: parseFloat(amount),
      })
      setStatus({ type: 'success', msg: `Transferred $${parseFloat(amount).toFixed(2)} to ${toAccount.trim()}.` })
      setToAccount('')
      setAmount('')
      setConfirm(false)
    } catch (err) {
      setStatus({ type: 'error', msg: err.response?.data?.detail || 'Transfer failed.' })
      setConfirm(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h1>Transfer</h1>
      <h2>Send funds to another account</h2>

      <div className="card">
        {status && <div className={`alert alert-${status.type}`}>{status.msg}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>From Account</label>
            <input type="text" value={accountNumber} disabled />
          </div>
          <div className="form-group">
            <label>To Account Number</label>
            <input
              type="text"
              placeholder="ACC0000002"
              value={toAccount}
              onChange={e => { setToAccount(e.target.value); setConfirm(false) }}
              required
            />
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
              Confirm transfer of <strong>${parseFloat(amount || 0).toFixed(2)}</strong> to <strong>{toAccount}</strong>? Click again to proceed.
            </div>
          )}

          <div className="row">
            <button type="submit" className="btn btn-primary" disabled={loading || !amount || !toAccount}>
              {loading ? 'Processing…' : confirm ? 'Confirm Transfer' : 'Transfer'}
            </button>
            {confirm && <button type="button" className="btn btn-ghost" onClick={reset}>Cancel</button>}
          </div>
        </form>
      </div>
    </div>
  )
}
