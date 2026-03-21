import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getManualEntries, createManualEntry, deleteManualEntry,
  toggleManualVote, addManualComment, deleteManualComment,
} from '../api';
import { getTokenPayload } from '../auth';

function renderFormatted(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('_') && part.endsWith('_')) {
      return <u key={i}>{part.slice(1, -1)}</u>;
    }
    return part;
  });
}

function RichTextarea({ value, onChange, placeholder, rows = 4 }) {
  const ref = useRef();

  function wrap(prefix, suffix) {
    const el = ref.current;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = value.slice(start, end);
    if (!selected) return;
    onChange(value.slice(0, start) + prefix + selected + suffix + value.slice(end));
    setTimeout(() => {
      el.setSelectionRange(start + prefix.length, end + prefix.length);
      el.focus();
    }, 0);
  }

  return (
    <div className="border rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-400">
      <div className="flex items-center gap-2 px-2 py-1 bg-gray-50 border-b">
        <button type="button" onClick={() => wrap('**', '**')}
          className="w-6 h-6 flex items-center justify-center rounded text-sm font-bold text-gray-700 hover:bg-gray-200 transition-colors"
          title="Negrito">B</button>
        <button type="button" onClick={() => wrap('*', '*')}
          className="w-6 h-6 flex items-center justify-center rounded text-sm italic text-gray-700 hover:bg-gray-200 transition-colors"
          title="Itálico">I</button>
        <button type="button" onClick={() => wrap('_', '_')}
          className="w-6 h-6 flex items-center justify-center rounded text-sm underline text-gray-700 hover:bg-gray-200 transition-colors"
          title="Sublinhado">S</button>
        <span className="text-xs text-gray-400">Selecione o texto e clique no estilo</span>
      </div>
      <textarea
        ref={ref}
        className="w-full px-3 py-2 text-sm resize-none focus:outline-none"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        rows={rows}
      />
    </div>
  );
}

function EntryCard({ entry, isProfessor, currentUserId, onVote, onDelete, onCommentAdded, onCommentDeleted }) {
  const [open, setOpen] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [voted, setVoted] = useState(entry.user_voted);
  const [voteCount, setVoteCount] = useState(entry.vote_count);

  async function handleVote(e) {
    e.stopPropagation();
    const result = await toggleManualVote(entry.id);
    if (result) {
      setVoted(result.voted);
      setVoteCount(result.vote_count);
      onVote();
    }
  }

  async function handleComment(e) {
    e.preventDefault();
    if (!commentText.trim()) return;
    setSubmitting(true);
    await addManualComment(entry.id, commentText.trim());
    setCommentText('');
    setSubmitting(false);
    onCommentAdded();
  }

  async function handleDeleteComment(commentId) {
    await deleteManualComment(commentId);
    onCommentDeleted();
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  return (
    <div className="border-b last:border-b-0">
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Voto */}
          <div className="flex flex-col items-center gap-0.5 shrink-0 pt-0.5">
            <button
              onClick={handleVote}
              className={`w-7 h-7 flex items-center justify-center rounded-full transition-colors ${voted ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-blue-500 hover:bg-blue-50'}`}
              title={voted ? 'Remover voto' : 'Votar'}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill={voted ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </button>
            <span className={`text-xs font-semibold tabular-nums ${voteCount > 0 ? 'text-blue-600' : 'text-gray-400'}`}>{voteCount}</span>
          </div>

          {/* Conteúdo */}
          <div className="flex-1 min-w-0">
            <button
              className="w-full flex items-start justify-between gap-2 text-left group"
              onClick={() => setOpen(o => !o)}
            >
              <span className="text-sm font-semibold text-gray-800 group-hover:text-blue-600 transition-colors leading-snug">
                {entry.question}
              </span>
              <div className="flex items-center gap-2 shrink-0">
                {entry.comments.length > 0 && (
                  <span className="text-xs text-gray-400 flex items-center gap-0.5">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    {entry.comments.length}
                  </span>
                )}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
                  viewBox="0 0 20 20" fill="currentColor"
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            </button>

            {open && (
              <div className="mt-3 space-y-4">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {renderFormatted(entry.answer)}
                </p>

                {isProfessor && (
                  <div className="flex justify-end">
                    <button onClick={() => onDelete(entry.id)} className="text-xs text-red-400 hover:text-red-600">
                      remover entrada
                    </button>
                  </div>
                )}

                {/* Comentários */}
                <div className="border-t pt-3 space-y-2">
                  {entry.comments.map(c => (
                    <div key={c.id} className="flex gap-2 group/comment">
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-semibold text-gray-600">{c.author_name || 'Anônimo'} </span>
                        <span className="text-xs text-gray-400">{formatDate(c.created_at)}</span>
                        <p className="text-xs text-gray-700 mt-0.5 whitespace-pre-wrap">{c.text}</p>
                      </div>
                      {(isProfessor || c.author_id === currentUserId) && (
                        <button
                          onClick={() => handleDeleteComment(c.id)}
                          className="text-red-400 hover:text-red-600 opacity-0 group-hover/comment:opacity-100 shrink-0"
                          title="Remover comentário"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                      )}
                    </div>
                  ))}

                  <form onSubmit={handleComment} className="flex gap-2 mt-2">
                    <input
                      className="flex-1 border rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                      placeholder="Adicionar comentário..."
                      value={commentText}
                      onChange={e => setCommentText(e.target.value)}
                      maxLength={500}
                    />
                    <button
                      type="submit"
                      disabled={submitting || !commentText.trim()}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1 rounded text-xs disabled:opacity-40"
                    >
                      Enviar
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ManualPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [saving, setSaving] = useState(false);
  const payload = getTokenPayload();
  const isProfessor = payload?.role === 'professor';
  const currentUserId = payload?.researcher_id || payload?.sub;

  async function load() {
    const data = await getManualEntries();
    setEntries(data || []);
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    setSaving(true);
    await createManualEntry({ question: question.trim(), answer: answer.trim() });
    setQuestion('');
    setAnswer('');
    setSaving(false);
    load();
  }

  async function handleDelete(id) {
    if (!confirm('Remover esta entrada?')) return;
    await deleteManualEntry(id);
    load();
  }

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
        <div className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h1 className="text-xl font-bold text-gray-900">Manual de Sobrevivência</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        {isProfessor && (
          <section className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Nova entrada</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Pergunta..."
                value={question}
                onChange={e => setQuestion(e.target.value)}
                required
              />
              <RichTextarea
                value={answer}
                onChange={setAnswer}
                placeholder="Resposta... (selecione texto e clique B para negrito)"
                rows={4}
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={saving || !question.trim() || !answer.trim()}
                  className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Salvando...' : 'Adicionar'}
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="bg-white rounded-xl shadow-sm border divide-y">
          {entries.length === 0 && (
            <p className="text-sm text-gray-400 italic p-6">Nenhuma entrada ainda.</p>
          )}
          {entries.map(entry => (
            <EntryCard
              key={entry.id}
              entry={entry}
              isProfessor={isProfessor}
              currentUserId={currentUserId}
              onVote={load}
              onDelete={handleDelete}
              onCommentAdded={load}
              onCommentDeleted={load}
            />
          ))}
        </section>
      </main>
    </div>
  );
}
