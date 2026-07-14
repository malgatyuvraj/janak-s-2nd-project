import { useState } from 'react'
import { LayoutDashboard, Briefcase, Users, Kanban, Calendar, Zap } from 'lucide-react'
import Dashboard from './components/Dashboard.jsx'
import Jobs from './components/Jobs.jsx'
import Candidates from './components/Candidates.jsx'
import Pipeline from './components/Pipeline.jsx'
import Interviews from './components/Interviews.jsx'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'jobs', label: 'Jobs', icon: Briefcase },
  { id: 'candidates', label: 'Candidates', icon: Users },
  { id: 'pipeline', label: 'Pipeline', icon: Kanban },
  { id: 'interviews', label: 'Interviews', icon: Calendar },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [selectedJobId, setSelectedJobId] = useState(null)

  const navigate = (t, jobId = null) => {
    if (jobId !== undefined) {
      setSelectedJobId(jobId)
    }
    setTab(t)
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo"><Zap size={20} /></span>
          <span>HireFlow AI</span>
        </div>
        <nav className="nav-links">
          {TABS.map(t => {
            const Icon = t.icon
            return (
              <button
                key={t.id}
                className={'nav-item' + (tab === t.id ? ' active' : '')}
                onClick={() => navigate(t.id)}
              >
                <Icon />
                {t.label}
              </button>
            )
          })}
        </nav>
      </aside>

      <div className="main-wrapper">
        <header className="top-header">
          {/* Top header can be used for user profile, search, or breadcrumbs */}
          <div className="row spread" style={{ width: '100%' }}>
            <h3 style={{ margin: 0, color: 'var(--text-muted)' }}>
              {TABS.find(t => t.id === tab)?.label}
            </h3>
            <div className="row gap">
              {/* Placeholder for user avatar */}
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary-light), var(--primary-color))' }}></div>
            </div>
          </div>
        </header>

        <main className="content">
          {tab === 'dashboard' && <Dashboard navigate={navigate} />}
          {tab === 'jobs' && <Jobs navigate={navigate} />}
          {tab === 'candidates' && <Candidates navigate={navigate} selectedJobId={selectedJobId} />}
          {tab === 'pipeline' && <Pipeline selectedJobId={selectedJobId} setSelectedJobId={setSelectedJobId} />}
          {tab === 'interviews' && <Interviews navigate={navigate} />}
        </main>
      </div>
    </div>
  )
}
