const TOKEN_KEY = 'alumnus_token';

export const saveToken   = (token) => localStorage.setItem(TOKEN_KEY, token);
export const getToken    = ()      => localStorage.getItem(TOKEN_KEY);
export const removeToken = ()      => localStorage.removeItem(TOKEN_KEY);

export function getTokenPayload() {
  const token = getToken();
  if (!token) return null;
  try {
    const part = token.split('.')[1];
    if (!part) return null;
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

/** Papéis com acesso ao dashboard admin (alinhado ao backend). */
export const DASHBOARD_ROLES = ['professor', 'admin', 'superadmin'];

export function isDashboardRole(role) {
  if (role == null || typeof role !== 'string') return false;
  return DASHBOARD_ROLES.includes(role.trim());
}

/** Verifica se o perfil tem acesso elevado (professor, admin ou superadmin). */
export const isPrivileged = (role) => isDashboardRole(role);

export async function getMe() {
  const token = getToken();
  if (!token) return null;
  const res = await fetch('/api/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) { removeToken(); return null; }
  return res.json();
}
