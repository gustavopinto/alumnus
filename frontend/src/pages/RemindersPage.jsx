import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAppLayout } from '../components/AppLayout';
import { getReminders, createReminder, deleteReminder } from '../api';
import Toast from '../components/Toast';
import { canDeleteReminder, creatorDisplayName } from '../reminderAccess';
import { slugify, invalidMentions, renderWithMentions, useMentions, MentionDropdown } from '../mentionUtils.jsx';

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
  const { refreshSidebarReminders, remindersRefreshKey = 0, currentUser, researchers = [], currentInstitution } = useAppLayout();
  const creatorOpts = { viewerName: currentUser?.nome };
  const [reminders, setReminders] = useState([]);
  const [text, setText] = useState('');
  const [dueDate, setDueDate] = useState(todayIso);
  const [saving, setSaving] = useState(false);
  const [mentionError, setMentionError] = useState('');
  const [toast, setToast] = useState('');
  const textareaRef = useRef();
  const { mentionSuggestions, mentionIndex, setMentionIndex, handleTextChange, insertMention, handleMentionKeyDown } =
    useMentions({ text, setText, inputRef: textareaRef, researchers });

  const load = useCallback(async () => {
    const data = await getReminders(currentInstitution?.id);
    setReminders(data || []);
  }, [currentInstitution]);

  useEffect(() => { load(); }, [load, remindersRefreshKey]);


  useEffect(() => {
    function syncMinDate() {
      const t = todayIso();
      setDueDate((d) => (d && d < t ? t : d));
    }
    window.addEventListener('focus', syncMinDate);
    return () => window.removeEventListener('focus', syncMinDate);
  }, []);

  function wrapFormat(prefix, suffix) {
    const el = textareaRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = text.slice(start, end);
    if (!selected) return;
    const newText = text.slice(0, start) + prefix + selected + suffix + text.slice(end);
    setText(newText);
    setTimeout(() => {
      el.setSelectionRange(start + prefix.length, end + prefix.length);
      el.focus();
    }, 0);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    const bad = invalidMentions(text.trim(), researchers);
    if (bad.length > 0) {
      setMentionError(`Menção não encontrada: ${bad.join(', ')}`);
      return;
    }
    setMentionError('');
    setSaving(true);
    await createReminder({ text, due_date: dueDate || null }, currentInstitution?.id);
    setText('');
    setDueDate(todayIso());
    setSaving(false);
    setToast('Lembrete adicionado');
    refreshSidebarReminders?.();
  }

  async function handleDelete(id) {
    if (!confirm('Remover lembrete?')) return;
    try {
      await deleteReminder(id);
      refreshSidebarReminders?.();
      setToast('Lembrete removido');
    } catch (e) {
      setToast('Não foi possível remover');
    }
  }

  const pending = reminders.filter(r => !r.done);
  const done = reminders.filter(r => r.done);
  const minDue = todayIso();

  return (
    <div className="min-h-full bg-gray-50">
      <Toast message={toast} onClose={() => setToast('')} />
      <main className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <section className="bg-white rounded-xl shadow-sm border p-6">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className={`relative border rounded-lg transition-colors focus-within:ring-2 ${mentionError ? 'border-red-400 focus-within:ring-red-300' : mentionSuggestions.length > 0 ? 'border-blue-400 ring-2 ring-blue-200 focus-within:ring-blue-400' : 'focus-within:ring-blue-400'}`}>
              <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border-b">
                <button type="button" onClick={() => wrapFormat('**', '**')}
                  className="w-6 h-6 flex items-center justify-center rounded text-sm font-bold text-gray-700 hover:bg-gray-200 transition-colors" title="Negrito">B</button>
                <button type="button" onClick={() => wrapFormat('*', '*')}
                  className="w-6 h-6 flex items-center justify-center rounded text-sm italic text-gray-700 hover:bg-gray-200 transition-colors" title="Itálico">I</button>
                <button type="button" onClick={() => wrapFormat('_', '_')}
                  className="w-6 h-6 flex items-center justify-center rounded text-sm underline text-gray-700 hover:bg-gray-200 transition-colors" title="Sublinhado">S</button>
                <span className="text-xs text-gray-400 ml-1">Selecione o texto e clique no estilo</span>
              </div>
              <textarea
                ref={textareaRef}
                className="w-full px-3 py-2 text-sm h-20 resize-none focus:outline-none"
                placeholder="Novo lembrete... (@ para mencionar alguém)"
                value={text}
                onChange={e => { handleTextChange(e); setMentionError(''); }}
                onKeyDown={e => {
                  if (handleMentionKeyDown(e)) return;
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); handleSubmit(e); }
                }}
              />
              <MentionDropdown suggestions={mentionSuggestions} activeIndex={mentionIndex} onSelect={insertMention} onHover={setMentionIndex} />
            </div>
            {mentionError && <p className="text-xs text-red-500">{mentionError}</p>}
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
                      <p className="text-sm whitespace-pre-wrap mb-2 text-gray-800">{renderWithMentions(r.text, researchers)}</p>
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
                    <p className="text-sm whitespace-pre-wrap mb-2 line-through text-gray-500">{renderWithMentions(r.text, researchers)}</p>
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
