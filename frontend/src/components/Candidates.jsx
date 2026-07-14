import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { UploadCloud, CheckCircle2, AlertCircle, FileText, Send, Users, ChevronRight, Briefcase, Star, Search } from 'lucide-react'

export default function Candidates({ navigate, selectedJobId }) {
  const [candidates, setCandidates] = useState([])
  const [jobs, setJobs] = useState([])
  const [ranked, setRanked] = useState(null)
  const [applyJobId, setApplyJobId] = useState(selectedJobId || '')
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  
  // Animation states
  const [shakeSelect, setShakeSelect] = useState(false)

  const fileRef = useRef()

  const reload = async () => {
    const [cs, js] = await Promise.all([api.listCandidates(), api.listJobs()])
    setCandidates(cs)
    setJobs(js)
    if (selectedJobId) {
      const r = await api.rankedCandidates(selectedJobId)
      setRanked(r)
    }
  }
  useEffect(() => { reload().catch(e => setError(e.message)) }, [selectedJobId])

  const handleUpload = async (e) => {
    e.preventDefault()
    setError('')
    setUploadStatus('')
    const fd = new FormData(e.target)
    const file = fileRef.current.files[0]
    if (!file) { setError('Pick a resume file first'); return }
    fd.set('file', file)
    setUploading(true)
    try {
      const c = await api.uploadResume(fd)
      setUploadStatus(`Parsed ${c.full_name}: ${c.skills ? c.skills.split(', ').length : 0} skills, ${c.experience_years} yrs exp.`)
      e.target.reset()
      setShowUpload(false)
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const apply = async (candidateId) => {
    if (!applyJobId) { 
      setShakeSelect(true)
      setTimeout(() => setShakeSelect(false), 500)
      setError('Please select a target job first before applying a candidate.')
      return 
    }
    setError('')
    try {
      await api.applyCandidate(parseInt(applyJobId), candidateId)
      if (selectedJobId) {
        const r = await api.rankedCandidates(selectedJobId)
        setRanked(r)
      } else {
        // Optional: show a success toast here
        setUploadStatus('Successfully applied candidate to job!')
        setTimeout(() => setUploadStatus(''), 3000)
      }
    } catch (err) { setError(err.message) }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, height: '100%' }}>
      <div className="page-head" style={{ marginBottom: 0 }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            Candidates
            {selectedJobId && <span className="badge" style={{ fontSize: 13, padding: '4px 10px', background: 'var(--primary-light)', color: 'var(--primary-color)', borderRadius: 'var(--radius-full)' }}>Filtered: Job #{selectedJobId}</span>}
          </h1>
          <p className="muted" style={{ margin: 0 }}>Manage your talent pool and view AI match scores.</p>
        </div>
        <button className="btn primary" onClick={() => setShowUpload(!showUpload)}>
          <UploadCloud size={18} /> {showUpload ? 'Cancel Upload' : 'Upload Resume'}
        </button>
      </div>

      {error && <div className="error" style={{ animation: 'fadeIn 0.3s' }}><AlertCircle size={18} /> {error}</div>}
      {uploadStatus && <div className="ok" style={{ animation: 'fadeIn 0.3s' }}><CheckCircle2 size={18} /> {uploadStatus}</div>}

      {showUpload && (
        <form className="card form" onSubmit={handleUpload} style={{ animation: 'fadeIn 0.3s', border: '1px solid var(--primary-light)', background: 'linear-gradient(to right, #ffffff, #f8fafc)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{ padding: 12, background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))', borderRadius: 'var(--radius-md)', color: 'white' }}>
              <FileText size={24} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 18 }}>AI Resume Parser</h3>
              <p className="muted small" style={{ margin: '4px 0 0' }}>Upload a PDF or DOCX. Our AI will automatically extract the candidate's skills and experience.</p>
            </div>
          </div>
          
          <div className="row">
            <label>Full Name<input name="full_name" required placeholder="Jane Doe" style={{ background: 'white' }} /></label>
            <label>Email<input name="email" type="email" required placeholder="jane@example.com" style={{ background: 'white' }} /></label>
            <label>Phone<input name="phone" placeholder="(555) 123-4567" style={{ background: 'white' }} /></label>
          </div>
          
          <div className="row" style={{ alignItems: 'flex-end', marginTop: 8 }}>
            <label style={{ flex: 1 }}>Resume File
              <div style={{ position: 'relative' }}>
                <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" required style={{ width: '100%', padding: '8px 12px', background: 'white', border: '2px dashed var(--border-color)' }} />
              </div>
            </label>
            <button className="btn primary" disabled={uploading} style={{ height: 42, minWidth: 160 }}>
              {uploading ? 'Parsing AI...' : <><UploadCloud size={18} /> Process Resume</>}
            </button>
          </div>
        </form>
      )}

      {selectedJobId && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ background: 'linear-gradient(to right, #f8fafc, #ffffff)', padding: '20px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: 12 }}>
            <Star size={20} color="var(--warning-color)" />
            <h3 style={{ margin: 0 }}>AI Ranking Results</h3>
          </div>
          
          {!ranked && <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>Loading ranking data…</div>}
          
          {ranked && ranked.results.length === 0 && (
            <div className="empty" style={{ margin: 24, padding: 48 }}>
              <Users size={48} color="var(--text-muted)" style={{ opacity: 0.2, marginBottom: 16 }} />
              <p style={{ fontSize: 16, color: 'var(--text-main)' }}>No candidates applied yet.</p>
              <p className="muted">Apply candidates from the database below to see their match scores.</p>
            </div>
          )}
          
          {ranked && ranked.results.length > 0 && (
            <table className="table" style={{ margin: 0 }}>
              <thead>
                <tr>
                  <th style={{ width: 60, paddingLeft: 24 }}>Rank</th>
                  <th>Candidate</th>
                  <th style={{ width: 140 }}>Match Score</th>
                  <th>Core Skills</th>
                  <th style={{ width: 140 }}>Missing</th>
                  <th style={{ width: 120, paddingRight: 24 }}>Stage</th>
                </tr>
              </thead>
              <tbody>
                {ranked.results.map((r, i) => (
                  <tr key={r.application_id}>
                    <td style={{ paddingLeft: 24 }}>
                      <div style={{ width: 28, height: 28, borderRadius: '50%', background: i === 0 ? 'var(--warning-light)' : '#f1f5f9', color: i === 0 ? 'var(--warning-color)' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14 }}>
                        {i + 1}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: 15 }}>{r.candidate_name}</div>
                      <div className="muted small">{r.candidate_email}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={'score ' + scoreClass(r.match_score)} style={{ width: 56, textAlign: 'center' }}>
                          {r.match_score.toFixed(0)}%
                        </span>
                        <div style={{ flex: 1, height: 6, background: '#f1f5f9', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${r.match_score}%`, background: r.match_score >= 70 ? 'var(--success-color)' : r.match_score >= 40 ? 'var(--warning-color)' : 'var(--danger-color)' }} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="skill-row" style={{ marginTop: 0 }}>
                        {r.matched_skills.slice(0, 3).map(s => <span key={s} className="chip small ok">{s}</span>)}
                        {r.matched_skills.length > 3 && <span className="muted small">+{r.matched_skills.length - 3}</span>}
                      </div>
                    </td>
                    <td>
                      {r.missing_skills.length === 0 ? (
                        <span className="muted small" style={{ display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircle2 size={14} color="var(--success-color)" /> Perfect fit</span>
                      ) : (
                        <div className="skill-row" style={{ marginTop: 0 }}>
                          {r.missing_skills.slice(0, 2).map(s => <span key={s} className="chip small warn">{s}</span>)}
                          {r.missing_skills.length > 2 && <span className="muted small">+{r.missing_skills.length - 2}</span>}
                        </div>
                      )}
                    </td>
                    <td style={{ paddingRight: 24 }}>
                      <span className="chip" style={{ background: '#f1f5f9', color: 'var(--text-main)' }}>{r.stage}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="card" style={{ padding: 0, flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="row spread" style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-color)', background: '#ffffff' }}>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Users size={20} color="var(--primary-color)" /> Talent Pool
          </h3>
          <div className="row gap" style={{ background: '#f8fafc', padding: '6px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', transition: 'all 0.2s', transform: shakeSelect ? 'translateX(5px)' : 'none', borderColor: shakeSelect ? 'var(--danger-color)' : 'var(--border-color)' }}>
            <Briefcase size={16} className="muted" />
            <select className="header-select" value={applyJobId} onChange={e => { setApplyJobId(e.target.value); setError(''); }} style={{ border: 'none', background: 'transparent', padding: '2px 4px', minWidth: 200, fontWeight: 500, boxShadow: 'none' }}>
              <option value="">— Select target job to apply —</option>
              {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
            </select>
          </div>
        </div>
        
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {candidates.length === 0 ? (
            <div className="empty" style={{ margin: 24, padding: 64, background: '#f8fafc' }}>
              <Search size={48} color="var(--text-muted)" style={{ opacity: 0.2, marginBottom: 16 }} />
              <p style={{ fontSize: 16, color: 'var(--text-main)', marginBottom: 8 }}>Your talent pool is empty.</p>
              <button className="btn primary" onClick={() => setShowUpload(true)}>Upload First Candidate</button>
            </div>
          ) : (
            <table className="table" style={{ margin: 0 }}>
              <thead>
                <tr>
                  <th style={{ paddingLeft: 24 }}>Candidate</th>
                  <th>Experience</th>
                  <th>Top Skills</th>
                  <th style={{ width: 140, paddingRight: 24 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map(c => (
                  <tr key={c.id}>
                    <td style={{ paddingLeft: 24 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'linear-gradient(135deg, var(--primary-light), #ffffff)', border: '1px solid var(--primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary-color)', fontWeight: 600, fontSize: 16 }}>
                          {c.full_name.charAt(0)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: 15 }}>{c.full_name}</div>
                          <div className="muted small">{c.email} • {c.phone || 'No phone'}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{c.experience_years} years</div>
                    </td>
                    <td>
                      <div className="skill-row" style={{ marginTop: 0 }}>
                        {c.skills ? c.skills.split(', ').slice(0, 4).map(s => (
                          <span key={s} className="chip small" style={{ background: '#f1f5f9', color: 'var(--text-main)' }}>{s}</span>
                        )) : <span className="muted">—</span>}
                        {c.skills && c.skills.split(', ').length > 4 &&
                          <span className="muted small" style={{ display: 'inline-flex', alignItems: 'center' }}>+{c.skills.split(', ').length - 4}</span>}
                      </div>
                    </td>
                    <td style={{ paddingRight: 24 }}>
                      <button className="btn small" onClick={() => apply(c.id)} style={{ padding: '8px 16px', background: applyJobId ? 'var(--primary-light)' : 'white', color: applyJobId ? 'var(--primary-color)' : 'var(--text-main)', borderColor: applyJobId ? 'transparent' : 'var(--border-color)', fontWeight: 600, width: '100%', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Apply</span>
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}

function scoreClass(s) {
  if (s >= 70) return 'high'
  if (s >= 40) return 'mid'
  return 'low'
}
