import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { Briefcase, Users, Kanban, Calendar } from 'lucide-react'

export default function Dashboard({ navigate }) {
  const [stats, setStats] = useState({ jobs: 0, candidates: 0, apps: 0, interviews: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [jobs, cands, apps, interviews] = await Promise.all([
          api.listJobs(),
          api.listCandidates(),
          api.listApplications(),
          api.listInterviews(),
        ])
        setStats({
          jobs: jobs.length,
          candidates: cands.length,
          apps: apps.length,
          interviews: interviews.length,
        })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p className="muted">Loading dashboard data…</p>

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Overview</h1>
          <p className="muted" style={{ margin: 0 }}>Welcome back! Here's what's happening today.</p>
        </div>
      </div>
      
      <div className="stat-grid">
        <Card label="Open Jobs" value={stats.jobs} icon={Briefcase} onClick={() => navigate('jobs')} />
        <Card label="Total Candidates" value={stats.candidates} icon={Users} onClick={() => navigate('candidates')} />
        <Card label="Active Applications" value={stats.apps} icon={Kanban} onClick={() => navigate('pipeline')} />
        <Card label="Upcoming Interviews" value={stats.interviews} icon={Calendar} onClick={() => navigate('interviews')} />
      </div>
    </div>
  )
}

function Card({ label, value, icon: Icon, onClick }) {
  return (
    <button className="stat-card" onClick={onClick}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      <Icon className="stat-icon" size={64} />
    </button>
  )
}

