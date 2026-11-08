import Header from '../components/layout/Header'
import { useAuth } from '../hooks/useAuth'

export default function Settings() {
  const { user } = useAuth()

  return (
    <div>
      <Header title="Settings" subtitle="Account and application preferences" />
      <div className="p-6 max-w-xl space-y-6">

        {/* Profile section */}
        <div className="card p-5">
          <h2 className="section-title mb-4">Profile</h2>
          <div className="space-y-3">
            <div>
              <p className="label">Email</p>
              <p className="text-sm text-primary">{user?.email ?? '—'}</p>
            </div>
            <div>
              <p className="label">Display Name</p>
              <p className="text-sm text-primary">{user?.name ?? '—'}</p>
            </div>
            <div>
              <p className="label">User ID</p>
              <p className="text-xs text-secondary font-mono">{user?.uid ?? '—'}</p>
            </div>
          </div>
        </div>

        {/* App info section */}
        <div className="card p-5">
          <h2 className="section-title mb-4">Application</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-secondary">Version</span>
              <span className="text-sm font-medium text-primary">1.0.0</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-secondary">AI Model</span>
              <span className="text-sm font-mono text-primary">deepseek-v4.1-flash-1017</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-secondary">Inference Provider</span>
              <span className="text-sm font-medium text-primary">Vultr Serverless</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-secondary">Max CSV Size</span>
              <span className="text-sm font-medium text-primary">10 MB</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
