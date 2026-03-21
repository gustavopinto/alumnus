import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAppLayout } from '../components/AppLayout';
import { getResearcherBySlug, updateResearcher, uploadPhoto, getNotes, createNote, deleteNote, getResearcherUser, getDeadlineInterests } from '../api';
import { DEADLINES, slugify } from '../deadlines';
import { getTokenPayload } from '../auth';
import Toast from '../components/Toast';

const STATUS_LABELS = { graduacao: 'Graduação', mestrado: 'Mestrado', doutorado: 'Doutorado', professor: 'Professor' };
const STATUS_COLORS = { graduacao: '#3B82F6', mestrado: '#F59E0B', doutorado: '#10B981', professor: '#7C3AED' };

function formatDate(iso) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatLastLogin(iso) {
  const now = new Date();
  const loginDate = new Date(iso);
  const diffMs = now - loginDate;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Último acesso: hoje';
  if (diffDays === 1) return 'Último acesso: ontem';
  if (diffDays <= 10) return `Último acesso: há ${diffDays} dias`;
  return 'Último acesso: há mais de 10 dias';
}

function NotesSection({ researcherId, canAdd, isProfessor, currentUserId }) {
  const [notes, setNotes] = useState([]);
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');
  const fileRef = useRef();

  async function load() {
    const data = await getNotes(researcherId);
    setNotes(data);
  }

  useEffect(() => { load(); }, [researcherId]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setSaving(true);
    await createNote(researcherId, text, file);
    setText('');
    setFile(null);
    if (fileRef.current) fileRef.current.value = '';
    setSaving(false);
    setToast('Anotação adicionada');
    load();
  }

  async function handleDelete(id) {
    if (!confirm('Remover esta anotação?')) return;
    await deleteNote(id);
    load();
  }

  const lastNote = notes.length > 0 ? notes[0] : null;

  return (
    <div className="space-y-4">
    <Toast message={toast} onClose={() => setToast('')} />
    {canAdd && <section className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800">Anotações de reuniões</h2>
        {lastNote && (
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Última: {formatDate(lastNote.created_at)}
          </span>
        )}
      </div>

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
    </section>}

    {notes.length > 0 && (
    <section className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-4">Histórico de anotações</h2>
      <div className="max-h-96 overflow-y-auto">
        <ul className="space-y-4">
          {notes.map(note => (
            <li key={note.id} className="border-l-2 border-blue-200 pl-4">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <span className="text-xs text-gray-400">{formatDate(note.created_at)}</span>
                  {note.created_by_name && (
                    <span className="ml-1.5 text-xs text-gray-500">
                      por <Link to={`/profile/${slugify(note.created_by_name)}`} className="hover:underline hover:text-gray-700">{note.created_by_name}</Link>
                    </span>
                  )}
                </div>
                {(isProfessor || note.created_by_id === currentUserId) && (
                  <button onClick={() => handleDelete(note.id)} className="text-xs text-red-400 hover:text-red-600">remover</button>
                )}
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
    )}
    </div>
  );
}

function ProfileSection({ researcher, canEdit, isProfessor, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    lattes_url: researcher.lattes_url || '',
    scholar_url: researcher.scholar_url || '',
    linkedin_url: researcher.linkedin_url || '',
    github_url: researcher.github_url || '',
    instagram_url: researcher.instagram_url ? researcher.instagram_url.replace(/^https?:\/\/(www\.)?(instagram\.com|x\.com|twitter\.com)\//, '').replace(/^@/, '') : '',
    twitter_url: researcher.twitter_url ? researcher.twitter_url.replace(/^https?:\/\/(www\.)?(instagram\.com|x\.com|twitter\.com)\//, '').replace(/^@/, '') : '',
    whatsapp: researcher.whatsapp || '',
    interesses: researcher.interesses || '',
  });
  const [whatsappError, setWhatsappError] = useState('');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoPreview, setPhotoPreview] = useState(researcher.photo_url || null);
  const [pendingPhotoUrl, setPendingPhotoUrl] = useState(null);
  const photoRef = useRef();

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  function maskPhone(value) {
    const digits = value.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 10)
      return digits.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3').replace(/-$/, '');
    return digits.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3').replace(/-$/, '');
  }

  function handleWhatsApp(e) {
    const masked = maskPhone(e.target.value);
    setForm({ ...form, whatsapp: masked });
    const digits = masked.replace(/\D/g, '');
    setWhatsappError(digits.length > 0 && digits.length < 10 ? 'Número inválido' : '');
  }

  async function handlePhotoSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingPhoto(true);
    const res = await uploadPhoto(file);
    setPendingPhotoUrl(res.url);
    setPhotoPreview(res.url);
    setUploadingPhoto(false);
  }

  async function handleSave(e) {
    e.preventDefault();
    const digits = form.whatsapp.replace(/\D/g, '');
    if (form.whatsapp && digits.length < 10) { setWhatsappError('Número inválido'); return; }
    setSaving(true);
    await updateResearcher(researcher.id, {
      lattes_url: form.lattes_url || null,
      scholar_url: form.scholar_url || null,
      linkedin_url: form.linkedin_url || null,
      github_url: form.github_url || null,
      instagram_url: form.instagram_url ? form.instagram_url.replace(/^@/, '') : null,
      twitter_url: form.twitter_url ? form.twitter_url.replace(/^@/, '') : null,
      whatsapp: form.whatsapp || null,
      interesses: form.interesses || null,
      ...(pendingPhotoUrl ? { photo_url: pendingPhotoUrl } : {}),
    });
    setSaving(false);
    setEditing(false);
    setPendingPhotoUrl(null);
    setToast('Perfil salvo com sucesso');
    onSaved();
  }

  function handleCancel() {
    setEditing(false);
    setPhotoPreview(researcher.photo_url || null);
    setPendingPhotoUrl(null);
  }

  const links = [
    { key: 'lattes_url', label: 'Lattes', value: researcher.lattes_url,
      cls: 'text-teal-700 bg-teal-50 border-teal-200 hover:bg-teal-100',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
        </svg>
      )},
    { key: 'scholar_url', label: 'Google Scholar', value: researcher.scholar_url,
      cls: 'text-indigo-600 bg-indigo-50 border-indigo-200 hover:bg-indigo-100',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3L1 9l4 2.18V17h2v-4.82L12 14l7-3.82V17h2v-5.82L23 9 12 3zm0 2.36L18.5 9 12 12.36 5.5 9 12 5.36zM5 19v2h14v-2H5z"/>
        </svg>
      )},
    { key: 'linkedin_url', label: 'LinkedIn', value: researcher.linkedin_url,
      cls: 'text-blue-700 bg-blue-50 border-blue-200 hover:bg-blue-100',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 3a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14m-.5 15.5v-5.3a3.26 3.26 0 00-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 011.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 001.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 00-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
        </svg>
      )},
    { key: 'github_url', label: 'GitHub', value: researcher.github_url,
      cls: 'text-gray-800 bg-gray-100 border-gray-300 hover:bg-gray-200',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2A10 10 0 002 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/>
        </svg>
      )},
    { key: 'instagram_url', label: 'Instagram', value: researcher.instagram_url ? (researcher.instagram_url.startsWith('http') ? researcher.instagram_url : `https://instagram.com/${researcher.instagram_url.replace(/^@/, '')}`) : null,
      cls: 'text-pink-600 bg-pink-50 border-pink-200 hover:bg-pink-100',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 01-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 017.8 2m-.2 2A3.6 3.6 0 004 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 003.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 011.25 1.25A1.25 1.25 0 0117.25 8 1.25 1.25 0 0116 6.75a1.25 1.25 0 011.25-1.25M12 7a5 5 0 015 5 5 5 0 01-5 5 5 5 0 01-5-5 5 5 0 015-5m0 2a3 3 0 00-3 3 3 3 0 003 3 3 3 0 003-3 3 3 0 00-3-3z"/>
        </svg>
      )},
    { key: 'twitter_url', label: 'Twitter / X', value: researcher.twitter_url ? (researcher.twitter_url.startsWith('http') ? researcher.twitter_url : `https://x.com/${researcher.twitter_url.replace(/^@/, '')}`) : null,
      cls: 'text-sky-600 bg-sky-50 border-sky-200 hover:bg-sky-100',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.253 5.622 5.91-5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      )},
  ];

  return (
    <>
    <Toast message={toast} onClose={() => setToast('')} />
    <section className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800">Perfil</h2>
        {canEdit && !editing && (
          <button onClick={() => setEditing(true)} className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Editar
          </button>
        )}
      </div>

      {editing ? (
        <form onSubmit={handleSave} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-2">Foto de perfil</label>
            <div className="flex items-center gap-3">
              {photoPreview ? (
                <img src={photoPreview} alt="" className="w-14 h-14 rounded-full object-cover border-2 border-gray-200" />
              ) : (
                <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 text-xs border-2 border-dashed border-gray-300">
                  sem foto
                </div>
              )}
              <div>
                <button
                  type="button"
                  onClick={() => photoRef.current.click()}
                  disabled={uploadingPhoto}
                  className="text-sm text-blue-600 hover:underline disabled:opacity-50"
                >
                  {uploadingPhoto ? 'Enviando...' : 'Escolher imagem'}
                </button>
                <p className="text-xs text-gray-400 mt-0.5">JPG, PNG ou WebP · máx. 5 MB</p>
                <input ref={photoRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoSelect} />
              </div>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">WhatsApp *</label>
            <input
              type="tel"
              required
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 ${whatsappError ? 'border-red-400' : ''}`}
              placeholder="(XX) XXXXX-XXXX"
              value={form.whatsapp}
              onChange={handleWhatsApp}
            />
            {whatsappError && <p className="text-xs text-red-500 mt-0.5">{whatsappError}</p>}
          </div>
          {[
            { key: 'lattes_url', label: 'Lattes', placeholder: 'http://lattes.cnpq.br/...' },
            { key: 'scholar_url', label: 'Google Scholar', placeholder: 'https://scholar.google.com/...' },
            { key: 'linkedin_url', label: 'LinkedIn', placeholder: 'https://linkedin.com/in/...' },
            { key: 'github_url', label: 'GitHub', placeholder: 'https://github.com/...' },
          ].map(({ key, label, placeholder }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
              <input
                type="url"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder={placeholder}
                value={form[key]}
                onChange={set(key)}
              />
            </div>
          ))}
          {[
            { key: 'instagram_url', label: 'Instagram' },
            { key: 'twitter_url', label: 'Twitter / X' },
          ].map(({ key, label }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
              <input
                type="text"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="@usuario"
                maxLength={50}
                value={form[key]}
                onChange={set(key)}
              />
            </div>
          ))}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Interesses de pesquisa</label>
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm h-20 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Ex: engenharia de software, mineração de repositórios..."
              value={form.interesses}
              onChange={set('interesses')}
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button type="button" onClick={handleCancel} className="bg-gray-200 px-4 py-1.5 rounded-lg text-sm hover:bg-gray-300">
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {links.map(({ label, value, icon, cls }) => value ? (
              <a key={label} href={value} target="_blank" rel="noreferrer"
                className={`inline-flex items-center gap-1.5 text-sm px-3 py-1 rounded-full border transition-colors ${cls}`}>
                {icon}
                {label}
              </a>
            ) : null)}
            {researcher.whatsapp && (
              <a
                href={`https://wa.me/55${researcher.whatsapp.replace(/\D/g, '')}`}
                target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-green-600 hover:underline bg-green-50 px-3 py-1 rounded-full border border-green-100"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                WhatsApp
              </a>
            )}
            {links.every(l => !l.value) && !researcher.interesses && !researcher.whatsapp && (
              <p className="text-sm text-gray-400 italic">Nenhuma informação de perfil cadastrada.</p>
            )}
          </div>
          {researcher.interesses && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">Interesses de pesquisa</p>
              <p className="text-sm text-gray-700">{researcher.interesses}</p>
            </div>
          )}
          {isProfessor && (researcher.matricula || researcher.curso || researcher.enrollment_date) && (
            <div className="border-t pt-3 mt-1 flex gap-6 flex-wrap">
              {researcher.matricula && (
                <div>
                  <p className="text-xs font-medium text-gray-500">Matrícula</p>
                  <p className="text-sm text-gray-700">{researcher.matricula}</p>
                </div>
              )}
              {researcher.curso && (
                <div>
                  <p className="text-xs font-medium text-gray-500">Curso</p>
                  <p className="text-sm text-gray-700">{researcher.curso}</p>
                </div>
              )}
              {researcher.enrollment_date && (
                <div>
                  <p className="text-xs font-medium text-gray-500">Ingresso</p>
                  <p className="text-sm text-gray-700">
                    {new Date(researcher.enrollment_date + 'T00:00:00').toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' })}
                  </p>
                </div>
              )}
              {researcher.enrollment_date && (researcher.status === 'mestrado' || researcher.status === 'doutorado') && (() => {
                const years = researcher.status === 'mestrado' ? 2 : 4;
                const d = new Date(researcher.enrollment_date + 'T00:00:00');
                d.setFullYear(d.getFullYear() + years);
                return (
                  <div>
                    <p className="text-xs font-medium text-gray-500">Possível Formatura</p>
                    <p className="text-sm text-gray-700">
                      {d.toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' })}
                    </p>
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      )}
    </section>
    </>
  );
}

export default function ResearcherPage() {
  const { slug } = useParams();
  const { sidebarOpen } = useAppLayout();
  const headerPad = sidebarOpen ? 'pl-14' : '';
  const [researcher, setResearcher] = useState(null);
  const [researcherUser, setResearcherUser] = useState(null);
  const [myDeadlines, setMyDeadlines] = useState([]);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const photoInputRef = useRef();

  const payload = getTokenPayload();
  const isProfessor = payload?.role === 'professor';
  const isOwnProfile = payload?.researcher_id != null && researcher?.id === payload.researcher_id;
  const canEdit = isProfessor || isOwnProfile;

  async function load() {
    const r = await getResearcherBySlug(slug);
    const [u, allInterests] = await Promise.all([getResearcherUser(r.id), getDeadlineInterests()]);
    setResearcher(r);
    setResearcherUser(u);
    if (u && allInterests) {
      const keys = allInterests.filter(i => i.user_id === u.id).map(i => i.deadline_key);
      setMyDeadlines(DEADLINES.filter(d => keys.includes(d.label)));
    }
  }

  useEffect(() => { load(); }, [slug]);

  async function handlePhotoChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingPhoto(true);
    const res = await uploadPhoto(file);
    await updateResearcher(researcher.id, { photo_url: res.url });
    setUploadingPhoto(false);
    load();
  }

  if (!researcher) {
    return <div className="flex items-center justify-center min-h-[50vh] text-gray-400">Carregando...</div>;
  }

  const color = STATUS_COLORS[researcher.status] || '#6B7280';

  return (
    <div className="min-h-full bg-gray-50">
      <header className={`bg-white border-b shadow-sm px-6 py-4 flex items-center gap-4 ${headerPad}`}>
        <div className="relative group shrink-0">
          {researcher.photo_url ? (
            <img src={researcher.photo_url} alt={researcher.nome} className="w-12 h-12 rounded-full object-cover border-2" style={{ borderColor: color }} />
          ) : (
            <div className="w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold" style={{ backgroundColor: color }}>
              {researcher.nome.charAt(0).toUpperCase()}
            </div>
          )}
          {canEdit && (
            <>
              <button
                type="button"
                onClick={() => photoInputRef.current.click()}
                disabled={uploadingPhoto}
                className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-100"
                title="Alterar foto"
              >
                {uploadingPhoto ? (
                  <svg className="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                )}
              </button>
              <input ref={photoInputRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoChange} />
            </>
          )}
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">{researcher.nome}</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: color }}>
              {STATUS_LABELS[researcher.status] || researcher.status}
            </span>
            {researcher.email && <span className="text-xs text-gray-500">{researcher.email}</span>}
          </div>
          {isProfessor && (
            <p className="text-xs text-gray-400 mt-1">
              {researcherUser?.last_login
                ? formatLastLogin(researcherUser.last_login)
                : 'Nunca acessou'}
            </p>
          )}
        </div>
      </header>

      <main className="max-w-3xl mx-auto py-8 px-4 space-y-6">
        <ProfileSection researcher={researcher} canEdit={canEdit} isProfessor={isProfessor} onSaved={load} />
        {myDeadlines.length > 0 && (
          <section className="bg-white rounded-xl border shadow-sm p-5 space-y-3">
            <h2 className="text-sm font-semibold text-gray-700">Trabalhando em</h2>
            <div className="flex flex-wrap gap-2">
              {myDeadlines.map(d => (
                <a
                  key={d.label}
                  href={d.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors font-medium"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {d.label}
                </a>
              ))}
            </div>
          </section>
        )}
        <NotesSection researcherId={researcher.id} canAdd={isProfessor || isOwnProfile} isProfessor={isProfessor} currentUserId={payload?.sub != null ? Number(payload.sub) : null} />
      </main>
    </div>
  );
}
