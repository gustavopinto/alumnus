import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { getNotes, createNote, deleteNote, updateNote, toggleNoteReaction, addNoteComment, deleteNoteComment } from '../api';
import { modKey } from '../platform';
import Toast from './Toast';
import { slugify } from '../mentionUtils.jsx';
import RichEditor from './RichEditor';
import RichContent from './RichContent';
import { useConfirm } from './ConfirmModal';

const REACTIONS = [
  { type: 'like',  emoji: '👍', label: 'Curtir' },
  { type: 'happy', emoji: '🎉', label: 'Ótimo' },
  { type: 'sad',   emoji: '😢', label: 'Triste' },
];

function ReactionBar({ note, currentUserId, onToggle }) {
  const counts = REACTIONS.map(r => ({
    ...r,
    count: (note.reactions || []).filter(x => x.type === r.type).length,
    mine:  (note.reactions || []).some(x => x.type === r.type && x.user_id === currentUserId),
  }));
  const hasAny = counts.some(r => r.count > 0);
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {counts.map(r => (
        <button
          key={r.type}
          type="button"
          onClick={() => onToggle(note.id, r.type)}
          title={r.label}
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border transition-colors ${
            r.mine
              ? 'bg-blue-50 border-blue-300 text-blue-700 font-semibold'
              : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
          }`}
        >
          <span>{r.emoji}</span>
          {r.count > 0 && <span>{r.count}</span>}
        </button>
      ))}
      {!hasAny && (
        <span className="text-xs text-gray-300 italic">reagir</span>
      )}
    </div>
  );
}

function CommentsSection({ note, currentUserId, isProfessor, researchers, onCommentAdded, onCommentDeleted }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const count = (note.comments || []).length;

  async function handleAdd(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!text.trim()) return;
    setSending(true);
    try {
      await addNoteComment(note.id, text.trim());
      setText('');
      onCommentAdded();
    } finally {
      setSending(false);
    }
  }

  async function handleDelete(commentId) {
    await deleteNoteComment(commentId);
    onCommentDeleted();
  }

  return (
    <div className="border-t border-gray-100">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-1.5 px-5 py-2 text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        {count > 0 ? `${count} comentário${count > 1 ? 's' : ''}` : 'Comentar'}
        <svg xmlns="http://www.w3.org/2000/svg" className={`w-3 h-3 ml-auto transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-5 pb-4 space-y-3">
          {(note.comments || []).map(c => (
            <div key={c.id} className="flex items-start gap-2 group">
              <div className="w-6 h-6 rounded-full bg-gray-200 text-gray-600 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                {(c.author_name || '?').slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 font-semibold leading-tight">
                  {c.author_name || 'Anônimo'}
                  <span className="font-normal ml-1 text-gray-400">
                    {c.created_at ? new Date(c.created_at).toLocaleDateString('pt-BR') : ''}
                  </span>
                </p>
                <p className="text-sm text-gray-700 mt-0.5 leading-snug">{c.text}</p>
              </div>
              {(isProfessor || c.author_id === currentUserId) && (
                <button
                  type="button"
                  onClick={() => handleDelete(c.id)}
                  className="p-1 rounded text-gray-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                  title="Remover"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
          <form onSubmit={handleAdd} className="flex gap-2 pt-1">
            <input
              type="text"
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Comentar..."
              className="flex-1 border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50"
            />
            <button
              type="submit"
              disabled={sending || !text.trim()}
              className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 shrink-0"
            >
              {sending ? '…' : 'Enviar'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function NotesSection({ userId, canAdd, isProfessor, currentUserId, researchers = [], preview = false, slug, alwaysOpen = false }) {
  const [open, setOpen] = useState(preview || alwaysOpen);
  const [notes, setNotes] = useState([]);
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [toast, setToast] = useState('');
  const { confirm, modal: confirmModal } = useConfirm();
  const fileRef = useRef();
  const loadNotesInFlight = useRef(false);
  const loaded = useRef(false);

  async function load() {
    if (loadNotesInFlight.current) return;
    loadNotesInFlight.current = true;
    try {
      const data = await getNotes(userId);
      setNotes(Array.isArray(data) ? data : []);
    } finally {
      loadNotesInFlight.current = false;
    }
  }

  useEffect(() => { loaded.current = false; setNotes([]); }, [userId]);

  useEffect(() => {
    if (preview) { loaded.current = true; load(); return; }
    if (open && !loaded.current) { loaded.current = true; load(); }
  }, [open, preview]); // eslint-disable-line

  async function handleSubmit(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!text.trim()) return;
    setSaving(true);
    await createNote(userId, text, file);
    setText('');
    setFile(null);
    if (fileRef.current) fileRef.current.value = '';
    setSaving(false);
    setToast('Anotação adicionada');
    load();
  }

  function startEdit(note) {
    setEditingId(note.id);
    setEditText(note.text);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditText('');
  }

  async function handleEditSubmit(noteId) {
    if (!editText.trim()) return;
    setEditSaving(true);
    await updateNote(noteId, editText);
    setEditingId(null);
    setEditText('');
    setEditSaving(false);
    setToast('Anotação atualizada');
    load();
  }

  async function handleDelete(id) {
    if (!await confirm({ title: 'Remover esta anotação?', confirmLabel: 'Remover' })) return;
    await deleteNote(id);
    load();
  }

  async function handleReaction(noteId, type) {
    if (!currentUserId) return;
    await toggleNoteReaction(noteId, type);
    load();
  }

  const visibleNotes = preview ? notes.slice(0, 3) : notes;

  if (preview) {
    return (
      <div className="space-y-0">
        {confirmModal}
        <Toast message={toast} onClose={() => setToast('')} />
        <section className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">📝 Anotações</h2>
            {slug && notes.length > 0 && (
              <Link to={`/app/profile/${slug}/notes`} className="text-sm text-blue-600 hover:underline">
                Ver todas →
              </Link>
            )}
          </div>
          <div className="px-6 py-4 space-y-4">
            {canAdd && (
              <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                  type="text"
                  value={text}
                  onChange={e => setText(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) handleSubmit(e); }}
                  placeholder="Nova anotação..."
                  className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50"
                  disabled={saving}
                />
                <button
                  type="submit"
                  disabled={saving || !text.trim()}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 shrink-0"
                >
                  {saving ? '...' : 'Adicionar'}
                </button>
              </form>
            )}
            {visibleNotes.length === 0 && loaded.current ? (
              <p className="text-xs text-gray-400">Nenhuma anotação ainda.</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {visibleNotes.map(note => (
                  <li key={note.id} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-gray-400">{formatDate(note.created_at)}</span>
                      {note.created_by_name && (
                        <span className="text-xs text-gray-500">
                          por <Link to={`/app/profile/${slugify(note.created_by_name)}`} className="font-semibold text-gray-700 hover:underline hover:text-blue-600">{note.created_by_name}</Link>
                        </span>
                      )}
                    </div>
                    <RichContent html={note.text} researchers={researchers} className="text-sm text-gray-700 line-clamp-2" />
                    {currentUserId && (
                      <div className="mt-2">
                        <ReactionBar note={note} currentUserId={currentUserId} onToggle={handleReaction} />
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {confirmModal}
      <Toast message={toast} onClose={() => setToast('')} />
      <section className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {alwaysOpen ? (
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-bold text-gray-800">📝 Anotações de reuniões</h2>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setOpen(o => !o)}
            className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
          >
            <h2 className="text-lg font-bold text-gray-800">📝 Anotações de reuniões</h2>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}

        {(open || alwaysOpen) && (
          <div className="px-6 pb-6 border-t">
            {canAdd && (
              <form onSubmit={handleSubmit} className="space-y-2 pt-4">
                <RichEditor
                  variant="simple"
                  researchers={researchers}
                  value={text}
                  onChange={setText}
                  onSubmit={handleSubmit}
                  placeholder="Nova anotação... (@ para mencionar alguém)"
                />
                <div className="flex items-center gap-3">
                  <label className="text-sm text-gray-500 cursor-pointer hover:text-blue-600 flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                    {file ? file.name : 'Anexar arquivo'}
                    <input ref={fileRef} type="file" accept="image/*,.pdf" className="hidden" onChange={(e) => setFile(e.target.files[0] || null)} />
                  </label>
                  {file && (
                    <button type="button" onClick={() => { setFile(null); fileRef.current.value = ''; }} className="text-xs text-red-400 hover:text-red-600">
                      remover
                    </button>
                  )}
                  <button type="submit" disabled={saving || !text.trim()} className="ml-auto bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
                    {saving ? 'Salvando...' : <>Adicionar <span className="opacity-50 text-xs">{modKey}+Enter</span></>}
                  </button>
                </div>
              </form>
            )}
            {notes.length === 0 && loaded.current && !canAdd && (
              <p className="text-xs text-gray-400 py-4">Nenhuma anotação ainda.</p>
            )}
            {notes.length === 0 && loaded.current && canAdd && (
              <p className="text-xs text-gray-400 pt-3">Nenhuma anotação ainda.</p>
            )}
          </div>
        )}
      </section>

      {/* Cards de anotações — fora do box principal */}
      {(open || alwaysOpen) && notes.length > 0 && (
        <div className="space-y-4 mt-6">
          {notes.map(note => {
            const initials = (note.created_by_name || '?').split(' ').filter(Boolean).slice(0, 2).map(p => p[0].toUpperCase()).join('');
            return (
              <div key={note.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {initials}
                    </div>
                    <div>
                      {note.created_by_name ? (
                        <Link to={`/app/profile/${slugify(note.created_by_name)}`} className="text-sm font-semibold text-gray-800 hover:text-blue-600 hover:underline leading-none">
                          {note.created_by_name}
                        </Link>
                      ) : (
                        <span className="text-sm font-semibold text-gray-800 leading-none">Anônimo</span>
                      )}
                      <p className="text-xs text-gray-400 mt-0.5">{formatDate(note.created_at)}</p>
                    </div>
                  </div>
                  {(isProfessor || note.created_by_id === currentUserId) && (
                    <div className="flex items-center gap-1">
                      <button onClick={() => startEdit(note)} title="Editar anotação" className="p-1.5 rounded-lg text-gray-300 hover:text-blue-500 hover:bg-blue-50 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button onClick={() => handleDelete(note.id)} title="Remover anotação" className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
                {/* Corpo */}
                <div className="px-5 py-5 bg-gray-50 border-t border-gray-100">
                  {editingId === note.id ? (
                    <div className="space-y-2">
                      <RichEditor
                        variant="simple"
                        researchers={researchers}
                        value={editText}
                        onChange={setEditText}
                        onSubmit={() => handleEditSubmit(note.id)}
                        placeholder="Editar anotação..."
                      />
                      <div className="flex items-center gap-2 justify-end">
                        <button type="button" onClick={cancelEdit} className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-100">
                          Cancelar
                        </button>
                        <button type="button" onClick={() => handleEditSubmit(note.id)} disabled={editSaving || !editText.trim()} className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
                          {editSaving ? 'Salvando...' : 'Salvar'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <RichContent html={note.text} researchers={researchers} className="text-sm text-gray-700 leading-relaxed" />
                  )}
                  {note.file_url && (
                    <a href={note.file_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 mt-3 text-xs text-blue-600 hover:underline">
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                      </svg>
                      {note.file_name || 'Anexo'}
                    </a>
                  )}
                </div>
                {/* Reactions */}
                {currentUserId && (
                  <div className="px-5 py-2.5 border-t border-gray-100 bg-white">
                    <ReactionBar
                      note={note}
                      currentUserId={currentUserId}
                      onToggle={handleReaction}
                    />
                  </div>
                )}
                {/* Comments */}
                {currentUserId && (
                  <CommentsSection
                    note={note}
                    currentUserId={currentUserId}
                    isProfessor={isProfessor}
                    researchers={researchers}
                    onCommentAdded={load}
                    onCommentDeleted={load}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
