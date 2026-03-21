import React, { useState, useEffect } from 'react';
import { useAppLayout } from '../components/AppLayout';
import { getAdminStats, getAdminUsers, updateUserRole, deleteUser } from '../api';

const ROLE_LABELS = { admin: 'Admin', professor: 'Professor', student: 'Aluno' };
const ROLE_COLORS = {
  admin:     'bg-purple-100 text-purple-700 border-purple-200',
  professor: 'bg-blue-100 text-blue-700 border-blue-200',
  student:   'bg-green-100 text-green-700 border-green-200',
};

function StatCard({ label, value, color = 'text-blue-600' }) {
  return (
    <div className="bg-white rounded-xl border shadow-sm p-5 flex flex-col gap-1">
      <span className={`text-3xl font-bold ${color}`}>{value ?? '—'}</span>
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  );
}

export default function AdminPage() {
  const { sidebarOpen } = useAppLayout();
  const headerPad = sidebarOpen ? 'pl-14' : '';
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editRole, setEditRole] = useState('');
  const [saving, setSaving] = useState(false);

  async function load() {
    const [s, u] = await Promise.all([getAdminStats(), getAdminUsers()]);
    setStats(s);
    setUsers(u || []);
  }

  useEffect(() => { load(); }, []);

  async function handleRoleChange(userId) {
    setSaving(true);
    await updateUserRole(userId, editRole);
    setEditingId(null);
    setSaving(false);
    load();
  }

  async function handleDelete(userId, nome) {
    if (!confirm(`Remover o usuário "${nome}"? Esta ação não pode ser desfeita.`)) return;
    await deleteUser(userId);
    load();
  }

  function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  return (
    <div className="min-h-full bg-gray-50">
      <header className={`bg-white border-b shadow-sm px-6 py-4 flex items-center gap-4 ${headerPad}`}>
        <div className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h1 className="text-xl font-bold text-gray-900">Dashboard Admin</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto py-8 px-4 space-y-8">

        {/* Stats */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Visão geral</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <StatCard label="Admins"       value={stats?.users_by_role?.admin     ?? 0} color="text-purple-600" />
            <StatCard label="Professores"  value={stats?.users_by_role?.professor  ?? 0} color="text-blue-600" />
            <StatCard label="Alunos"       value={stats?.users_by_role?.student    ?? 0} color="text-green-600" />
            <StatCard label="Pesquisadores" value={stats?.total_researchers}         color="text-indigo-600" />
            <StatCard label="Lembretes"    value={stats?.total_reminders}           color="text-amber-600" />
            <StatCard label="Manual"       value={stats?.total_manual_entries}      color="text-teal-600" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4">
            <StatCard label="Anotações"   value={stats?.total_notes}               color="text-rose-600" />
            <StatCard label="Posts mural" value={stats?.total_board_posts}         color="text-orange-600" />
          </div>
        </section>

        {/* Users */}
        <section className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="text-base font-semibold text-gray-800">Usuários</h2>
            <p className="text-sm text-gray-500 mt-0.5">{users.length} usuário{users.length !== 1 ? 's' : ''} cadastrado{users.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Perfil</th>
                  <th className="px-4 py-3">Pesquisador</th>
                  <th className="px-4 py-3">Último acesso</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-800">{u.nome}</td>
                    <td className="px-4 py-3 text-gray-500">{u.email}</td>
                    <td className="px-4 py-3">
                      {editingId === u.id ? (
                        <div className="flex items-center gap-2">
                          <select
                            value={editRole}
                            onChange={e => setEditRole(e.target.value)}
                            className="border rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-purple-400"
                          >
                            <option value="admin">Admin</option>
                            <option value="professor">Professor</option>
                            <option value="student">Aluno</option>
                          </select>
                          <button
                            onClick={() => handleRoleChange(u.id)}
                            disabled={saving}
                            className="bg-purple-600 text-white px-2 py-1 rounded text-xs hover:bg-purple-700 disabled:opacity-50"
                          >
                            Salvar
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="text-gray-500 hover:text-gray-700 text-xs px-1"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${ROLE_COLORS[u.role] || 'bg-gray-100 text-gray-700 border-gray-200'}`}>
                          {ROLE_LABELS[u.role] || u.role}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{u.researcher_nome || '—'}</td>
                    <td className="px-4 py-3 text-gray-400">{formatDate(u.last_login)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        {editingId !== u.id && (
                          <button
                            onClick={() => { setEditingId(u.id); setEditRole(u.role); }}
                            className="p-1.5 rounded text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                            title="Editar perfil"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(u.id, u.nome)}
                          className="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          title="Remover usuário"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400 italic">Nenhum usuário encontrado.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
