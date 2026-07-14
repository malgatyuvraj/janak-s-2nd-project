// Thin wrapper around the FastAPI endpoints.

const BASE = ''  // Vite proxy forwards /api -> backend

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail
    try {
      detail = (await res.json()).detail || (await res.text())
    } catch {
      detail = res.statusText
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Jobs
  listJobs: () => request('/api/jobs'),
  createJob: (data) => request('/api/jobs', { method: 'POST', body: JSON.stringify(data) }),
  deleteJob: (id) => request(`/api/jobs/${id}`, { method: 'DELETE' }),

  // Candidates
  listCandidates: () => request('/api/candidates'),
  uploadResume: async (formData) => {
    const res = await fetch('/api/candidates/upload', { method: 'POST', body: formData })
    if (!res.ok) {
      const t = await res.text()
      throw new Error(t || res.statusText)
    }
    return res.json()
  },

  // Applications + skill matching
  applyCandidate: (job_id, candidate_id, notes = '') =>
    request('/api/applications', {
      method: 'POST',
      body: JSON.stringify({ job_id, candidate_id, notes }),
    }),
  listApplications: (job_id) =>
    request('/api/applications' + (job_id ? `?job_id=${job_id}` : '')),
  moveStage: (app_id, stage) =>
    request(`/api/applications/${app_id}/stage?stage=${encodeURIComponent(stage)}`, {
      method: 'PATCH',
    }),
  rankedCandidates: (job_id) =>
    request(`/api/jobs/${job_id}/ranked-candidates`),

  // Pipeline
  pipeline: (job_id) =>
    request('/api/pipeline' + (job_id ? `?job_id=${job_id}` : '')),

  // Interviews
  listInterviews: (application_id) =>
    request('/api/interviews' + (application_id ? `?application_id=${application_id}` : '')),
  scheduleInterview: (data) =>
    request('/api/interviews', { method: 'POST', body: JSON.stringify(data) }),
  updateInterview: (id, data) =>
    request(`/api/interviews/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  cancelInterview: (id) => request(`/api/interviews/${id}`, { method: 'DELETE' }),
}

export const STAGE_LABELS = {
  applied: 'Applied',
  screening: 'Screening',
  interview: 'Interview',
  offer: 'Offer',
  hired: 'Hired',
  rejected: 'Rejected',
}

export const STAGES = Object.keys(STAGE_LABELS)
