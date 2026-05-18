import { useEffect, useState } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

const TX_ICONS = { deposit: 'DEP', withdraw: 'WTH', transfer: 'TRF' }

function txAmount(tx, accountNumber) {
  const isCredit = tx.to_account === accountNumber && tx.type !== 'withdraw'
  const sign = isCredit ? '+' : '-'
  const cls = isCredit ? 'positive' : 'negative'
  return <span className={`tx-amount ${cls}`}>{sign}${tx.amount.toFixed(2)}</span>
}

export default function History() {
  const { accountNumber } = useAuth()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const PAGE_SIZE = 15

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')
      try {
        const params = new URLSearchParams({ page, page_size: PAGE_SIZE })
        if (typeFilter) params.set('type', typeFilter)
        if (dateFrom) params.set('date_from', dateFrom)
        if (dateTo) params.set('date_to', dateTo)
        const res = await api.get(`/history/${accountNumber}?${params}`)
        setItems(res.data.items || [])
        setTotal(res.data.total || 0)
      } catch {
        setError('Failed to load transaction history.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [accountNumber, page, typeFilter, dateFrom, dateTo])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function handleFilterChange(setter) {
    return (e) => { setter(e.target.value); setPage(1) }
  }

  return (
    <div className="page">
      <h1>Transaction History</h1>
      <h2>{total} transaction{total !== 1 ? 's' : ''}</h2>

      <div className="filter-bar">
        <select value={typeFilter} onChange={handleFilterChange(setTypeFilter)}>
          <option value="">All types</option>
          <option value="deposit">Deposit</option>
          <option value="withdraw">Withdraw</option>
          <option value="transfer">Transfer</option>
        </select>
        <input type="date" value={dateFrom} onChange={handleFilterChange(setDateFrom)} title="From date" />
        <input type="date" value={dateTo} onChange={handleFilterChange(setDateTo)} title="To date" />
        {(typeFilter || dateFrom || dateTo) && (
          <button className="btn btn-ghost" style={{ padding: '7px 14px', fontSize: '0.85rem' }}
            onClick={() => { setTypeFilter(''); setDateFrom(''); setDateTo(''); setPage(1) }}>
            Clear
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        {loading ? (
          <div className="spinner">Loading…</div>
        ) : items.length === 0 ? (
          <p className="muted">No transactions match your filters.</p>
        ) : (
          <ul className="tx-list">
            {items.map((tx, i) => (
              <li key={i} className="tx-item">
                <div className={`tx-icon ${tx.type}`}>{TX_ICONS[tx.type]}</div>
                <div className="tx-meta">
                  <div className="tx-type">
                    {tx.type}
                    {tx.status === 'failed' && <span className="tx-status-failed">FAILED</span>}
                  </div>
                  <div className="tx-date">
                    {tx.from_account && tx.type === 'transfer' && `From: ${tx.from_account} → `}
                    {tx.to_account && tx.type === 'transfer' && `To: ${tx.to_account}`}
                    {' · '}{new Date(tx.created_at).toLocaleString()}
                  </div>
                </div>
                {txAmount(tx, accountNumber)}
              </li>
            ))}
          </ul>
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)}
            style={{ padding: '6px 14px' }}>← Prev</button>
          <span>Page {page} of {totalPages}</span>
          <button className="btn btn-ghost" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}
            style={{ padding: '6px 14px' }}>Next →</button>
        </div>
      )}
    </div>
  )
}
