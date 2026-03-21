import React, { useState, useEffect } from 'react';
import { updateResearcher } from '../api';
import { modKey, isModEnter } from '../platform';

export default function NotesModal({ student, onClose }) {
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setText(student?.observacoes || '');
  }, [student]);

  if (!student) return null;

  async function handleSave() {
    setSaving(true);
    await updateResearcher(student.id, { observacoes: text });
    setSaving(false);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg text-gray-800">Anotações — {student.fullName}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <textarea
          className="w-full border rounded-lg px-3 py-2 text-sm h-48 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Trabalhos, publicações, observações..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={e => isModEnter(e) && handleSave()}
          autoFocus
        />
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg bg-gray-100 hover:bg-gray-200">Cancelar</button>
          <button onClick={handleSave} disabled={saving} className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Salvando...' : <><span>Salvar</span> <span className="opacity-50 text-xs">{modKey}+Enter</span></>}
          </button>
        </div>
      </div>
    </div>
  );
}
