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
import { useConfirm } from '../components/ConfirmModal';

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

function ReminderCard({ r, researchers, creatorOpts, onDelete }) {
  const days = daysLeft(r.due_date);
  const overdue = days !== null && days < 0;
  const urgent  = days !== null && days >= 0 && days <= 3;

  const borderColor = overdue ? 'border-l-red-400' : urgent ? 'border-l-orange-400' : 'border-l-blue-300';

  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm border-l-4 ${borderColor} overflow-hidden`}>
      <div className="px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-800 leading-relaxed">
              <RichContent html={r.text} researchers={researchers} inline />
            </p>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
              {r.due_date && (
                <span className={`text-xs font-medium ${overdue ? 'text-red-500' : urgent ? 'text-orange-500' : 'text-gray-400'}`}>
                  {overdue
                    ? `⚠ Atrasado · ${formatDue(r.due_date)}`
                    : days === 0
                    ? '📅 Hoje!'
                    : `📅 ${days}d · ${formatDue(r.due_date)}`}
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
              onClick={() => onDelete(r.id)}
              title="Remover lembrete"
              aria-label="Remover lembrete"
              className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors shrink-0"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
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
  const { confirm, modal: confirmModal } = useConfirm();

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
    if (!await confirm({ title: 'Remover lembrete?', confirmLabel: 'Remover' })) return;
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
      {confirmModal}
      <Toast message={toast} onClose={() => setToast('')} />
      <main className="max-w-2xl mx-auto py-8 px-4 space-y-6">

        {/* Form */}
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

        {/* Pending */}
        {pending.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide px-1">Fica ligado!</h3>
            {pending.map(r => (
              <ReminderCard
                key={r.id}
                r={r}
                researchers={researchers}
                creatorOpts={creatorOpts}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Done */}
        {done.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide px-1">Passados</h3>
            {done.map(r => (
              <div key={r.id} className="opacity-50">
                <ReminderCard
                  r={r}
                  researchers={researchers}
                  creatorOpts={creatorOpts}
                  onDelete={handleDelete}
                />
              </div>
            ))}
          </div>
        )}

      </main>
    </div>
  );
}
