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
  if (options.method === 'DELETE') return null;
  return res.json();
}

// Students
export const getStudents = () => request('/students/');
export const createStudent = (data) => request('/students/', { method: 'POST', body: JSON.stringify(data) });
export const updateStudent = (id, data) => request(`/students/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteStudent = (id) => request(`/students/${id}`, { method: 'DELETE' });

// Relationships
export const getRelationships = () => request('/relationships/');
export const createRelationship = (data) => request('/relationships/', { method: 'POST', body: JSON.stringify(data) });
export const updateRelationship = (id, data) => request(`/relationships/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteRelationship = (id) => request(`/relationships/${id}`, { method: 'DELETE' });

// Graph
export const getGraph = () => request('/graph/');
export const updateLayout = (positions) => request('/graph/layout', { method: 'PUT', body: JSON.stringify({ positions }) });

// Notes
export const getNotes = (studentId) => request(`/students/${studentId}/notes`);
export const deleteNote = (noteId) => request(`/notes/${noteId}`, { method: 'DELETE' });

export async function createNote(studentId, text, file) {
  const form = new FormData();
  form.append('text', text);
  if (file) form.append('file', file);
  const token = getToken();
  const res = await fetch(`/api/students/${studentId}/notes`, {
    method: 'POST',
    body: form,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.json();
}

// Works
export const getStudent = (id) => request(`/students/${id}`);
export const getStudentBySlug = (slug) => request(`/students/by-slug/${slug}`);
export const getWorks = (studentId) => request(`/students/${studentId}/works`);
export const createWork = (studentId, data) => request(`/students/${studentId}/works`, { method: 'POST', body: JSON.stringify(data) });
export const updateWork = (workId, data) => request(`/works/${workId}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteWork = (workId) => request(`/works/${workId}`, { method: 'DELETE' });

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
