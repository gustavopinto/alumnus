import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getReminders, createReminder, updateReminder, deleteReminder } from '../api';

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

export default function RemindersPage() {
  const navigate = useNavigate();
  const [reminders, setReminders] = useState([]);
  const [text, setText] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [saving, setSaving] = useState(false);

  async function load() {
    const data = await getReminders();
    setReminders(data || []);
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setSaving(true);
    await createReminder({ text, due_date: dueDate || null });
    setText('');
    setDueDate('');
    setSaving(false);
    load();
  }

  async function toggleDone(r) {
    await updateReminder(r.id, { done: !r.done });
    load();
  }

  async function handleDelete(id) {
    if (!confirm('Remover lembrete?')) return;
    await deleteReminder(id);
    load();
  }

  const pending = reminders.filter(r => !r.done);
  const done = reminders.filter(r => r.done);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b shadow-sm px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/')} className="text-gray-500 hover:text-gray-800 text-sm flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Retornar
        </button>
        <div className="w-px h-6 bg-gray-200" />
        <h1 className="text-xl font-bold text-gray-900">Lembretes</h1>
      </header>

      <main className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <section className="bg-white rounded-xl shadow-sm border p-6">
          <form onSubmit={handleSubmit} className="space-y-3">
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Novo lembrete..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500">Data limite</label>
                <input
                  type="date"
                  className="border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={saving || !text.trim()}
                className="ml-auto bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Salvando...' : 'Adicionar'}
              </button>
            </div>
          </form>
        </section>

        <section className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Pendentes</h2>
          {pending.length === 0 && <p className="text-sm text-gray-400 italic">Nenhum lembrete pendente.</p>}
          <ul className="space-y-3">
            {pending.map(r => {
              const days = daysLeft(r.due_date);
              const overdue = days !== null && days < 0;
              const urgent = days !== null && days >= 0 && days <= 3;
              return (
                <li key={r.id} className="flex items-start gap-3 border-b pb-3 last:border-0 last:pb-0">
                  <button
                    onClick={() => toggleDone(r)}
                    className="mt-0.5 w-4 h-4 rounded border-2 border-gray-300 hover:border-blue-500 shrink-0 flex items-center justify-center"
                    title="Marcar como feito"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{r.text}</p>
                    {r.due_date && (
                      <span className={`text-xs mt-0.5 inline-block ${overdue ? 'text-red-500 font-semibold' : urgent ? 'text-orange-500 font-medium' : 'text-gray-400'}`}>
                        {overdue ? `Atrasado · ${formatDue(r.due_date)}` : days === 0 ? 'Hoje!' : `${days}d · ${formatDue(r.due_date)}`}
                      </span>
                    )}
                  </div>
                  <button onClick={() => handleDelete(r.id)} className="text-xs text-red-400 hover:text-red-600 shrink-0">remover</button>
                </li>
              );
            })}
          </ul>
        </section>

        {done.length > 0 && (
          <section className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Concluídos</h2>
            <ul className="space-y-3">
              {done.map(r => (
                <li key={r.id} className="flex items-start gap-3 border-b pb-3 last:border-0 last:pb-0 opacity-50">
                  <button
                    onClick={() => toggleDone(r)}
                    className="mt-0.5 w-4 h-4 rounded border-2 border-blue-400 bg-blue-400 shrink-0 flex items-center justify-center"
                    title="Desmarcar"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                  <p className="text-sm text-gray-500 line-through">{r.text}</p>
                  <button onClick={() => handleDelete(r.id)} className="text-xs text-red-400 hover:text-red-600 shrink-0 ml-auto">remover</button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
