import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { Plus, Trash2, Users, Kanban, X, Briefcase } from 'lucide-react'

const EMPTY = { title: '', department: '', location: '', description: '', required_skills: '' }

export default function Jobs({ navigate }) {
  const [jobs, setJobs] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  const reload = async () => setJobs(await api.listJobs())
  useEffect(() => { reload().catch(e => setError(e.message)) }, [])

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.createJob(form)
      setForm(EMPTY)
      setShowForm(false)
      await reload()
    } catch (err) { setError(err.message) }
  }

  const remove = async (id) => {
    if (!confirm('Delete this job?')) return
    await api.deleteJob(id)
    reload()
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Open Jobs</h1>
          <p className="muted" style={{ margin: 0 }}>Manage your open roles and requirements.</p>
        </div>
        <button className="btn primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? <><X size={16} /> Cancel</> : <><Plus size={16} /> New Job</>}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && (
        <form className="card form" onSubmit={submit}>
          <h3 style={{ marginBottom: 16 }}>Create a New Job</h3>
          <label>Title<input required value={form.title}
            onChange={e => setForm({ ...form, title: e.target.value })} placeholder="e.g. Senior Software Engineer" /></label>
          <div className="row">
            <label>Department<input value={form.department}
              onChange={e => setForm({ ...form, department: e.target.value })} placeholder="e.g. Engineering" /></label>
            <label>Location<input value={form.location}
              onChange={e => setForm({ ...form, location: e.target.value })} placeholder="e.g. Remote, NY" /></label>
          </div>
          <label>Description<textarea required rows={4} value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Describe the role and responsibilities..." /></label>
          <label>Required skills (comma-separated)
            <input value={form.required_skills}
              placeholder="python, react, system design"
              onChange={e => setForm({ ...form, required_skills: e.target.value })} /></label>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
            <button className="btn primary" type="submit">Create Job</button>
          </div>
        </form>
      )}

      <div className="list">
        {jobs.length === 0 && !showForm && (
          <div className="empty" style={{ background: 'white', borderRadius: 12, padding: 48, boxShadow: 'var(--shadow-sm)' }}>
            <Briefcase size={48} color="var(--text-muted)" style={{ opacity: 0.3, marginBottom: 16 }} />
            <p>No jobs yet — create one to get started.</p>
            <button className="btn primary" onClick={() => setShowForm(true)} style={{ marginTop: 16 }}>
              <Plus size={16} /> Create First Job
            </button>
          </div>
        )}
        {jobs.map(j => (
          <div key={j.id} className="card job-card">
            <div className="job-head">
              <div>
                <h3>{j.title}</h3>
                <div className="muted small" style={{ marginTop: 6, fontWeight: 500 }}>
                  {j.department || '—'} • {j.location || '—'} • Posted {new Date(j.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="row gap">
                <button className="btn" onClick={() => navigate('candidates', j.id)}>
                  <Users size={16} /> Candidates
                </button>
                <button className="btn" onClick={() => navigate('pipeline', j.id)}>
                  <Kanban size={16} /> Pipeline
                </button>
                <button className="btn danger" onClick={() => remove(j.id)}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
            <p style={{ lineHeight: 1.5, marginTop: 12, marginBottom: 16 }}>{j.description}</p>
            {j.required_skills && (
              <div className="skill-row">
                {j.required_skills.split(',').map(s => s.trim()).filter(Boolean).map(s => (
                  <span key={s} className="chip">{s}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
