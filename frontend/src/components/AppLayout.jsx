import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Outlet, useOutletContext, useNavigate, Link } from 'react-router-dom';
import Sidebar, { SidebarRail } from './Sidebar';
import Footer from './Footer';
import { getGraph, getResearchers, getReminderUnreadCount } from '../api';
import { removeToken, getTokenPayload, getMe } from '../auth';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

function shortName(fullName) {
  const parts = (fullName || '').trim().split(/\s+/);
  if (parts.length <= 1) return fullName;
  return `${parts[0]} ${parts[parts.length - 1]}`;
}

export function useAppLayout() {
  return useOutletContext() ?? {};
}

export default function AppLayout() {
  const [researchers, setResearchers] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(() => localStorage.getItem('sidebarOpen') !== 'false');
  const [reminderCount, setReminderCount] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const settingsRef = useRef(null);
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    const [graphData, researchersData] = await Promise.all([getGraph(), getResearchers()]);
    setResearchers(researchersData || []);
    setNodes(
      (graphData.nodes || []).map((n) => ({
        ...n,
        data: { ...n.data, name: shortName(n.data.name), researcherId: n.id },
      })),
    );
    setEdges(graphData.edges || []);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    getMe().then((u) => { if (u) setCurrentUser(u); }).catch(() => {});
  }, []);

  const refreshReminderNotifications = useCallback(async () => {
    try {
      const data = await getReminderUnreadCount();
      if (data && typeof data.count === 'number') setReminderCount(data.count);
    } catch {
      setReminderCount(0);
    }
  }, []);

  useEffect(() => {
    refreshReminderNotifications();
    const t = setInterval(refreshReminderNotifications, 45000);
    return () => clearInterval(t);
  }, [refreshReminderNotifications]);

  useEffect(() => {
    function onFocus() { refreshReminderNotifications(); }
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [refreshReminderNotifications]);

  // Fecha dropdown ao clicar fora
  useEffect(() => {
    function handler(e) {
      if (settingsRef.current && !settingsRef.current.contains(e.target)) setSettingsOpen(false);
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const setSidebarOpenPersist = useCallback((next) => {
    setSidebarOpen((prev) => {
      const value = typeof next === 'function' ? next(prev) : next;
      localStorage.setItem('sidebarOpen', String(value));
      return value;
    });
  }, []);

  function handleLogout() {
    removeToken();
    window.location.href = '/login';
  }

  const payload = getTokenPayload();
  const userName =
    (currentUser?.nome && String(currentUser.nome).trim())
    || (payload?.nome && String(payload.nome).trim())
    || currentUser?.email
    || payload?.email
    || 'Usuário';

  const myResearcher = researchers.find(r => r.id === payload?.researcher_id);
  const profileSlug = myResearcher ? slugify(myResearcher.nome) : null;

  const outletContext = useMemo(
    () => ({
      sidebarOpen,
      setSidebarOpen: setSidebarOpenPersist,
      researchers,
      loadData,
      graphNodes: nodes,
      graphEdges: edges,
      refreshReminderNotifications,
    }),
    [sidebarOpen, setSidebarOpenPersist, researchers, loadData, nodes, edges, refreshReminderNotifications],
  );

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <aside
        className={`shrink-0 h-screen border-r bg-gray-100 flex flex-col transition-[width] duration-200 ease-out overflow-hidden ${
          sidebarOpen ? 'w-80' : 'w-[3.25rem]'
        }`}
      >
        {sidebarOpen ? (
          <>
            <div className="p-4 border-b bg-white flex items-center justify-between shrink-0">
              <Link to="/" className="group">
                <h1 className="text-xl font-bold text-blue-700 group-hover:text-blue-800">Alumnus</h1>
                <p className="text-xs text-gray-500">Rede de pesquisa</p>
              </Link>
            </div>
            <div className="flex-1 min-h-0 min-w-0 overflow-y-auto">
              <Sidebar researchers={researchers} onRefresh={loadData} role={payload?.role} />
            </div>
            <Footer />
          </>
        ) : (
          <SidebarRail
            researchers={researchers}
            onExpand={() => setSidebarOpenPersist(true)}
            onLogout={handleLogout}
          />
        )}
      </aside>

      {/* Conteúdo principal */}
      <div className="flex-1 min-h-0 min-w-0 flex flex-col">
        {/* Topbar */}
        <header className="h-12 shrink-0 bg-white border-b flex items-center justify-between px-4 z-30">
          {/* Esquerda: botão recolher */}
          <div className="flex items-center">
            {sidebarOpen && (
              <button
                type="button"
                aria-label="Recolher menu"
                title="Recolher menu"
                onClick={() => setSidebarOpenPersist((o) => !o)}
                className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M18 19l-7-7 7-7" />
                </svg>
              </button>
            )}
          </div>

          {/* Direita: sino + nome + configurações */}
          <div className="flex items-center gap-2">
            {/* Notificações */}
            <button
              type="button"
              aria-label={reminderCount > 0 ? `${reminderCount} lembretes pendentes` : 'Lembretes'}
              title={reminderCount > 0 ? `${reminderCount} lembrete(s) pendente(s)` : 'Lembretes'}
              onClick={() => navigate('/reminders')}
              className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-500"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {reminderCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[1rem] h-4 flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full px-0.5 leading-none" aria-hidden="true">
                  {reminderCount > 9 ? '9+' : reminderCount}
                </span>
              )}
            </button>

            {/* Nome */}
            <span className="text-sm font-semibold text-gray-800 truncate max-w-[16rem]" title={userName}>
              {userName}
            </span>

            {/* Configurações */}
            <div className="relative" ref={settingsRef}>
              <button
                type="button"
                aria-label="Configurações"
                title="Configurações"
                aria-expanded={settingsOpen}
                onClick={() => setSettingsOpen((o) => !o)}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-500"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>

              {settingsOpen && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white border rounded-xl shadow-lg z-50 py-1 overflow-hidden">
                  {profileSlug && (
                    <button
                      type="button"
                      onClick={() => { setSettingsOpen(false); navigate(`/profile/${profileSlug}`); }}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      Meu perfil
                    </button>
                  )}
                  <div className="border-t mx-2 my-1" />
                  <button
                    type="button"
                    onClick={() => { setSettingsOpen(false); handleLogout(); }}
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Sair
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="flex-1 min-h-0 overflow-y-auto">
          <Outlet context={outletContext} />
        </div>
      </div>
    </div>
  );
}
