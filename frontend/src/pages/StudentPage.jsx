import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStudentBySlug, updateStudent, getWorks, createWork, updateWork, deleteWork, getNotes, createNote, deleteNote } from '../api';

const STATUS_LABELS = { graduacao: 'Graduação', mestrado: 'Mestrado', doutorado: 'Doutorado', professor: 'Professor' };
const STATUS_COLORS = { graduacao: '#3B82F6', mestrado: '#F59E0B', doutorado: '#10B981', professor: '#7C3AED' };

const WORK_TYPES = [
  { type: 'projeto',    label: 'Projetos' },
  { type: 'artigo',     label: 'Artigos em andamento' },
  { type: 'publicacao', label: 'Publicações' },
];

function formatDate(iso) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function NotesSection({ studentId }) {
  const [notes, setNotes] = useState([]);
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const fileRef = useRef();

  async function load() {
    const data = await getNotes(studentId);
    setNotes(data);
  }

  useEffect(() => { load(); }, [studentId]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setSaving(true);
    await createNote(studentId, text, file);
    setText('');
    setFile(null);
    if (fileRef.current) fileRef.current.value = '';
    setSaving(false);
    load();
  }

  async function handleDelete(id) {
    if (!confirm('Remover esta anotação?')) return;
    await deleteNote(id);
    load();
  }

  return (
    <div className="space-y-4">
    <section className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-4">Anotações</h2>

      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          className="w-full border rounded-lg px-3 py-2 text-sm h-24 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Nova anotação..."
          value={text}
          onChange={(e) => setText(e.target.value)}
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
            {saving ? 'Salvando...' : 'Adicionar'}
          </button>
        </div>
      </form>
    </section>

    <section className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-4">Histórico</h2>
      <div className="max-h-96 overflow-y-auto">
        {notes.length === 0 && <p className="text-sm text-gray-400 italic">Nenhuma anotação ainda.</p>}
        <ul className="space-y-4">
          {notes.map(note => (
            <li key={note.id} className="border-l-2 border-blue-200 pl-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-400">{formatDate(note.created_at)}</span>
                <button onClick={() => handleDelete(note.id)} className="text-xs text-red-400 hover:text-red-600">remover</button>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{note.text}</p>
              {note.file_url && (
                <a href={note.file_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 mt-1 text-xs text-blue-600 hover:underline">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                  {note.file_name || 'Anexo'}
                </a>
              )}
            </li>
          ))}
        </ul>
      </div>
    </section>
    </div>
  );
}

function WorkSection({ title, type, works, studentId, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ title: '', description: '', year: '', url: '' });

  const filtered = works.filter(w => w.type === type);
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  function openNew() {
    setEditing(null);
    setForm({ title: '', description: '', year: '', url: '' });
    setShowForm(true);
  }

  function openEdit(w) {
    setEditing(w);
    setForm({ title: w.title, description: w.description || '', year: w.year || '', url: w.url || '' });
    setShowForm(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const payload = { ...form, type, year: form.year ? Number(form.year) : null };
    if (editing) {
      await updateWork(editing.id, payload);
    } else {
      await createWork(studentId, payload);
    }
    setShowForm(false);
    onRefresh();
  }

  async function handleDelete(id) {
    if (!confirm('Remover este item?')) return;
    await deleteWork(id);
    onRefresh();
  }

  return (
    <section className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800">{title}</h2>
        <button onClick={openNew} className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700">
          + Adicionar
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mb-4 p-4 bg-gray-50 rounded-lg space-y-2 border">
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Título *" required value={form.title} onChange={set('title')} />
          <textarea className="w-full border rounded px-3 py-2 text-sm" placeholder="Descrição" rows={2} value={form.description} onChange={set('description')} />
          <div className="flex gap-2">
            <input className="w-32 border rounded px-3 py-2 text-sm" placeholder="Ano" type="number" value={form.year} onChange={set('year')} />
            <input className="flex-1 border rounded px-3 py-2 text-sm" placeholder="URL" value={form.url} onChange={set('url')} />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700">
              {editing ? 'Salvar' : 'Criar'}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="bg-gray-200 px-4 py-1.5 rounded text-sm hover:bg-gray-300">
              Cancelar
            </button>
          </div>
        </form>
      )}

      {filtered.length === 0 && !showForm && (
        <p className="text-sm text-gray-400 italic">Nenhum item cadastrado.</p>
      )}

      <ul className="space-y-3">
        {filtered.map(w => (
          <li key={w.id} className="flex items-start justify-between gap-4 border-b pb-3 last:border-0 last:pb-0">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 text-sm">
                {w.url ? (
                  <a href={w.url} target="_blank" rel="noreferrer" className="hover:text-blue-600 underline underline-offset-2">{w.title}</a>
                ) : w.title}
                {w.year && <span className="ml-2 text-gray-400 text-xs font-normal">({w.year})</span>}
              </p>
              {w.description && <p className="text-xs text-gray-500 mt-0.5">{w.description}</p>}
            </div>
            <div className="flex gap-2 shrink-0 text-xs">
              <button onClick={() => openEdit(w)} className="text-blue-600 hover:underline">editar</button>
              <button onClick={() => handleDelete(w.id)} className="text-red-500 hover:underline">remover</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function StudentPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [works, setWorks] = useState([]);

  async function load() {
    const s = await getStudentBySlug(slug);
    const w = await getWorks(s.id);
    setStudent(s);
    setWorks(w);
  }

  useEffect(() => { load(); }, [slug]);

  if (!student) {
    return <div className="flex items-center justify-center h-screen text-gray-400">Carregando...</div>;
  }

  const color = STATUS_COLORS[student.status] || '#6B7280';

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
        {student.photo_url ? (
          <img src={student.photo_url} alt={student.nome} className="w-12 h-12 rounded-full object-cover border-2" style={{ borderColor: color }} />
        ) : (
          <div className="w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold" style={{ backgroundColor: color }}>
            {student.nome.charAt(0).toUpperCase()}
          </div>
        )}
        <div>
          <h1 className="text-xl font-bold text-gray-900">{student.nome}</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: color }}>
              {STATUS_LABELS[student.status] || student.status}
            </span>
            {student.email && <span className="text-xs text-gray-500">{student.email}</span>}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto py-8 px-4 space-y-6">
        <NotesSection studentId={student.id} />
      </main>
    </div>
  );
}
