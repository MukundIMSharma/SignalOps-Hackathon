import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import Approvals from './pages/Approvals'
import Investigations from './pages/Investigations'
import Overview from './pages/Overview'
import ReportPage from './pages/Report'
import Reports from './pages/Reports'
import Systems from './pages/Systems'

const NAV = [
  ['/', 'Overview'], ['/investigations', 'Investigations'], ['/reports', 'Incident reports'],
  ['/approvals', 'Approvals'], ['/systems', 'Systems / MCP'],
] as const

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <nav className="no-print sticky top-0 flex h-screen w-56 shrink-0 flex-col border-r border-zinc-800 bg-[#0c0d0f] px-3 py-4">
          <div className="mb-6 px-2">
            <div className="text-[15px] font-semibold tracking-tight text-zinc-50">SignalOps</div>
            <div className="text-[11px] text-zinc-500">NovaCommerce · incident investigator</div>
          </div>
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) => `mb-0.5 rounded px-2 py-1.5 text-sm ${isActive ? 'bg-zinc-800 text-zinc-50' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'}`}>
              {label}
            </NavLink>
          ))}
          <div className="mt-auto px-2 text-[11px] leading-relaxed text-zinc-600">
            Data via Synapse-generated MCP servers.<br />All actions are simulated.
          </div>
        </nav>
        <main className="min-w-0 flex-1 px-6 py-5">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/investigations" element={<Investigations />} />
            <Route path="/investigations/:id" element={<Investigations />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/:id" element={<ReportPage />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/systems" element={<Systems />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
