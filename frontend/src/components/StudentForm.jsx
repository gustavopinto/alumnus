import React, { useState, useEffect } from 'react';
import { createResearcher, updateResearcher, uploadPhoto } from '../api';
import Toast from './Toast';

const EMPTY = { nome: '', status: 'graduacao', email: '', observacoes: '', photo_url: '', orientador_id: '', matricula: '', curso: '', enrollment_date: '' };

export default function ResearcherForm({ researcher, researchers, onSaved, onCancel }) {
  const [form, setForm] = useState(EMPTY);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState('');

  useEffect(() => {
    if (researcher) {
      setForm({
        nome: researcher.nome || '',
        status: researcher.status || 'graduacao',
        email: researcher.email || '',
        observacoes: researcher.observacoes || '',
        photo_url: researcher.photo_url || '',
        orientador_id: researcher.orientador_id || '',
        matricula: researcher.matricula || '',
        curso: researcher.curso || '',
        enrollment_date: researcher.enrollment_date || '',
      });
    } else {
      setForm(EMPTY);
    }
  }, [researcher]);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function handlePhoto(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const res = await uploadPhoto(file);
    setForm({ ...form, photo_url: res.url });
    setUploading(false);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const payload = {
      ...form,
      orientador_id: form.orientador_id ? Number(form.orientador_id) : null,
    };
    if (researcher) {
      await updateResearcher(researcher.id, payload);
      setToast('Pesquisador atualizado com sucesso');
    } else {
      await createResearcher(payload);
      setToast('Pesquisador criado com sucesso');
    }
    setTimeout(onSaved, 1200);
  }

  return (
    <>
    <Toast message={toast} onClose={() => setToast('')} />
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-bold text-lg">{researcher ? 'Editar Pesquisador' : 'Novo Pesquisador'}</h3>

      <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Nome *" required value={form.nome} onChange={set('nome')} />

      <select className="w-full border rounded px-3 py-2 text-sm" value={form.status} onChange={set('status')}>
        <option value="graduacao">Graduação</option>
        <option value="mestrado">Mestrado</option>
        <option value="doutorado">Doutorado</option>
        <option value="professor">Professor</option>
      </select>

      <input className="w-full border rounded px-3 py-2 text-sm" placeholder="E-mail" value={form.email} onChange={set('email')} />

      <select className="w-full border rounded px-3 py-2 text-sm" value={form.orientador_id} onChange={set('orientador_id')}>
        <option value="">Sem orientador</option>
        {researchers.filter((s) => !researcher || s.id !== researcher.id).map((s) => (
          <option key={s.id} value={s.id}>{s.nome}</option>
        ))}
      </select>

      <div className="flex gap-2">
        <input className="flex-1 border rounded px-3 py-2 text-sm" placeholder="Matrícula" value={form.matricula} onChange={set('matricula')} />
        <input className="flex-1 border rounded px-3 py-2 text-sm" placeholder="Curso" value={form.curso} onChange={set('curso')} />
      </div>

      <div>
        <label className="text-xs text-gray-500">
          Data de ingresso {(form.status === 'mestrado' || form.status === 'doutorado') ? '*' : ''}
        </label>
        <input
          type="date"
          className="w-full border rounded px-3 py-2 text-sm mt-1"
          value={form.enrollment_date}
          required={form.status === 'mestrado' || form.status === 'doutorado'}
          onChange={set('enrollment_date')}
        />
      </div>

      <textarea className="w-full border rounded px-3 py-2 text-sm" placeholder="Observações" rows={2} value={form.observacoes} onChange={set('observacoes')} />

      <div>
        <label className="text-sm text-gray-600">Foto</label>
        <input type="file" accept="image/*" onChange={handlePhoto} className="block text-sm mt-1" />
        {uploading && <span className="text-xs text-gray-500">Enviando...</span>}
        {form.photo_url && <img src={form.photo_url} alt="" className="w-12 h-12 rounded-full mt-1 object-cover" />}
      </div>

      <div className="flex gap-2">
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">
          {researcher ? 'Salvar' : 'Criar'}
        </button>
        <button type="button" onClick={onCancel} className="bg-gray-200 px-4 py-2 rounded text-sm hover:bg-gray-300">
          Cancelar
        </button>
      </div>
    </form>
    </>
  );
}
