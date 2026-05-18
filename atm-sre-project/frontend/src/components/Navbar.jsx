import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { logout, accountNumber } = useAuth()

  return (
    <nav className="navbar">
      <span className="navbar-brand">ATM Banking</span>
      <div className="navbar-links">
        <NavLink to="/" end className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>Dashboard</NavLink>
        <NavLink to="/deposit-withdraw" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>Deposit/Withdraw</NavLink>
        <NavLink to="/transfer" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>Transfer</NavLink>
        <NavLink to="/history" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>History</NavLink>
        <NavLink to="/cards" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>Cards</NavLink>
        <button className="btn btn-ghost" style={{ padding: '6px 14px', fontSize: '0.85rem' }} onClick={logout}>
          Logout
        </button>
      </div>
    </nav>
  )
}
