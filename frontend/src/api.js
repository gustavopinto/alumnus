import { getToken, removeToken } from './auth';

const BASE = '/api';

async function request(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  });
  if (res.status === 401) {
    removeToken();
    window.location.href = '/entrar';
    return;
  }
  if (res.status === 204 || res.status === 205) return null;
  if (options.method === 'DELETE') return null;
  return res.json();
}

// Professors
export const getProfessors = () => request('/professors/');

// User profile
export const updateMyProfile   = (data) => request('/users/me', { method: 'PATCH', body: JSON.stringify(data) });
export const updateUserProfile = (userId, data) => request(`/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) });
export const getProfileBySlug = (slug) => request(`/profiles/by-slug/${slug}`);

// Researchers
export const getResearchers = (institutionId, ativo) => {
  const params = new URLSearchParams();
  if (institutionId) params.set('institution_id', institutionId);
  if (ativo !== undefined) params.set('ativo', ativo);
  const qs = params.toString();
  return request(`/researchers/${qs ? `?${qs}` : ''}`);
};
export const createResearcher = (data) => request('/researchers/', { method: 'POST', body: JSON.stringify(data) });
export const updateResearcher = (id, data) => request(`/researchers/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteResearcher = (id) => request(`/researchers/${id}`, { method: 'DELETE' });

// Relationships
export const getRelationships = () => request('/relationships/');
export const createRelationship = (data) => request('/relationships/', { method: 'POST', body: JSON.stringify(data) });
export const updateRelationship = (id, data) => request(`/relationships/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteRelationship = (id) => request(`/relationships/${id}`, { method: 'DELETE' });

// Graph
export const getGraph = (institutionId) =>
  request(`/graph/${institutionId ? `?institution_id=${institutionId}` : ''}`);
export const updateLayout = (positions) => request('/graph/layout', { method: 'PUT', body: JSON.stringify({ positions }) });

// Notes
export const getNotes = (userId, institutionId) =>
  request(`/users/${userId}/notes${institutionId ? `?institution_id=${institutionId}` : ''}`);
export const deleteNote = (noteId) => request(`/notes/${noteId}`, { method: 'DELETE' });

export async function createNote(userId, text, file, institutionId) {
  const form = new FormData();
  form.append('text', text);
  if (file) form.append('file', file);
  if (institutionId != null) form.append('institution_id', institutionId);
  const token = getToken();
  const res = await fetch(`/api/users/${userId}/notes`, {
    method: 'POST',
    body: form,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.json();
}

// Researcher
export const getResearcher = (id) => request(`/researchers/${id}`);
export const getResearcherUser = (researcherId) => request(`/researchers/${researcherId}/user`);

// Reminders
export const getReminders = (institutionId) =>
  request(`/reminders/${institutionId ? `?institution_id=${institutionId}` : ''}`);
export const createReminder = (data, institutionId) =>
  request('/reminders/', { method: 'POST', body: JSON.stringify({ ...data, institution_id: institutionId || null }) });
export const updateReminder = (id, data) => request(`/reminders/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export async function deleteReminder(id) {
  const token = getToken();
  const res = await fetch(`${BASE}/reminders/${id}`, {
    method: 'DELETE',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    removeToken();
    window.location.href = '/entrar';
    return;
  }
  if (!res.ok) {
    let msg = 'Não foi possível remover';
    try {
      const body = await res.json();
      if (body?.detail) msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
}

// Tips
export const getTips = (institutionId) =>
  request(`/tips/${institutionId ? `?institution_id=${institutionId}` : ''}`);
export const createTip = (data, institutionId) =>
  request('/tips/', { method: 'POST', body: JSON.stringify({ ...data, institution_id: institutionId || null }) });
export const deleteTip = (id) => request(`/tips/${id}`, { method: 'DELETE' });
export const toggleTipVote = (entryId) => request(`/tips/${entryId}/vote`, { method: 'POST' });
export const addTipComment = (entryId, text) => request(`/tips/${entryId}/comments`, { method: 'POST', body: JSON.stringify({ text }) });
export const deleteTipComment = (commentId) => request(`/tips/comments/${commentId}`, { method: 'DELETE' });

// Deadlines
export const getDeadlines = (institutionId) =>
  request(`/deadlines/${institutionId ? `?institution_id=${institutionId}` : ''}`);
export const createDeadline = (data) =>
  request('/deadlines/', { method: 'POST', body: JSON.stringify(data) });
export const deleteDeadline = (id) =>
  request(`/deadlines/${id}`, { method: 'DELETE' });
export const getDeadlineInterests = (institutionId) =>
  request(`/deadlines/interests${institutionId ? `?institution_id=${institutionId}` : ''}`);
export const toggleDeadlineInterest = (deadlineId) =>
  request(`/deadlines/${deadlineId}/interest`, { method: 'POST' });
export const extractDeadlineFromUrl = (url) =>
  request('/deadlines/extract-url', { method: 'POST', body: JSON.stringify({ url }) });

// Upload
export async function uploadPhoto(file) {
  const form = new FormData();
  form.append('file', file);
  const token = getToken();
  const res = await fetch(`${BASE}/upload/photo`, {
    method: 'POST',
    body: form,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.json();
}


// Institutions
export const getInstitutions = () => request('/institutions/');
export const createInstitution = (email) => request('/institutions/', { method: 'POST', body: JSON.stringify({ email }) });
export const getMyEmails = () => request('/institutions/my-emails');
export const addMyEmail = (email) => request('/institutions/my-emails', { method: 'POST', body: JSON.stringify({ email }) });
export const removeMyEmail = (piId) => request(`/institutions/my-emails/${piId}`, { method: 'DELETE' });

// Groups
export const getGroups = () => request('/groups/');
export const createGroup = (name, institution_id) => request('/groups/', { method: 'POST', body: JSON.stringify({ name, institution_id }) });
export const updateGroup = (id, data) => request(`/groups/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// --- Admin ---
export const getAdminStats = () => request('/admin/stats');
export const getAdminUsers = () => request('/admin/users');
export const updateUserRole = (id, role) => request(`/admin/users/${id}`, { method: 'PUT', body: JSON.stringify({ role }) });
export const deleteUser = (id) => request(`/admin/users/${id}`, { method: 'DELETE' });
export const deletePendingResearcher = (id) => request(`/admin/researchers/${id}`, { method: 'DELETE' });
export const bulkDeleteUsers = (user_ids, researcher_ids) => request('/admin/bulk-delete', { method: 'POST', body: JSON.stringify({ user_ids, researcher_ids }) });

// Milestones
export const getMilestones      = (researcherId) => request(`/researchers/${researcherId}/milestones/`);
export const createMilestone    = (researcherId, data) => request(`/researchers/${researcherId}/milestones/`, { method: 'POST', body: JSON.stringify(data) });
export const updateMilestone    = (researcherId, milestoneId, data) => request(`/researchers/${researcherId}/milestones/${milestoneId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteMilestone    = (researcherId, milestoneId) => request(`/researchers/${researcherId}/milestones/${milestoneId}`, { method: 'DELETE' });
