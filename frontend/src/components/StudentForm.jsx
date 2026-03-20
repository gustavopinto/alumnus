import React, { useState, useEffect } from 'react';
import { createStudent, updateStudent, uploadPhoto } from '../api';

const EMPTY = { nome: '', status: 'graduacao', email: '', observacoes: '', photo_url: '', orientador_id: '' };

export default function StudentForm({ student, students, onSaved, onCancel }) {
  const [form, setForm] = useState(EMPTY);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (student) {
      setForm({
        nome: student.nome || '',
        status: student.status || 'graduacao',
        email: student.email || '',
        observacoes: student.observacoes || '',
        photo_url: student.photo_url || '',
        orientador_id: student.orientador_id || '',
      });
    } else {
      setForm(EMPTY);
    }
  }, [student]);

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
    if (student) {
      await updateStudent(student.id, payload);
    } else {
      await createStudent(payload);
    }
    onSaved();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-bold text-lg">{student ? 'Editar Aluno' : 'Novo Aluno'}</h3>

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
        {students.filter((s) => !student || s.id !== student.id).map((s) => (
          <option key={s.id} value={s.id}>{s.nome}</option>
        ))}
      </select>

      <textarea className="w-full border rounded px-3 py-2 text-sm" placeholder="Observações" rows={2} value={form.observacoes} onChange={set('observacoes')} />

      <div>
        <label className="text-sm text-gray-600">Foto</label>
        <input type="file" accept="image/*" onChange={handlePhoto} className="block text-sm mt-1" />
        {uploading && <span className="text-xs text-gray-500">Enviando...</span>}
        {form.photo_url && <img src={form.photo_url} alt="" className="w-12 h-12 rounded-full mt-1 object-cover" />}
      </div>

      <div className="flex gap-2">
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">
          {student ? 'Salvar' : 'Criar'}
        </button>
        <button type="button" onClick={onCancel} className="bg-gray-200 px-4 py-2 rounded text-sm hover:bg-gray-300">
          Cancelar
        </button>
      </div>
    </form>
  );
}
