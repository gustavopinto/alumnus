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
    window.location.href = '/login';
    return;
  }
  if (res.status === 204 || res.status === 205) return null;
  if (options.method === 'DELETE') return null;
  return res.json();
}

// Researchers
export const getResearchers = () => request('/researchers/');
export const createResearcher = (data) => request('/researchers/', { method: 'POST', body: JSON.stringify(data) });
export const updateResearcher = (id, data) => request(`/researchers/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteResearcher = (id) => request(`/researchers/${id}`, { method: 'DELETE' });

// Relationships
export const getRelationships = () => request('/relationships/');
export const createRelationship = (data) => request('/relationships/', { method: 'POST', body: JSON.stringify(data) });
export const updateRelationship = (id, data) => request(`/relationships/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteRelationship = (id) => request(`/relationships/${id}`, { method: 'DELETE' });

// Graph
export const getGraph = () => request('/graph/');
export const updateLayout = (positions) => request('/graph/layout', { method: 'PUT', body: JSON.stringify({ positions }) });

// Notes
export const getNotes = (researcherId) => request(`/researchers/${researcherId}/notes`);
export const deleteNote = (noteId) => request(`/notes/${noteId}`, { method: 'DELETE' });

export async function createNote(researcherId, text, file) {
  const form = new FormData();
  form.append('text', text);
  if (file) form.append('file', file);
  const token = getToken();
  const res = await fetch(`/api/researchers/${researcherId}/notes`, {
    method: 'POST',
    body: form,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.json();
}

// Works
export const getResearcher = (id) => request(`/researchers/${id}`);
export const getResearcherUser = (researcherId) => request(`/researchers/${researcherId}/user`);
export const getResearcherBySlug = (slug) => request(`/researchers/by-slug/${slug}`);
export const getWorks = (researcherId) => request(`/researchers/${researcherId}/works`);
export const createWork = (researcherId, data) => request(`/researchers/${researcherId}/works`, { method: 'POST', body: JSON.stringify(data) });
export const updateWork = (workId, data) => request(`/works/${workId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteWork = (workId) => request(`/works/${workId}`, { method: 'DELETE' });

// Reminders
export const getReminders = () => request('/reminders/');
export const getReminderUnreadCount = () => request('/reminders/notifications/unread-count');
export const createReminder = (data) => request('/reminders/', { method: 'POST', body: JSON.stringify(data) });
export const updateReminder = (id, data) => request(`/reminders/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export async function deleteReminder(id) {
  const token = getToken();
  const res = await fetch(`${BASE}/reminders/${id}`, {
    method: 'DELETE',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    removeToken();
    window.location.href = '/login';
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

export async function markReminderNotificationRead(id) {
  const token = getToken();
  const res = await fetch(`${BASE}/reminders/${id}/mark-notification-read`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    removeToken();
    window.location.href = '/login';
    return;
  }
  if (!res.ok) throw new Error('mark read failed');
}

// Board
export const getBoardPosts = () => request('/board/');
export const createBoardPost = (data) => request('/board/', { method: 'POST', body: JSON.stringify(data) });
export const deleteBoardPost = (id) => request(`/board/${id}`, { method: 'DELETE' });

// Manual
export const getManualEntries = () => request('/manual/');
export const createManualEntry = (data) => request('/manual/', { method: 'POST', body: JSON.stringify(data) });
export const deleteManualEntry = (id) => request(`/manual/${id}`, { method: 'DELETE' });
export const toggleManualVote = (entryId) => request(`/manual/${entryId}/vote`, { method: 'POST' });
export const addManualComment = (entryId, text) => request(`/manual/${entryId}/comments`, { method: 'POST', body: JSON.stringify({ text }) });
export const deleteManualComment = (commentId) => request(`/manual/comments/${commentId}`, { method: 'DELETE' });

// Deadlines
export const getDeadlineInterests = () => request('/deadlines/interests');
export const toggleDeadlineInterest = (key) => request(`/deadlines/${encodeURIComponent(key)}/interest`, { method: 'POST' });
export const extractDeadlineFromUrl = (url) => request('/deadlines/extract-url', { method: 'POST', body: JSON.stringify({ url }) });

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


// --- Admin ---
export const getAdminStats = () => request('/admin/stats');
export const getAdminUsers = () => request('/admin/users');
export const updateUserRole = (id, role, is_admin = false) => request(`/admin/users/${id}`, { method: 'PUT', body: JSON.stringify({ role, is_admin }) });
export const deleteUser = (id) => request(`/admin/users/${id}`, { method: 'DELETE' });
export const deletePendingResearcher = (id) => request(`/admin/researchers/${id}`, { method: 'DELETE' });
