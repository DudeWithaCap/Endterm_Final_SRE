import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../context/AuthContext'

const TX_ICONS = { deposit: 'DEP', withdraw: 'WTH', transfer: 'TRF' }

function txAmount(tx, accountNumber) {
  const isCredit = tx.to_account === accountNumber && tx.type !== 'withdraw'
  const sign = isCredit ? '+' : '-'
  const cls = isCredit ? 'positive' : 'negative'
  return <span className={`tx-amount ${cls}`}>{sign}${tx.amount.toFixed(2)}</span>
}

export default function Dashboard() {
  const { accountNumber } = useAuth()
  const [account, setAccount] = useState(null)
  const [txs, setTxs] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [accRes, histRes] = await Promise.all([
          api.get(`/account/${accountNumber}`),
          api.get(`/history/${accountNumber}?page=1&page_size=5`),
        ])
        setAccount(accRes.data)
        setTxs(histRes.data.items || [])
      } catch (err) {
        setError('Failed to load account data.')
      }
    }
    load()
  }, [accountNumber])

  if (error) return <div className="page"><div className="alert alert-error">{error}</div></div>
  if (!account) return <div className="page"><div className="spinner">Loading…</div></div>

  return (
    <div className="page">
      <div className="card">
        <div className="balance-hero">
          <div className="balance-amount">${account.balance.toFixed(2)}</div>
          <div className="balance-label">Available Balance · {account.currency}</div>
        </div>
        <hr className="divider" />
        <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between' }}>
          <div>
            <div className="muted">Account Holder</div>
            <div style={{ fontWeight: 600 }}>{account.owner_name}</div>
          </div>
          <div>
            <div className="muted">Account Number</div>
            <div style={{ fontFamily: 'monospace', fontWeight: 600 }}>{account.account_number}</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3>Recent Transactions</h3>
          <Link to="/history" style={{ fontSize: '0.85rem' }}>View all →</Link>
        </div>

        {txs.length === 0 ? (
          <p className="muted">No transactions yet.</p>
        ) : (
          <ul className="tx-list">
            {txs.map((tx, i) => (
              <li key={i} className="tx-item">
                <div className={`tx-icon ${tx.type}`}>{TX_ICONS[tx.type]}</div>
                <div className="tx-meta">
                  <div className="tx-type">
                    {tx.type}
                    {tx.status === 'failed' && <span className="tx-status-failed">FAILED</span>}
                  </div>
                  <div className="tx-date">{new Date(tx.created_at).toLocaleString()}</div>
                </div>
                {txAmount(tx, accountNumber)}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="row">
        <Link to="/deposit-withdraw" className="btn btn-primary" style={{ flex: 1, textAlign: 'center' }}>Deposit / Withdraw</Link>
        <Link to="/transfer" className="btn btn-ghost" style={{ flex: 1, textAlign: 'center' }}>Transfer</Link>
      </div>
    </div>
  )
}
