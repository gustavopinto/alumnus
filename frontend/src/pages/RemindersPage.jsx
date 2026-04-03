import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAppLayout } from '../components/AppLayout';
import { getReminders, createReminder, deleteReminder } from '../api';
import { keys } from '../queryKeys';
import Toast from '../components/Toast';
import { canDeleteReminder, creatorDisplayName } from '../reminderAccess';
import { slugify } from '../mentionUtils.jsx';
import RichEditor from '../components/RichEditor';
import RichContent from '../components/RichContent';

function formatDue(dateStr) {
  if (!dateStr) return null;
  const [y, m, d] = dateStr.split('-');
  return `${d}/${m}/${y}`;
}

function daysLeft(dateStr) {
  if (!dateStr) return null;
  const diff = new Date(dateStr) - new Date();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function todayIso() {
  return new Date().toISOString().split('T')[0];
}

export default function RemindersPage() {
  const { currentUser, researchers = [], currentInstitution } = useAppLayout();
  const creatorOpts = { viewerName: currentUser?.nome };
  const instId = currentInstitution !== undefined ? (currentInstitution?.id ?? null) : undefined;
  const queryClient = useQueryClient();

  const { data: reminders = [] } = useQuery({
    queryKey: keys.reminders(instId),
    queryFn: () => getReminders(instId),
    enabled: instId !== undefined,
  });

  const createMutation = useMutation({
    mutationFn: ({ text, dueDate }) => createReminder({ text, due_date: dueDate || null }, instId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.reminders(instId) }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteReminder(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.reminders(instId) }),
  });

  const [text, setText] = useState('');
  const [dueDate, setDueDate] = useState(todayIso);
  const [toast, setToast] = useState('');

  useEffect(() => {
    function syncMinDate() {
      const t = todayIso();
      setDueDate((d) => (d && d < t ? t : d));
    }
    window.addEventListener('focus', syncMinDate);
    return () => window.removeEventListener('focus', syncMinDate);
  }, []);

  async function handleSubmit(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!text.trim()) return;
    await createMutation.mutateAsync({ text, dueDate });
    setText('');
    setDueDate(todayIso());
    setToast('Lembrete adicionado');
  }

  async function handleDelete(id) {
    if (!confirm('Remover lembrete?')) return;
    try {
      await deleteMutation.mutateAsync(id);
      setToast('Lembrete removido');
    } catch {
      setToast('Não foi possível remover');
    }
  }

  const pending = reminders.filter(r => !r.done);
  const done = reminders.filter(r => r.done);
  const minDue = todayIso();
  const saving = createMutation.isPending;

  return (
    <div className="min-h-full bg-gray-50">
      <Toast message={toast} onClose={() => setToast('')} />
      <main className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <section className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">🔔 Lembretes</h2>
          <form onSubmit={handleSubmit} className="space-y-3">
            <RichEditor
              variant="simple"
              researchers={researchers}
              value={text}
              onChange={setText}
              onSubmit={handleSubmit}
              placeholder="Novo lembrete... (@ para mencionar alguém)"
            />
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500">Data limite</label>
                <input
                  type="date"
                  className="border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={dueDate}
                  min={minDue}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v && v < minDue) setDueDate(minDue);
                    else setDueDate(v);
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={saving || !text.trim()}
                className="ml-auto bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Salvando...' : <>Adicionar <span className="opacity-50 text-xs">{/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl'}+Enter</span></>}
              </button>
            </div>
          </form>
        </section>

        {pending.length > 0 && (
          <section className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Fica ligado!</h2>
            <ul className="space-y-3">
              {pending.map(r => {
                const days = daysLeft(r.due_date);
                const overdue = days !== null && days < 0;
                const urgent = days !== null && days >= 0 && days <= 3;
                return (
                  <li key={r.id} className="flex items-start gap-3 border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm mb-2 text-gray-800"><RichContent html={r.text} researchers={researchers} inline /></p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        {r.due_date && (
                          <span className={`text-xs ${overdue ? 'text-red-500 font-semibold' : urgent ? 'text-orange-500 font-medium' : 'text-gray-400'}`}>
                            {overdue ? `Atrasado · ${formatDue(r.due_date)}` : days === 0 ? 'Hoje!' : `${days}d · ${formatDue(r.due_date)}`}
                          </span>
                        )}
                        <span className="text-xs text-gray-400">
                          Por{' '}
                          {r.created_by_name
                            ? <a href={`/app/profile/${slugify(r.created_by_name)}`} className="font-semibold text-gray-600 hover:text-blue-600 hover:underline">{creatorDisplayName(r, creatorOpts)}</a>
                            : <span className="font-semibold text-gray-600">{creatorDisplayName(r, creatorOpts)}</span>
                          }
                        </span>
                      </div>
                    </div>
                    {canDeleteReminder(r) && (
                      <button
                        type="button"
                        onClick={() => handleDelete(r.id)}
                        title="Remover"
                        aria-label="Remover lembrete"
                        className="p-1 rounded text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0 mt-0.5"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {done.length > 0 && (
          <section className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Passados</h2>
            <ul className="space-y-3">
              {done.map(r => {
                const days = daysLeft(r.due_date);
                const overdue = days !== null && days < 0;
                const urgent = days !== null && days >= 0 && days <= 3;
                return (
                <li
                  key={r.id}
                  className="flex items-start gap-3 border-b pb-3 last:border-0 last:pb-0 opacity-50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm mb-2 line-through text-gray-500"><RichContent html={r.text} researchers={researchers} inline /></p>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      {r.due_date && (
                        <span className={`text-xs ${overdue ? 'text-red-500 font-semibold' : urgent ? 'text-orange-500 font-medium' : 'text-gray-400'}`}>
                          {overdue ? `Atrasado · ${formatDue(r.due_date)}` : days === 0 ? 'Hoje!' : `${days}d · ${formatDue(r.due_date)}`}
                        </span>
                      )}
                      <span className="text-xs text-gray-400">
                        Por{' '}
                        {r.created_by_name
                          ? <a href={`/app/profile/${slugify(r.created_by_name)}`} className="font-semibold text-gray-500 hover:text-blue-600 hover:underline">{creatorDisplayName(r, creatorOpts)}</a>
                          : <span className="font-semibold text-gray-500">{creatorDisplayName(r, creatorOpts)}</span>
                        }
                      </span>
                    </div>
                  </div>
                  {canDeleteReminder(r) && (
                    <button
                      type="button"
                      onClick={() => handleDelete(r.id)}
                      title="Remover"
                      aria-label="Remover lembrete"
                      className="p-1 rounded text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0 ml-auto mt-0.5"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </li>
              );
              })}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
