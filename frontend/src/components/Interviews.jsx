import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import { Plus, X, Calendar as CalendarIcon, Clock, Video, Phone, MapPin, AlignLeft, User } from 'lucide-react'

const EMPTY = {
  application_id: '',
  scheduled_date: '',
  scheduled_time: '',
  duration_minutes: 45,
  interviewer: '',
  interview_type: 'video',
  location: '',
  notes: '',
}

export default function Interviews() {
  const [interviews, setInterviews] = useState([])
  const [apps, setApps] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  const reload = async () => {
    const [ints, applications] = await Promise.all([
      api.listInterviews(),
      api.listApplications(),
    ])
    setInterviews(ints)
    setApps(applications)
  }
  useEffect(() => { reload().catch(e => setError(e.message)) }, [])

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const payload = {
        ...form,
        application_id: parseInt(form.application_id),
        duration_minutes: parseInt(form.duration_minutes),
      }
      await api.scheduleInterview(payload)
      setForm(EMPTY)
      setShowForm(false)
      await reload()
    } catch (err) { setError(err.message) }
  }

  const cancel = async (id) => {
    if (!confirm('Cancel this interview?')) return
    await api.cancelInterview(id)
    reload()
  }

  const updateStatus = async (id, status) => {
    await api.updateInterview(id, { status })
    reload()
  }

  // group by date for a calendar feel
  const grouped = useMemo(() => {
    const out = {}
    for (const i of interviews) {
      const d = i.scheduled_date
      if (!out[d]) out[d] = []
      out[d].push(i)
    }
    return Object.entries(out).sort(([a], [b]) => a.localeCompare(b))
  }, [interviews])

  const getTypeIcon = (type) => {
    if (type === 'video') return <Video size={14} />
    if (type === 'phone') return <Phone size={14} />
    return <MapPin size={14} />
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Interviews</h1>
          <p className="muted" style={{ margin: 0 }}>Schedule and manage candidate interviews.</p>
        </div>
        <button className="btn primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? <><X size={16} /> Cancel</> : <><Plus size={16} /> Schedule</>}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && (
        <form className="card form" onSubmit={submit}>
          <h3 style={{ marginBottom: 16 }}>Schedule New Interview</h3>
          <label>Application
            <select required value={form.application_id}
              onChange={e => setForm({ ...form, application_id: e.target.value })}>
              <option value="">— Pick candidate application —</option>
              {apps.map(a => (
                <option key={a.id} value={a.id}>
                  {a.candidate?.full_name} → {a.job?.title} (score {a.match_score.toFixed(0)}%)
                </option>
              ))}
            </select>
          </label>
          <div className="row">
            <label>Date
              <div style={{ position: 'relative' }}>
                <input type="date" required value={form.scheduled_date} style={{ width: '100%' }}
                  onChange={e => setForm({ ...form, scheduled_date: e.target.value })} />
              </div>
            </label>
            <label>Time
              <input type="time" required value={form.scheduled_time}
                onChange={e => setForm({ ...form, scheduled_time: e.target.value })} />
            </label>
            <label>Duration (min)
              <input type="number" min={15} step={15}
                value={form.duration_minutes}
                onChange={e => setForm({ ...form, duration_minutes: e.target.value })} />
            </label>
          </div>
          <div className="row">
            <label>Interviewer
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <User size={16} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
                <input value={form.interviewer} style={{ paddingLeft: 36, width: '100%' }} placeholder="e.g. John Smith"
                  onChange={e => setForm({ ...form, interviewer: e.target.value })} />
              </div>
            </label>
            <label>Type
              <select value={form.interview_type}
                onChange={e => setForm({ ...form, interview_type: e.target.value })}>
                <option value="video">Video Call</option>
                <option value="phone">Phone Call</option>
                <option value="onsite">On-site</option>
              </select>
            </label>
          </div>
          <label>Location / Link
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <MapPin size={16} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
              <input value={form.location} style={{ paddingLeft: 36, width: '100%' }}
                placeholder="https://meet.google.com/... or Room 4B"
                onChange={e => setForm({ ...form, location: e.target.value })} />
            </div>
          </label>
          <label>Notes
            <div style={{ position: 'relative' }}>
              <AlignLeft size={16} style={{ position: 'absolute', left: 10, top: 12, color: 'var(--text-muted)' }} />
              <textarea rows={2} value={form.notes} style={{ paddingLeft: 36, width: '100%' }} placeholder="Any instructions for the interviewer?"
                onChange={e => setForm({ ...form, notes: e.target.value })} />
            </div>
          </label>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
            <button className="btn primary" type="submit">Schedule Interview</button>
          </div>
        </form>
      )}

      {interviews.length === 0 && !showForm && (
        <div className="empty" style={{ background: 'white', borderRadius: 12, padding: 48, boxShadow: 'var(--shadow-sm)' }}>
          <CalendarIcon size={48} color="var(--text-muted)" style={{ opacity: 0.3, marginBottom: 16 }} />
          <p>No interviews scheduled yet.</p>
          <button className="btn primary" onClick={() => setShowForm(true)} style={{ marginTop: 16 }}>
            <Plus size={16} /> Schedule First Interview
          </button>
        </div>
      )}

      {grouped.map(([date, items]) => (
        <div key={date} className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ background: '#f8fafc', padding: '16px 24px', borderBottom: '1px solid var(--border-color)' }}>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--primary-color)' }}>
              <CalendarIcon size={18} />
              {new Date(date + 'T00:00:00').toLocaleDateString(undefined, {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
              })}
            </h3>
          </div>
          <table className="table" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th style={{ paddingLeft: 24 }}>Time</th>
                <th>Candidate</th>
                <th>Job</th>
                <th>Interviewer</th>
                <th>Type</th>
                <th>Status</th>
                <th style={{ paddingRight: 24 }}></th>
              </tr>
            </thead>
            <tbody>
              {items.map(i => (
                <tr key={i.id} style={{ opacity: i.status === 'cancelled' ? 0.6 : 1 }}>
                  <td style={{ paddingLeft: 24, fontWeight: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Clock size={14} className="muted" /> {i.scheduled_time}
                    </div>
                    <div className="muted small" style={{ marginTop: 4 }}>{i.duration_minutes} min</div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{i.candidate_name}</div>
                  </td>
                  <td className="muted">{i.job_title}</td>
                  <td>{i.interviewer || '—'}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, textTransform: 'capitalize' }}>
                      {getTypeIcon(i.interview_type)} {i.interview_type}
                    </div>
                  </td>
                  <td>
                    <select className="stage-select" value={i.status} style={{ padding: '4px 8px', marginTop: 0 }}
                      onChange={e => updateStatus(i.id, e.target.value)}>
                      <option value="scheduled">Scheduled</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </td>
                  <td style={{ paddingRight: 24, textAlign: 'right' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
                      {i.location && (
                        <div className="muted small" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <MapPin size={12} /> {i.location.length > 20 ? i.location.substring(0, 20) + '...' : i.location}
                        </div>
                      )}
                      {i.status !== 'cancelled' &&
                        <button className="btn small danger" onClick={() => cancel(i.id)} style={{ padding: '4px 8px' }}>Cancel</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
