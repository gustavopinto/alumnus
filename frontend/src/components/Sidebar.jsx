import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import ResearcherForm from './StudentForm';
import { deleteResearcher, getReminders, createReminder, updateReminder, deleteReminder } from '../api';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

const DEADLINES = [
  { label: 'ICSE 2026', url: 'https://conf.researchr.org/home/icse-2026', date: '2026-01-24' },
  { label: 'FSE 2026', url: 'https://conf.researchr.org/home/fse-2026', date: '2026-02-06' },
  { label: 'ASE 2026', url: 'https://conf.researchr.org/home/ase-2026', date: '2026-04-10' },
  { label: 'MSR 2026', url: 'https://conf.researchr.org/home/msr-2026', date: '2026-02-13' },
  { label: 'ISSTA 2026', url: 'https://conf.researchr.org/home/issta-2026', date: '2026-02-07' },
  { label: 'SBES 2026', url: 'https://cbsoft.sbc.org.br/2026/', date: '2026-05-04' },
  { label: 'SBSI 2026', url: 'https://sbsi.sbc.org.br/2026/', date: '2025-09-29' },
  { label: 'SBIE 2025', url: 'https://cbie.sbc.org.br/2025/sbie2/', date: '2025-06-09' },
  { label: 'WASHES 2026', url: 'https://csbc.sbc.org.br/2026/washes/', date: '2026-03-30' },
  { label: 'WER 2026 – Regular', url: 'https://organizacaower.github.io/WER2026/es/track-regular.html', date: '2026-03-31' },
  { label: 'WER 2026 – Industry', url: 'https://organizacaower.github.io/WER2026/es/track-industry.html', date: '2026-04-13' },
];

function daysUntil(dateStr) {
  const diff = new Date(dateStr) - new Date();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function today() {
  return new Date().toISOString().split('T')[0];
}

function RemindersDropdown({ rail = false }) {
  const [open, setOpen] = useState(false);
  const [showOld, setShowOld] = useState(false);
  const [reminders, setReminders] = useState([]);
  const [text, setText] = useState('');
  const [date, setDate] = useState(today());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const ref = useRef();
  const dateRef = useRef();

  async function load() {
    const data = await getReminders();
    setReminders(data || []);
  }

  useEffect(() => { load(); }, []);

  useEffect(() => {
    function handler(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!text.trim() || !date) return;
    setSaving(true);
    setError('');
    try {
      const result = await createReminder({ text: text.trim(), due_date: date });
      if (result && result.id) {
        setText('');
        setDate('');
        load();
      } else {
        setError('Erro ao adicionar lembrete');
      }
    } catch {
      setError('Erro ao adicionar lembrete');
    } finally {
      setSaving(false);
    }
  }

  async function toggleDone(r) {
    await updateReminder(r.id, { done: !r.done });
    load();
  }

  async function handleDelete(id) {
    await deleteReminder(id);
    load();
  }

  const todayStr = today();
  const upcoming = reminders
    .filter(r => !r.done && r.due_date >= todayStr)
    .sort((a, b) => a.due_date.localeCompare(b.due_date));
  const old = reminders
    .filter(r => !r.done && r.due_date < todayStr)
    .sort((a, b) => b.due_date.localeCompare(a.due_date));

  const bellIcon = (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  );

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        title={rail ? 'Lembretes' : undefined}
        onClick={() => setOpen(o => !o)}
        className={
          rail
            ? 'relative w-11 h-11 flex items-center justify-center bg-white border rounded-lg text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors'
            : 'w-full flex items-center gap-2 bg-white border rounded-lg px-3 py-2 text-sm text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors'
        }
      >
        {bellIcon}
        {!rail && (
          <>
            <span className="flex-1 text-left">Lembretes</span>
            {upcoming.length > 0 && (
              <span className="bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5 leading-none">{upcoming.length}</span>
            )}
            <svg xmlns="http://www.w3.org/2000/svg" className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </>
        )}
        {rail && upcoming.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[1.125rem] h-[1.125rem] flex items-center justify-center bg-blue-600 text-white text-[10px] font-bold rounded-full px-0.5 leading-none">
            {upcoming.length > 9 ? '9+' : upcoming.length}
          </span>
        )}
      </button>

      {open && (
        <div
          className={
            rail
              ? 'absolute left-full top-0 ml-1 w-80 max-h-[min(28rem,calc(100vh-6rem))] overflow-y-auto bg-white border rounded-xl shadow-lg z-[60] overflow-x-hidden'
              : 'absolute left-0 right-0 top-full mt-1 bg-white border rounded-xl shadow-lg z-50 overflow-hidden'
          }
        >
          {/* Caixa de criação */}
          <div className="p-3 border-b bg-gray-50">
            <form onSubmit={handleAdd} className="space-y-2">
              <input
                className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
                placeholder="Novo lembrete..."
                value={text}
                maxLength={50}
                onChange={e => setText(e.target.value)}
              />
              <div className="flex items-center gap-2">
                <label className="flex-1 flex items-center gap-1.5 border rounded px-2 py-1.5 text-sm text-gray-600 cursor-pointer hover:border-blue-400 hover:text-blue-600 transition-colors bg-white">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>{date ? new Date(date + 'T00:00:00').toLocaleDateString('pt-BR') : 'Selecionar data'}</span>
                  <input
                    ref={dateRef}
                    type="date"
                    className="sr-only"
                    value={date}
                    min={todayStr}
                    onChange={e => setDate(e.target.value)}
                  />
                </label>
                <button
                  type="submit"
                  disabled={saving || !text.trim() || !date}
                  className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs hover:bg-blue-700 disabled:opacity-40"
                >
                  +
                </button>
              </div>
              {error && <p className="text-xs text-red-500">{error}</p>}
            </form>
          </div>

          {/* Caixa de listagem */}
          <div className="p-3 space-y-2">
            {upcoming.length === 0 && old.length === 0 && (
              <p className="text-xs text-gray-400 italic text-center py-1">Nenhum lembrete.</p>
            )}
            <ul className="space-y-1.5 max-h-48 overflow-y-auto">
              {upcoming.map(r => {
                const days = daysUntil(r.due_date);
                const urgent = days <= 3;
                return (
                  <li key={r.id} className="rounded px-1 py-1 group">
                    <div className="flex items-start gap-1.5">
                      <span className="flex-1 text-sm font-medium text-gray-700 leading-snug break-words min-w-0">{r.text}</span>
                      <button onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 shrink-0 mt-0.5" title="Remover">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                    <span className={`text-xs ${urgent ? 'text-orange-500 font-semibold' : 'text-gray-400'}`}>
                      {days === 0 ? 'Hoje!' : `${days}d`} · {new Date(r.due_date + 'T00:00:00').toLocaleDateString('pt-BR')}
                    </span>
                  </li>
                );
              })}
            </ul>

            {old.length > 0 && (
              <div className="border-t pt-2">
                <button
                  onClick={() => setShowOld(o => !o)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {old.length} atrasado{old.length > 1 ? 's' : ''}
                </button>
                {showOld && (
                  <ul className="mt-1.5 space-y-1.5 max-h-32 overflow-y-auto">
                    {old.map(r => (
                      <li key={r.id} className="rounded px-1 py-1 group opacity-60">
                        <div className="flex items-start gap-1.5">
                          <span className="flex-1 text-sm font-medium text-gray-600 leading-snug break-words min-w-0">{r.text}</span>
                          <button onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 shrink-0 mt-0.5">
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </button>
                        </div>
                        <span className="text-xs text-red-400">
                          Atrasado · {new Date(r.due_date + 'T00:00:00').toLocaleDateString('pt-BR')}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Dropdown({ label, icon, badge, children, rail = false }) {
  const [open, setOpen] = useState(false);
  const ref = useRef();

  useEffect(() => {
    function handler(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        title={rail ? label : undefined}
        onClick={() => setOpen(o => !o)}
        className={
          rail
            ? 'relative w-11 h-11 flex items-center justify-center bg-white border rounded-lg text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors'
            : 'w-full flex items-center gap-2 bg-white border rounded-lg px-3 py-2 text-sm text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors'
        }
      >
        {icon}
        {!rail && (
          <>
            <span className="flex-1 text-left">{label}</span>
            {badge != null && badge > 0 && (
              <span className="bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5 leading-none">{badge}</span>
            )}
            <svg xmlns="http://www.w3.org/2000/svg" className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </>
        )}
        {rail && badge != null && badge > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[1.125rem] h-[1.125rem] flex items-center justify-center bg-blue-600 text-white text-[10px] font-bold rounded-full px-0.5 leading-none">
            {badge > 9 ? '9+' : badge}
          </span>
        )}
      </button>
      {open && (
        <div
          className={
            rail
              ? 'absolute left-full top-0 ml-1 w-72 max-h-[min(24rem,calc(100vh-6rem))] overflow-y-auto bg-white border rounded-xl shadow-lg z-[60] p-3'
              : 'absolute left-0 right-0 top-full mt-1 bg-white border rounded-xl shadow-lg z-50 p-3'
          }
        >
          {children}
        </div>
      )}
    </div>
  );
}

const GROUP_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const CALENDAR_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const BOOK_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

/** Barra estreita com ícones quando o menu principal está recolhido */
export function SidebarRail({ researchers, onExpand, onLogout }) {
  const upcomingDeadlines = [...DEADLINES].filter(d => daysUntil(d.date) >= 0).sort((a, b) => new Date(a.date) - new Date(b.date));
  const pastDeadlines = [...DEADLINES].filter(d => daysUntil(d.date) < 0).sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <div className="flex flex-col flex-1 min-h-0 h-full bg-gray-100">
      <div className="flex flex-col items-center gap-2.5 py-3 px-1.5 flex-1 min-h-0 overflow-y-auto overscroll-contain">
        <button
          type="button"
          onClick={onExpand}
          className="w-11 h-11 flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors shrink-0"
          title="Expandir menu"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M6 5l7 7-7 7" />
          </svg>
        </button>

        <Link
          to="/"
          title="Grupo — ir para o grafo"
          className="relative w-11 h-11 flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors shrink-0"
        >
          {GROUP_ICON}
          {researchers.length > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[1.125rem] h-[1.125rem] flex items-center justify-center bg-blue-600 text-white text-[10px] font-bold rounded-full px-0.5 leading-none">
              {researchers.length > 9 ? '9+' : researchers.length}
            </span>
          )}
        </Link>

        <RemindersDropdown rail />

        <Dropdown rail label="Deadlines" icon={CALENDAR_ICON} badge={upcomingDeadlines.length}>
          <ul className="space-y-1.5">
            {upcomingDeadlines.map((d) => {
              const days = daysUntil(d.date);
              return (
                <li key={d.label} className="rounded px-1 py-1">
                  <a href={d.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600 hover:underline block truncate">{d.label}</a>
                  <span className={`text-xs ${days <= 14 ? 'text-red-500 font-semibold' : 'text-gray-400'}`}>
                    {days === 0 ? 'Hoje!' : `${days}d`} · {new Date(d.date).toLocaleDateString('pt-BR')}
                  </span>
                </li>
              );
            })}
            {pastDeadlines.length > 0 && <li className="border-t my-1" />}
            {pastDeadlines.map((d) => (
              <li key={d.label} className="rounded px-1 py-1 opacity-40">
                <a href={d.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600 hover:underline block truncate">{d.label}</a>
                <span className="text-xs text-gray-400">Encerrado · {new Date(d.date).toLocaleDateString('pt-BR')}</span>
              </li>
            ))}
          </ul>
        </Dropdown>

        <Link
          to="/manual"
          title="Manual de Sobrevivência"
          className="w-11 h-11 flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors shrink-0"
        >
          {BOOK_ICON}
        </Link>
      </div>

      <div className="shrink-0 py-2.5 flex justify-center border-t border-gray-200/80 bg-white">
        <button
          type="button"
          onClick={onLogout}
          className="w-11 h-11 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
          title="Sair"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({ researchers, onRefresh, role }) {
  const [view, setView] = useState('list');
  const [editResearcher, setEditResearcher] = useState(null);

  function handleEdit(s) { setEditResearcher(s); setView('researcher-form'); }

  async function handleDeactivate(id) {
    if (!confirm('Inativar este pesquisador?')) return;
    await deleteResearcher(id);
    onRefresh();
  }

  function handleSaved() { setView('list'); setEditResearcher(null); onRefresh(); }

  if (view === 'researcher-form') {
    return (
      <div className="p-4">
        <ResearcherForm researcher={editResearcher} researchers={researchers} onSaved={handleSaved}
          onCancel={() => { setView('list'); setEditResearcher(null); }} />
      </div>
    );
  }

  const upcomingDeadlines = [...DEADLINES].filter(d => daysUntil(d.date) >= 0).sort((a, b) => new Date(a.date) - new Date(b.date));
  const pastDeadlines = [...DEADLINES].filter(d => daysUntil(d.date) < 0).sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <div className="p-4 space-y-2 overflow-y-auto h-full">

      {/* Grupo */}
      <Dropdown
        label="Grupo"
        icon={GROUP_ICON}
        badge={researchers.length}
      >
        <ul className="space-y-1">
          {researchers.map((s) => (
            <li key={s.id} className="flex items-center justify-between rounded px-1 py-1 text-sm hover:bg-gray-50">
              <Link to={`/profile/${slugify(s.nome)}`} className="flex-1 truncate hover:text-blue-600">{s.nome}</Link>
              {role === 'professor' && (
                <span className="flex gap-1 shrink-0 ml-1">
                  <button onClick={() => handleEdit(s)} title="Editar" className="text-blue-500 hover:text-blue-700 p-0.5">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button onClick={() => handleDeactivate(s.id)} title="Inativar" className="text-red-400 hover:text-red-600 p-0.5">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                  </button>
                </span>
              )}
            </li>
          ))}
        </ul>
      </Dropdown>

      {/* Lembretes */}
      <RemindersDropdown />

      {/* Deadlines */}
      <Dropdown
        label="Deadlines"
        icon={CALENDAR_ICON}
        badge={upcomingDeadlines.length}
      >
        <ul className="space-y-1.5">
          {upcomingDeadlines.map((d) => {
            const days = daysUntil(d.date);
            return (
              <li key={d.label} className="rounded px-1 py-1">
                <a href={d.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600 hover:underline block truncate">{d.label}</a>
                <span className={`text-xs ${days <= 14 ? 'text-red-500 font-semibold' : 'text-gray-400'}`}>
                  {days === 0 ? 'Hoje!' : `${days}d`} · {new Date(d.date).toLocaleDateString('pt-BR')}
                </span>
              </li>
            );
          })}
          {pastDeadlines.length > 0 && <li className="border-t my-1" />}
          {pastDeadlines.map((d) => (
            <li key={d.label} className="rounded px-1 py-1 opacity-40">
              <a href={d.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600 hover:underline block truncate">{d.label}</a>
              <span className="text-xs text-gray-400">Encerrado · {new Date(d.date).toLocaleDateString('pt-BR')}</span>
            </li>
          ))}
        </ul>
      </Dropdown>

      {/* Manual de Sobrevivência */}
      <Link
        to="/manual"
        className="w-full flex items-center gap-2 bg-white border rounded-lg px-3 py-2 text-sm text-gray-700 shadow-sm hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors"
      >
        {BOOK_ICON}
        <span>Manual de Sobrevivência</span>
      </Link>

      {/* Mural — hidden for now */}
      {/* <Link to="/board" ...>Mural</Link> */}
    </div>
  );
}
