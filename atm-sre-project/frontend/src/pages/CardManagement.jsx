import { useEffect, useState } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function CardManagement() {
  const { accountNumber } = useAuth()
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionStatus, setActionStatus] = useState(null)

  // PIN change form
  const [currentPin, setCurrentPin] = useState('')
  const [newPin, setNewPin] = useState('')
  const [pinLoading, setPinLoading] = useState(false)
  const [pinStatus, setPinStatus] = useState(null)

  // Limit edit state
  const [editLimit, setEditLimit] = useState({}) // { cardNumber: value }

  async function loadCards() {
    try {
      const res = await api.get(`/card/account/${accountNumber}/cards`)
      setCards(res.data)
    } catch {
      setError('Failed to load cards.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadCards() }, [accountNumber])

  async function toggleBlock(card) {
    setActionStatus(null)
    const endpoint = card.is_blocked ? 'unblock' : 'block'
    try {
      await api.post(`/card/${card.card_number}/${endpoint}`, {})
      setActionStatus({ type: 'success', msg: `Card ${card.is_blocked ? 'unblocked' : 'blocked'} successfully.` })
      loadCards()
    } catch (err) {
      setActionStatus({ type: 'error', msg: err.response?.data?.detail || 'Action failed.' })
    }
  }

  async function updateLimit(card) {
    const newLimit = parseFloat(editLimit[card.card_number])
    if (!newLimit || newLimit <= 0) return
    setActionStatus(null)
    try {
      await api.put(`/card/${card.card_number}/limit`, { daily_limit: newLimit })
      setActionStatus({ type: 'success', msg: `Daily limit updated to $${newLimit.toFixed(2)}.` })
      setEditLimit(prev => ({ ...prev, [card.card_number]: '' }))
      loadCards()
    } catch (err) {
      setActionStatus({ type: 'error', msg: err.response?.data?.detail || 'Failed to update limit.' })
    }
  }

  async function handleChangePin(e) {
    e.preventDefault()
    setPinLoading(true)
    setPinStatus(null)
    try {
      await api.post('/card/change-pin', { current_pin: currentPin, new_pin: newPin })
      setPinStatus({ type: 'success', msg: 'PIN changed successfully.' })
      setCurrentPin('')
      setNewPin('')
    } catch (err) {
      setPinStatus({ type: 'error', msg: err.response?.data?.detail || 'Failed to change PIN.' })
    } finally {
      setPinLoading(false)
    }
  }

  if (loading) return <div className="page"><div className="spinner">Loading…</div></div>

  return (
    <div className="page">
      <h1>Card Management</h1>
      <h2>Manage your cards and security</h2>

      {error && <div className="alert alert-error">{error}</div>}
      {actionStatus && <div className={`alert alert-${actionStatus.type}`}>{actionStatus.msg}</div>}

      <div className="card">
        <h3>Your Cards</h3>
        {cards.length === 0 ? (
          <p className="muted">No cards found for this account.</p>
        ) : (
          cards.map(card => (
            <div key={card.card_number}>
              <div className="card-chip">
                <div>
                  <div className="card-number">{card.card_number}</div>
                  <div className="muted" style={{ marginTop: 4 }}>Daily limit: ${card.daily_limit.toFixed(2)}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span className={`badge ${card.is_blocked ? 'badge-blocked' : 'badge-active'}`}>
                    {card.is_blocked ? 'Blocked' : 'Active'}
                  </span>
                  <button
                    className={`btn ${card.is_blocked ? 'btn-success' : 'btn-danger'}`}
                    style={{ padding: '6px 14px', fontSize: '0.85rem' }}
                    onClick={() => toggleBlock(card)}
                  >
                    {card.is_blocked ? 'Unblock' : 'Block'}
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <input
                  type="number"
                  min="1"
                  step="1"
                  placeholder={`New limit (current: $${card.daily_limit.toFixed(2)})`}
                  value={editLimit[card.card_number] || ''}
                  onChange={e => setEditLimit(prev => ({ ...prev, [card.card_number]: e.target.value }))}
                  style={{ flex: 1, padding: '8px 12px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', fontSize: '0.9rem', outline: 'none' }}
                />
                <button className="btn btn-ghost" style={{ padding: '8px 16px' }}
                  onClick={() => updateLimit(card)}
                  disabled={!editLimit[card.card_number]}>
                  Update Limit
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <h3>Change PIN</h3>
        {pinStatus && <div className={`alert alert-${pinStatus.type}`}>{pinStatus.msg}</div>}
        <form onSubmit={handleChangePin}>
          <div className="form-group">
            <label>Current PIN</label>
            <input type="password" value={currentPin} onChange={e => setCurrentPin(e.target.value)} required maxLength={8} />
          </div>
          <div className="form-group">
            <label>New PIN</label>
            <input type="password" value={newPin} onChange={e => setNewPin(e.target.value)} required maxLength={8} minLength={4} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={pinLoading}>
            {pinLoading ? 'Changing…' : 'Change PIN'}
          </button>
        </form>
      </div>
    </div>
  )
}
