import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { getToken, getTokenPayload, getMe, removeToken, isPrivileged, isDashboardRole } from '../auth';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

export default function ProtectedRoute({ children, professorOnly = false, adminOnly = false }) {
  const location = useLocation();
  const [state, setState]           = useState('loading');
  const [profileSlug, setProfileSlug] = useState('');

  useEffect(() => {
    async function check() {
      try {
        if (!getToken()) { setState('redirect_login'); return; }

        const payload = getTokenPayload();
        if (!payload || payload.exp * 1000 < Date.now()) {
          removeToken();
          setState('redirect_login');
          return;
        }

        if (adminOnly) {
          // JWT pode estar sem `role` (token antigo); confirma no servidor.
          if (isDashboardRole(payload.role)) {
            setState('ok');
            return;
          }
          const me = await getMe();
          if (!getToken()) {
            setState('redirect_login');
            return;
          }
          if (me && isDashboardRole(me.role)) {
            setState('ok');
            return;
          }
          setState('forbidden');
          return;
        }

        if (payload.is_admin || isPrivileged(payload.role)) { setState('ok'); return; }

        // researcher
        if (professorOnly) { setState('forbidden'); return; }

        const me = await getMe();
        if (!me || !me.researcher_id) { setState('redirect_login'); return; }

        const res = await fetch(`/api/researchers/${me.researcher_id}`, {
          headers: { Authorization: `Bearer ${getToken()}` },
        });
        if (!res.ok) { setState('redirect_login'); return; }
        const researcher = await res.json();
        const slug = slugify(researcher.nome);

        const path = location.pathname;
        const allowedStudent =
          path === '/app' ||
          path === '/app/group' ||
          path === `/app/profile/${slug}` ||
          path === '/app/manual' ||
          path === '/app/reminders' ||
          path === '/app/deadlines' ||
          path.startsWith('/app/profile/');

        if (allowedStudent) {
          setState('ok');
        } else {
          setProfileSlug(slug);
          setState('redirect_profile');
        }
      } catch {
        setState('redirect_login');
      }
    }
    check();
  }, [location.pathname, adminOnly, professorOnly]);

  if (state === 'loading')          return <div className="flex items-center justify-center h-screen text-gray-400 text-sm">Verificando acesso...</div>;
  if (state === 'redirect_login')   return <Navigate to="/entrar" replace state={{ from: location }} />;
  if (state === 'redirect_profile') return <Navigate to={`/app/profile/${profileSlug}`} replace />;
  if (state === 'forbidden')        return <div className="flex items-center justify-center h-screen text-red-500 text-sm">Acesso não permitido.</div>;
  return children;
}
