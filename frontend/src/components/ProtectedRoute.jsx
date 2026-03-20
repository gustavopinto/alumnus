import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { getToken, getTokenPayload, getMe, removeToken } from '../auth';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

export default function ProtectedRoute({ children, professorOnly = false }) {
  const location = useLocation();
  const [state, setState]           = useState('loading');
  const [profileSlug, setProfileSlug] = useState('');

  useEffect(() => {
    async function check() {
      if (!getToken()) { setState('redirect_login'); return; }

      const payload = getTokenPayload();
      if (!payload || payload.exp * 1000 < Date.now()) {
        removeToken();
        setState('redirect_login');
        return;
      }

      if (payload.role === 'professor') { setState('ok'); return; }

      // student
      if (professorOnly) { setState('forbidden'); return; }

      const me = await getMe();
      if (!me || !me.student_id) { setState('redirect_login'); return; }

      const stuRes = await fetch(`/api/students/${me.student_id}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!stuRes.ok) { setState('redirect_login'); return; }
      const stu  = await stuRes.json();
      const slug = slugify(stu.nome);

      if (location.pathname === `/profile/${slug}`) {
        setState('ok');
      } else {
        setProfileSlug(slug);
        setState('redirect_profile');
      }
    }
    check();
  }, [location.pathname]);

  if (state === 'loading')          return <div className="flex items-center justify-center h-screen text-gray-400 text-sm">Verificando acesso...</div>;
  if (state === 'redirect_login')   return <Navigate to="/login" replace state={{ from: location }} />;
  if (state === 'redirect_profile') return <Navigate to={`/profile/${profileSlug}`} replace />;
  if (state === 'forbidden')        return <div className="flex items-center justify-center h-screen text-red-500 text-sm">Acesso não permitido.</div>;
  return children;
}
