import React, { useState } from 'react';
import StudentForm from './StudentForm';
import { deleteStudent } from '../api';

const DEADLINES = [
  { label: 'ICSE 2026', url: 'https://conf.researchr.org/home/icse-2026', date: '2026-01-24' },
  { label: 'FSE 2026', url: 'https://conf.researchr.org/home/fse-2026', date: '2026-02-06' },
  { label: 'ASE 2026', url: 'https://conf.researchr.org/home/ase-2026', date: '2026-04-10' },
  { label: 'MSR 2026', url: 'https://conf.researchr.org/home/msr-2026', date: '2026-02-13' },
  { label: 'ISSTA 2026', url: 'https://conf.researchr.org/home/issta-2026', date: '2026-02-07' },
];

function daysUntil(dateStr) {
  const diff = new Date(dateStr) - new Date();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

export default function Sidebar({ students, onRefresh, role }) {
  const [view, setView] = useState('list');
  const [editStudent, setEditStudent] = useState(null);

  function handleEdit(s) {
    setEditStudent(s);
    setView('student-form');
  }

  async function handleDelete(id) {
    if (!confirm('Inativar este aluno?')) return;
    await deleteStudent(id);
    onRefresh();
  }

  function handleSaved() {
    setView('list');
    setEditStudent(null);
    onRefresh();
  }

  if (view === 'student-form') {
    return (
      <div className="p-4">
        <StudentForm student={editStudent} students={students} onSaved={handleSaved}
          onCancel={() => { setView('list'); setEditStudent(null); }} />
      </div>
    );
  }

  const sorted = [...DEADLINES].sort((a, b) => new Date(a.date) - new Date(b.date));

  return (
    <div className="p-4 space-y-5 overflow-y-auto h-full">
      <div>
        <h3 className="font-bold text-sm text-gray-600 uppercase mb-2">Alunos ({students.length})</h3>
        <ul className="space-y-1">
          {students.map((s) => (
            <li key={s.id} className="flex items-center justify-between bg-white rounded px-2 py-1.5 text-sm shadow-sm">
              <span className="truncate">{s.nome}</span>
              {role === 'professor' && (
                <span className="flex gap-1 shrink-0">
                  <button onClick={() => handleEdit(s)} className="text-blue-600 hover:underline text-xs">editar</button>
                  <button onClick={() => handleDelete(s.id)} className="text-red-500 hover:underline text-xs">inativar</button>
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="font-bold text-sm text-gray-600 uppercase mb-2">Deadlines</h3>
        <ul className="space-y-1.5">
          {sorted.map((d) => {
            const days = daysUntil(d.date);
            const past = days < 0;
            return (
              <li key={d.label} className={`bg-white rounded px-2 py-1.5 shadow-sm ${past ? 'opacity-40' : ''}`}>
                <a href={d.url} target="_blank" rel="noreferrer"
                  className="text-sm font-medium text-blue-600 hover:underline block truncate">
                  {d.label}
                </a>
                <span className={`text-xs ${past ? 'text-gray-400' : days <= 14 ? 'text-red-500 font-semibold' : 'text-gray-400'}`}>
                  {past ? 'Encerrado' : days === 0 ? 'Hoje!' : `${days}d`}
                  {' · '}{new Date(d.date).toLocaleDateString('pt-BR')}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
