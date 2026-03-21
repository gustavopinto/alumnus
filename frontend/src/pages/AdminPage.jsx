import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAdminStats, getAdminUsers, updateUserRole, deleteUser, deletePendingResearcher } from '../api';
import { getTokenPayload } from '../auth';

const ROLE_LABELS = { superadmin: 'Superadmin', admin: 'Admin', professor: 'Professor', student: 'Aluno' };
const ROLE_COLORS = {
  superadmin: 'bg-red-100 text-red-700 border-red-200',
  admin:      'bg-purple-100 text-purple-700 border-purple-200',
  professor:  'bg-blue-100 text-blue-700 border-blue-200',
  student:    'bg-green-100 text-green-700 border-green-200',
  pending:    'bg-gray-100 text-gray-500 border-gray-200',
};

function StatCard({ label, value, color = 'text-blue-600' }) {
  return (
    <div className="bg-white rounded-xl border shadow-sm p-5 flex flex-col gap-1">
      <span className={`text-3xl font-bold ${color}`}>{value ?? '—'}</span>
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  );
}

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [editingId, setEditingId] = useState(undefined);
  const [editRole, setEditRole] = useState('');
  const [saving, setSaving] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const isSuperadmin = getTokenPayload()?.role === 'superadmin';

  function copyInviteLink(u) {
    const token = btoa(u.email);
    const url = `${window.location.origin}/entrar?tab=cadastro&token=${token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedId(u.researcher_id ?? u.id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  }

  const ROLE_ORDER = { superadmin: 0, professor: 1, admin: 2, student: 3 };

  async function load() {
    const [s, u] = await Promise.all([getAdminStats(), getAdminUsers()]);
    setStats(s);
    const sorted = (u || []).sort((a, b) => {
      if (a.pending !== b.pending) return a.pending ? 1 : -1;
      const ra = ROLE_ORDER[a.role] ?? 99;
      const rb = ROLE_ORDER[b.role] ?? 99;
      if (ra !== rb) return ra - rb;
      return (a.nome || '').localeCompare(b.nome || '', 'pt-BR');
    });
    setUsers(sorted);
  }

  useEffect(() => { load(); }, []);

  async function handleRoleChange(userId) {
    setSaving(true);
    await updateUserRole(userId, editRole, ['admin','superadmin'].includes(editRole));
    setEditingId(null);
    setSaving(false);
    load();
  }

  async function handleDelete(u) {
    if (!confirm(`Remover "${u.nome}"? Esta ação não pode ser desfeita.`)) return;
    if (u.pending) {
      await deletePendingResearcher(u.researcher_id);
    } else {
      await deleteUser(u.id);
    }
    load();
  }

  function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  return (
    <div className="min-h-full bg-gray-50">
      <main className="max-w-5xl mx-auto py-8 px-4 space-y-8">

        {/* Stats */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Visão geral</h2>
          <div className={`grid grid-cols-2 gap-4 ${isSuperadmin ? 'sm:grid-cols-3' : 'sm:grid-cols-2'}`}>
            {isSuperadmin && (stats?.users_by_role?.admin ?? 0) > 0 ? (
              <StatCard label="Admins"       value={stats?.users_by_role?.admin      ?? 0} color="text-purple-600" />
            ) : null}
            <StatCard label="Professores"  value={stats?.users_by_role?.professor  ?? 0} color="text-blue-600" />
            <StatCard label="Alunos"       value={stats?.users_by_role?.student    ?? 0} color="text-green-600" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4">
            <StatCard label="Lembretes"    value={stats?.total_reminders}           color="text-amber-600" />
            <StatCard label="Manual"       value={stats?.total_manual_entries}      color="text-teal-600" />
            <StatCard label="Posts mural"  value={stats?.total_board_posts}         color="text-orange-600" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
            <StatCard label="Anotações"   value={stats?.total_notes}               color="text-rose-600" />
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
                  <th className="px-4 py-3">WhatsApp</th>
                  <th className="px-4 py-3">Último acesso</th>
                  <th className="px-4 py-3">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((u, idx) => (
                  <tr key={u.id ?? `pending-${idx}`} className={`hover:bg-gray-50 transition-colors ${u.pending ? 'opacity-60' : ''}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {u.photo_url
                          ? <img src={u.photo_url} alt="" className="w-7 h-7 rounded-full object-cover shrink-0" />
                          : <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-500 shrink-0">{(u.nome || '?')[0].toUpperCase()}</div>
                        }
                        <span className="font-medium text-gray-800">
                          {u.researcher_nome
                            ? <a href={`/app/profile/${slugify(u.nome)}`} className="hover:text-blue-600 hover:underline">{u.nome}</a>
                            : u.nome}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{u.email}</td>
                    <td className="px-4 py-3">
                      {u.pending ? (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${ROLE_COLORS.pending}`}>
                          Pendente
                        </span>
                      ) : editingId === u.id && isSuperadmin ? (
                        <div className="flex items-center gap-2 flex-wrap">
                          <select
                            value={editRole}
                            onChange={e => setEditRole(e.target.value)}
                            className="border rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-purple-400"
                          >
                            <option value="superadmin">Superadmin</option>
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
                            onClick={() => setEditingId(undefined)}
                            className="text-gray-500 hover:text-gray-700 text-xs px-1"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 flex-wrap">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${ROLE_COLORS[u.role] || 'bg-gray-100 text-gray-700 border-gray-200'}`}>
                            {ROLE_LABELS[u.role] || u.role}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {u.whatsapp
                        ? <a href={`https://wa.me/${u.whatsapp.replace(/\D/g, '')}`} target="_blank" rel="noreferrer" className="hover:text-green-600 hover:underline">{u.whatsapp}</a>
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-400">{formatDate(u.last_login)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        {u.pending && editingId !== u.id && (
                          <button
                            onClick={() => copyInviteLink(u)}
                            className="p-1.5 rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                            title="Copiar link de ativação"
                          >
                            {copiedId === (u.researcher_id ?? u.id) ? (
                              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            ) : (
                              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                              </svg>
                            )}
                          </button>
                        )}
                        {editingId !== u.id && isSuperadmin && (
                          <button
                            onClick={() => {
                              if (u.pending) {
                                navigate(`/app/profile/${slugify(u.nome)}`);
                              } else {
                                setEditingId(u.id); setEditRole(u.role);
                              }
                            }}
                            className="p-1.5 rounded text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                            title={u.pending ? 'Ver perfil' : 'Editar perfil'}
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                        )}
                        {editingId !== u.id && isSuperadmin && (
                          <button
                            onClick={() => handleDelete(u)}
                            className="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                            title="Remover"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
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
