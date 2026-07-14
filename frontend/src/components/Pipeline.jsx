import { useEffect, useState } from 'react'
import { api, STAGE_LABELS, STAGES } from '../api.js'
import { AlertCircle, Filter, GripHorizontal } from 'lucide-react'

export default function Pipeline({ selectedJobId, setSelectedJobId }) {
  const [jobs, setJobs] = useState([])
  const [pipeline, setPipeline] = useState({ columns: [] })
  const [error, setError] = useState('')

  const reload = async () => {
    const js = await api.listJobs()
    setJobs(js)
    const p = await api.pipeline(selectedJobId || undefined)
    setPipeline(p)
  }
  useEffect(() => { reload().catch(e => setError(e.message)) }, [selectedJobId])

  const move = async (appId, newStage) => {
    setError('')
    try {
      await api.moveStage(appId, newStage)
      await reload()
    } catch (err) { setError(err.message) }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="page-head">
        <div>
          <h1>Hiring Pipeline</h1>
          <p className="muted" style={{ margin: 0 }}>Track candidates across all stages.</p>
        </div>
        <div className="row gap" style={{ background: 'white', padding: '6px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
          <Filter size={16} color="var(--text-muted)" />
          <select className="header-select" value={selectedJobId || ''} onChange={e => setSelectedJobId(e.target.value || null)} style={{ border: 'none', boxShadow: 'none', padding: '4px 8px' }}>
            <option value="">All Jobs</option>
            {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
          </select>
        </div>
      </div>
      
      {error && <div className="error"><AlertCircle size={18} /> {error}</div>}

      <div className="kanban">
        {STAGES.map(stage => {
          const col = pipeline.columns.find(c => c.stage === stage) || { applications: [] }
          return (
            <div key={stage} className="kanban-col">
              <div className="kanban-head">
                <span>{STAGE_LABELS[stage]}</span>
                <span className="count">{col.applications.length}</span>
              </div>
              <div className="kanban-body">
                {col.applications.length === 0 &&
                  <div className="empty">No candidates</div>}
                {col.applications.map(app => (
                  <div key={app.id} className="kanban-card">
                    <GripHorizontal size={16} color="#cbd5e1" style={{ position: 'absolute', top: 12, right: 12, cursor: 'grab' }} />
                    <div className="row spread" style={{ paddingRight: 24 }}>
                      <strong style={{ fontSize: 15 }}>{app.candidate?.full_name || 'Unknown'}</strong>
                      <span className={'score ' + scoreClass(app.match_score)}>
                        {app.match_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="muted small" style={{ fontWeight: 500 }}>{app.job?.title}</div>
                    {app.matched_skills && (
                      <div className="skill-row">
                        {app.matched_skills.split(', ').slice(0, 3).map(s => (
                          <span key={s} className="chip small ok">{s}</span>
                        ))}
                        {app.matched_skills.split(', ').length > 3 &&
                          <span className="muted small">+{app.matched_skills.split(', ').length - 3}</span>}
                      </div>
                    )}
                    <select
                      className="stage-select"
                      value={app.stage}
                      onChange={e => move(app.id, e.target.value)}
                    >
                      {STAGES.map(s => <option key={s} value={s}>{STAGE_LABELS[s]}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function scoreClass(s) {
  if (s >= 70) return 'high'
  if (s >= 40) return 'mid'
  return 'low'
}
