import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { modKey, isModEnter } from '../platform';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTips, createTip, deleteTip,
  toggleTipVote, addTipComment, deleteTipComment,
} from '../api';
import { getTokenPayload, isDashboardRole } from '../auth';
import { useAppLayout } from '../components/AppLayout';
import { keys } from '../queryKeys';
import Toast from '../components/Toast';

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

function RichTextarea({ value, onChange, placeholder, rows = 4, id, required, onKeyDown }) {
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
        id={id}
        required={required}
        aria-required={required ? true : undefined}
        className="w-full px-3 py-2 text-sm resize-none focus:outline-none"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        rows={rows}
      />
    </div>
  );
}

function sameUser(a, b) {
  if (a == null || b == null) return false;
  return Number(a) === Number(b);
}

function EntryCard({ entry, authUserId, canModerate, onVote, onDelete, onCommentAdded, onCommentDeleted }) {
  const [commentsOpen, setCommentsOpen] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [voted, setVoted] = useState(entry.user_voted);
  const [voteCount, setVoteCount] = useState(entry.vote_count);

  async function handleVote(e) {
    e.stopPropagation();
    const result = await toggleTipVote(entry.id);
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
    await addTipComment(entry.id, commentText.trim());
    setCommentText('');
    setSubmitting(false);
    onCommentAdded();
  }

  async function handleDeleteComment(commentId) {
    await deleteTipComment(commentId);
    onCommentDeleted();
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  const canDeleteEntry = sameUser(entry.author_id, authUserId) || canModerate;

  return (
    <article className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-4 py-5 sm:px-6">
        <div className="flex items-start gap-3">
          {/* Voto */}
          <div className="flex flex-col items-center gap-0.5 shrink-0 pt-1">
            <button
              type="button"
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
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-sm font-semibold text-gray-900 leading-snug pr-2">
                {entry.question}
              </h3>
              {canDeleteEntry && (
                <button
                  type="button"
                  onClick={() => onDelete(entry.id)}
                  className="shrink-0 -mt-1 -mr-1 p-1.5 rounded-md text-red-400 hover:text-red-600 hover:bg-red-50 transition-colors self-start"
                  title="Remover entrada"
                  aria-label="Remover entrada"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>

            <p className="text-xs text-gray-500 mt-1.5">
              {entry.author_name ? (
                <>Por <Link to={`/app/profile/${slugify(entry.author_name)}`} className="font-medium text-gray-700 hover:text-blue-600 hover:underline">{entry.author_name}</Link></>
              ) : (
                <span className="italic">Autor desconhecido</span>
              )}
              {entry.created_at && (
                <span className="text-gray-400"> · {formatDate(entry.created_at)}</span>
              )}
            </p>

            <div className="mt-3 rounded-lg bg-gray-50 border border-gray-100 px-3 py-3">
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                {renderFormatted(entry.answer)}
              </p>
            </div>

            <button
              type="button"
              className="mt-4 w-full flex items-center justify-between gap-2 text-left py-1 text-xs font-medium text-gray-600 hover:text-gray-900"
              onClick={() => setCommentsOpen(o => !o)}
            >
              <span className="flex items-center gap-1.5">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Comentários
                {entry.comments.length > 0 && (
                  <span className="text-gray-400 font-normal">({entry.comments.length})</span>
                )}
              </span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className={`w-4 h-4 text-gray-400 transition-transform shrink-0 ${commentsOpen ? 'rotate-180' : ''}`}
                viewBox="0 0 20 20" fill="currentColor"
              >
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>

            {commentsOpen && (
              <div className="mt-2 border-t border-gray-100 pt-3 space-y-2">
                {entry.comments.map(c => (
                  <div key={c.id} className="flex gap-2 group/comment">
                    <div className="flex-1 min-w-0">
                      {c.author_name
                        ? <Link to={`/app/profile/${slugify(c.author_name)}`} className="text-xs font-semibold text-gray-600 hover:text-blue-600 hover:underline">{c.author_name}</Link>
                        : <span className="text-xs font-semibold text-gray-600">Anônimo</span>
                      }{' '}
                      <span className="text-xs text-gray-400">{formatDate(c.created_at)}</span>
                      <p className="text-xs text-gray-700 mt-0.5 whitespace-pre-wrap">{c.text}</p>
                    </div>
                    {(sameUser(c.author_id, authUserId) || canModerate) && (
                      <button
                        type="button"
                        onClick={() => handleDeleteComment(c.id)}
                        className="text-red-400 hover:text-red-600 opacity-0 group-hover/comment:opacity-100 shrink-0 p-0.5 self-start"
                        title="Remover comentário"
                        aria-label="Remover comentário"
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
                    onKeyDown={e => isModEnter(e) && handleComment(e)}
                    maxLength={500}
                  />
                  <button
                    type="submit"
                    disabled={submitting || !commentText.trim()}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1 rounded text-xs disabled:opacity-40"
                  >
                    Enviar <span className="opacity-50">{modKey}+Enter</span>
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

export default function ManualPage() {
  const { currentInstitution } = useAppLayout();
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [toast, setToast] = useState('');
  const payload = getTokenPayload();
  const canModerateManual = isDashboardRole(payload?.role);
  const authUserId = payload?.sub != null ? Number(payload.sub) : null;

  const queryClient = useQueryClient();
  const instId = currentInstitution !== undefined ? (currentInstitution?.id ?? null) : undefined;
  const { data: entries = [] } = useQuery({
    queryKey: keys.tips(instId),
    queryFn: () => getTips(instId),
    enabled: instId !== undefined,
  });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: keys.tips(instId) });

  const createMutation = useMutation({
    mutationFn: () => createTip({ question: question.trim(), answer: answer.trim() }, instId),
    onSuccess: () => { setQuestion(''); setAnswer(''); setToast('Entrada adicionada com sucesso'); invalidate(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteTip(id),
    onSuccess: () => { setToast('Entrada removida'); invalidate(); },
  });

  function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    createMutation.mutate();
  }

  async function handleDelete(id) {
    if (!confirm('Remover esta entrada?')) return;
    deleteMutation.mutate(id);
  }

  return (
    <div className="min-h-full bg-gray-50">
      <Toast message={toast} onClose={() => setToast('')} />
      <main className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <section className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Nova entrada</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label htmlFor="manual-question" className="block text-xs font-medium text-gray-700 mb-1">
                  Pergunta <span className="text-red-500" aria-hidden="true">*</span>
                </label>
                <input
                  id="manual-question"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Pergunta..."
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (isModEnter(e)) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  required
                  aria-required="true"
                />
              </div>
              <div>
                <label htmlFor="manual-answer" className="block text-xs font-medium text-gray-700 mb-1">
                  Resposta <span className="text-red-500" aria-hidden="true">*</span>
                </label>
                <RichTextarea
                  id="manual-answer"
                  required
                  value={answer}
                  onChange={setAnswer}
                  placeholder="Resposta... (selecione texto e clique B para negrito)"
                  rows={4}
                  onKeyDown={e => isModEnter(e) && handleSubmit(e)}
                />
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={createMutation.isPending || !question.trim() || !answer.trim()}
                  className="ml-auto bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Salvando...' : <>Adicionar <span className="opacity-50 text-xs">{modKey}+Enter</span></>}
                </button>
              </div>
            </form>
          </section>

        <section className="flex flex-col gap-6" aria-label="Entradas do manual">
          {entries.length === 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm px-6 py-10 text-center">
              <p className="text-sm text-gray-400 italic">Nenhuma entrada ainda.</p>
            </div>
          )}
          {entries.map(entry => (
            <EntryCard
              key={entry.id}
              entry={entry}
              authUserId={authUserId}
              canModerate={canModerateManual}
              onVote={invalidate}
              onDelete={handleDelete}
              onCommentAdded={invalidate}
              onCommentDeleted={invalidate}
            />
          ))}
        </section>
      </main>
    </div>
  );
}
