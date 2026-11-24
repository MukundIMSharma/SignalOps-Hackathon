import { Link } from 'react-router-dom'
import { Card } from '../components/ui'

// Milestone 5 replaces this with the approval center (preview, approve/reject, execution, audit).
export default function Approvals() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-zinc-50">Approvals</h1>
      <Card>
        <p className="text-sm text-zinc-400">Approve / reject is being built (Milestone 5). Proposed actions are listed on each <Link to="/investigations" className="text-indigo-300 hover:underline">investigation</Link>; nothing executes without approval.</p>
      </Card>
    </div>
  )
}
