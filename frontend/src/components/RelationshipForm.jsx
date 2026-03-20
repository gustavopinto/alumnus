import React, { useState } from 'react';
import { createRelationship } from '../api';

const TYPES = [
  { value: 'orienta', label: 'Orienta' },
  { value: 'coautor', label: 'Coautor' },
  { value: 'mesmo_projeto', label: 'Mesmo Projeto' },
  { value: 'mesmo_laboratorio', label: 'Mesmo Laboratório' },
];

export default function RelationshipForm({ students, onSaved, onCancel }) {
  const [form, setForm] = useState({ source_student_id: '', target_student_id: '', relation_type: 'orienta' });

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    await createRelationship({
      source_student_id: Number(form.source_student_id),
      target_student_id: Number(form.target_student_id),
      relation_type: form.relation_type,
    });
    onSaved();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-bold text-lg">Nova Relação</h3>

      <select className="w-full border rounded px-3 py-2 text-sm" required value={form.source_student_id} onChange={set('source_student_id')}>
        <option value="">Aluno origem...</option>
        {students.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
      </select>

      <select className="w-full border rounded px-3 py-2 text-sm" required value={form.target_student_id} onChange={set('target_student_id')}>
        <option value="">Aluno destino...</option>
        {students.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
      </select>

      <select className="w-full border rounded px-3 py-2 text-sm" value={form.relation_type} onChange={set('relation_type')}>
        {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
      </select>

      <div className="flex gap-2">
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">Criar</button>
        <button type="button" onClick={onCancel} className="bg-gray-200 px-4 py-2 rounded text-sm hover:bg-gray-300">Cancelar</button>
      </div>
    </form>
  );
}
